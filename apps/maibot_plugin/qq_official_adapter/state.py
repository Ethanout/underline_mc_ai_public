"""Durable event dedupe, gateway resume cursor, and reply sequence reservation."""

from __future__ import annotations

import copy
import json
import sqlite3
import threading
from pathlib import Path


class OfficialState:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, ts REAL);
            CREATE TABLE IF NOT EXISTS replies (id TEXT PRIMARY KEY, seq INTEGER);
            CREATE TABLE IF NOT EXISTS messages (id TEXT PRIMARY KEY, target TEXT, private INTEGER, ts REAL, payload TEXT);
            CREATE TABLE IF NOT EXISTS quote_indexes (id TEXT PRIMARY KEY, ref_idx TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS quote_indexes_ref ON quote_indexes(ref_idx);
            CREATE INDEX IF NOT EXISTS messages_target ON messages(target, private, ts);
            CREATE INDEX IF NOT EXISTS events_time ON events(ts);
        """)

    def get(self, key, default=None):
        with self.lock:
            row = self.db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def put(self, key, value):
        with self.lock, self.db:
            self.db.execute("INSERT OR REPLACE INTO state VALUES (?, ?)", (key, json.dumps(value)))

    def seen(self, event_id):
        with self.lock:
            return bool(self.db.execute("SELECT 1 FROM events WHERE id=?", (event_id,)).fetchone())

    def mark(self, event_id, now):
        with self.lock, self.db:
            self.db.execute("INSERT OR IGNORE INTO events VALUES (?, ?)", (event_id, now))
            self.db.execute("DELETE FROM events WHERE ts<?", (now - 7 * 86400,))
            self.db.execute("DELETE FROM replies WHERE id IN (SELECT id FROM messages WHERE ts<?)", (now - 7 * 86400,))
            self.db.execute("DELETE FROM messages WHERE ts<?", (now - 7 * 86400,))
            self.db.execute("DELETE FROM quote_indexes WHERE id NOT IN (SELECT id FROM messages)")

    def next_reply(self, message_id, limit):
        return self.reserve_replies(message_id, limit, 1)[0]

    def reserve_replies(self, message_id, limit, count):
        # Reserve before the HTTP request; an ambiguous network failure must not reuse a sequence.
        with self.lock, self.db:
            row = self.db.execute("SELECT seq FROM replies WHERE id=?", (message_id,)).fetchone()
            previous = row[0] if row else 0
            sequence = previous + count
            if count < 1 or sequence > limit:
                raise ValueError("该消息已达到官方被动回复次数上限")
            self.db.execute("INSERT OR REPLACE INTO replies VALUES (?, ?)", (message_id, sequence))
        return list(range(previous + 1, sequence + 1))

    def remember(self, message_id, target, private, timestamp, incoming=True, ref_idx=""):
        with self.lock, self.db:
            self.db.execute("INSERT OR IGNORE INTO messages VALUES (?, ?, ?, ?, ?)",
                            (message_id, target, int(private), timestamp, "incoming" if incoming else "outgoing"))
            if ref_idx:
                self.db.execute("INSERT OR REPLACE INTO quote_indexes VALUES (?, ?)", (message_id, ref_idx))

    def reply_target(self, target, private, message_id=""):
        with self.lock:
            if message_id:
                row = self.db.execute("SELECT id, ts, payload FROM messages WHERE target=? AND private=? AND id=?",
                                      (target, int(private), message_id)).fetchone()
            else:
                row = self.db.execute("SELECT id, ts, payload FROM messages WHERE target=? AND private=? AND payload='incoming' ORDER BY ts DESC LIMIT 1",
                                      (target, int(private))).fetchone()
            quote = self.db.execute("SELECT ref_idx FROM quote_indexes WHERE id=?", (row[0],)).fetchone() if row else None
        return {"id": row[0], "ts": row[1], "incoming": row[2] == "incoming",
                "ref_idx": quote[0] if quote else ""} if row else None

    def resolve_event_references(self, event_type, data):
        """Resolve opaque quote indexes only against unique messages in this conversation."""
        result = copy.deepcopy(data)
        private = event_type == "C2C_MESSAGE_CREATE"
        author = data.get("author") or {}
        target = str(author.get("user_openid") or author.get("id") or "") if private else str(data.get("group_openid") or "")
        if not target:
            return result

        def resolve(index):
            if not isinstance(index, str) or not index:
                return ""
            with self.lock:
                rows = self.db.execute(
                    "SELECT m.id FROM messages m JOIN quote_indexes q ON m.id=q.id "
                    "WHERE m.target=? AND m.private=? AND q.ref_idx=? LIMIT 2",
                    (target, int(private), index),
                ).fetchall()
            return rows[0][0] if len(rows) == 1 else ""

        scene = result.get("message_scene") or {}
        ref_index = next((item.partition("=")[2] for item in scene.get("ext", [])
                          if isinstance(item, str) and item.startswith("ref_msg_idx=")), "")
        target_id = resolve(ref_index)
        if target_id and not result.get("message_reference") and not result.get("reference"):
            result["message_reference"] = {"message_id": target_id}

        remaining = 60

        def resolve_elements(elements, depth=0):
            nonlocal remaining
            if depth >= 8:
                return
            for element in elements[:60]:
                if remaining <= 0:
                    return
                if not isinstance(element, dict):
                    continue
                remaining -= 1
                # msg_idx identifies a quoted message, never a new delivery ID.
                if element.get("message_type") == 103 and not element.get("message_id") and not element.get("id"):
                    matched = resolve(element.get("msg_idx"))
                    if matched:
                        element["message_id"] = matched
                resolve_elements(element.get("msg_elements") or [], depth + 1)

        resolve_elements(result.get("msg_elements") or [])
        return result

    def close(self):
        with self.lock:
            self.db.close()
