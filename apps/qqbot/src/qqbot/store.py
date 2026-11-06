"""Persist source identity and task boundaries independently of model text."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class Store:
    def __init__(self, path=None, clock=time.time):
        self.path = str(path or os.environ.get("QQBOT_DB", "runtime/private/qqbot.db"))
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY, group_id TEXT, message_id TEXT, user_id TEXT,
                nickname TEXT, card TEXT, ts REAL, quote_id TEXT, segments TEXT,
                is_bot INTEGER, raw TEXT, image_summary TEXT);
            CREATE INDEX IF NOT EXISTS messages_group ON messages(group_id, ts);
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, group_id TEXT, user_id TEXT, nickname TEXT,
                trigger_id TEXT, status TEXT, result TEXT, updated REAL);
            CREATE TABLE IF NOT EXISTS audit (
                id INTEGER PRIMARY KEY, task_id TEXT, user_id TEXT, ts REAL,
                tool TEXT, args TEXT, result TEXT, denied INTEGER);
            CREATE TABLE IF NOT EXISTS memory_state (
                id TEXT PRIMARY KEY, group_id TEXT, category TEXT, kind TEXT,
                author TEXT, content TEXT, sources TEXT, state TEXT, updated REAL);
            CREATE TABLE IF NOT EXISTS runtime_overrides (
                name TEXT PRIMARY KEY, value REAL, reason TEXT, updated REAL);
            CREATE TABLE IF NOT EXISTS recycle_bin (
                id TEXT PRIMARY KEY, payload TEXT, deleted REAL);
            CREATE TABLE IF NOT EXISTS state (
                key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS tool_runs (
                id TEXT PRIMARY KEY, status TEXT, result TEXT);
            CREATE TABLE IF NOT EXISTS essence_processed (
                id TEXT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS image_files (
                sha256 TEXT PRIMARY KEY, file_id TEXT, expires_at REAL, path TEXT);
            CREATE TABLE IF NOT EXISTS memory_changes (
                id INTEGER PRIMARY KEY, memory_id TEXT, ts REAL, action TEXT, details TEXT);
            CREATE TABLE IF NOT EXISTS research_sources (
                id TEXT PRIMARY KEY, group_id TEXT, requested_url TEXT, url TEXT,
                title TEXT, content TEXT, fetched_at REAL, task_id TEXT, truncated INTEGER);
            CREATE INDEX IF NOT EXISTS research_sources_group ON research_sources(group_id, requested_url);
            CREATE TABLE IF NOT EXISTS research_knowledge (
                id TEXT PRIMARY KEY, group_id TEXT, title TEXT, content TEXT, tags TEXT,
                source_ids TEXT, version TEXT, verification TEXT, task_id TEXT, created REAL, updated REAL);
            CREATE INDEX IF NOT EXISTS research_knowledge_group ON research_knowledge(group_id, updated);
        """)
        self.db.commit()
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(messages)")}
        if "image_summary" not in columns:
            self.db.execute("ALTER TABLE messages ADD COLUMN image_summary TEXT DEFAULT ''")
            self.db.commit()

    def close(self):
        self.db.close()

    def rows(self, sql, params=()):
        with self.lock:
            return [dict(row) for row in self.db.execute(sql, params).fetchall()]

    def write(self, sql, params=()):
        with self.lock, self.db:
            return self.db.execute(sql, params).rowcount

    def append(self, event, received_at=None):
        if event.get("post_type") != "message" or event.get("message_type") != "group":
            return False
        group = str(event.get("group_id", ""))
        mid = str(
            event.get("message_id")
            if event.get("message_id") is not None
            else event.get("message_seq") or hashlib.sha256(dumps(event).encode()).hexdigest()
        )
        segments = event.get("message", [])
        if isinstance(segments, str):
            segments = [{"type": "text", "data": {"text": segments}}]
        sender = event.get("sender") or {}
        uid = str(event.get("user_id", sender.get("user_id", "")))
        quote = next(
            (
                str(s.get("data", {}).get("id", ""))
                for s in segments
                if isinstance(s, dict) and s.get("type") == "reply"
            ),
            "",
        )
        bot = uid == "self" or (event.get("self_id") is not None and uid == str(event["self_id"]))
        summaries = " | ".join(
            str(s.get("data", {}).get("summary", ""))
            for s in segments
            if isinstance(s, dict) and s.get("type") == "image"
        )
        return bool(
            self.write(
                "INSERT OR IGNORE INTO messages VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    f"{group}:{mid}",
                    group,
                    mid,
                    uid,
                    sender.get("nickname", ""),
                    sender.get("card", ""),
                    float(event.get("time") or received_at or self.clock()),
                    quote,
                    dumps(segments),
                    int(bot),
                    dumps(event),
                    summaries,
                ),
            )
        )

    def messages(self, group_id):
        return self.rows(
            "SELECT * FROM messages WHERE group_id=? ORDER BY ts,rowid", (str(group_id),)
        )

    def message(self, group_id, message_id):
        mid = str(message_id)
        stable = mid if mid.startswith(f"{group_id}:") else f"{group_id}:{mid}"
        rows = self.rows(
            "SELECT * FROM messages WHERE id=? AND group_id=?", (stable, str(group_id))
        )
        return rows[0] if rows else None

    @staticmethod
    def text(row):
        pieces = []
        for segment in json.loads(row["segments"]):
            data = segment.get("data", {})
            if segment.get("type") == "text":
                pieces.append(str(data.get("text", "")))
            elif segment.get("type") == "image":
                pieces.append(
                    f"[图片:{data.get('summary') or row.get('image_summary') or '未缓存'}]"
                )
            elif segment.get("type") == "at":
                raw = json.loads(row.get("raw", "{}"))
                target = str(data.get("qq", ""))
                pieces.append("@毯毯" if target == str(raw.get("self_id")) else "@" + target)
        return "".join(pieces)

    def transcript(self, group_id, limit=30, max_chars=3000, trigger_id=None):
        rows = self.messages(group_id)
        lines = []
        for row in rows:
            name = "毯毯" if row["is_bot"] else row["nickname"] or row["card"] or row["user_id"]
            name = " ".join(name.splitlines())
            quote = ""
            if row["quote_id"]:
                target = self.message(group_id, row["quote_id"])
                quote = (
                    f" 引用#{row['quote_id']}「{self.text(target)[:20] if target else '原文缺失'}」"
                )
            mark = ">> " if str(trigger_id) in (row["id"], row["message_id"]) else ""
            lines.append(
                f"{mark}{datetime.fromtimestamp(row['ts']).strftime('%H:%M:%S')} #{row['message_id']} {name}：{self.text(row)}{quote}".replace(
                    "\n", " "
                )
            )
        selected = lines[-max(0, limit) :] if limit > 0 else []
        while selected:
            omitted = len(lines) - len(selected)
            prefix = f"更早的 {omitted} 条未显示\n" if omitted else ""
            if len(prefix + "\n".join(selected)) <= max_chars:
                return prefix + "\n".join(selected)
            selected.pop(0)
        return (f"更早的 {len(lines)} 条未显示"[:max_chars]) if lines and max_chars > 0 else ""

    def create_task(self, group_id, user_id, trigger_id, nickname=""):
        task_id = f"{group_id}:{trigger_id}"
        self.write(
            "INSERT OR IGNORE INTO tasks VALUES (?,?,?,?,?,?,?,?)",
            (
                task_id,
                str(group_id),
                str(user_id),
                nickname,
                str(trigger_id),
                "queued",
                "",
                self.clock(),
            ),
        )
        return self.task(task_id)

    def task(self, task_id):
        rows = self.rows("SELECT * FROM tasks WHERE id=?", (task_id,))
        return rows[0] if rows else None

    def update_task(self, task_id, status, result=""):
        self.write(
            "UPDATE tasks SET status=?,result=?,updated=? WHERE id=?",
            (status, result, self.clock(), task_id),
        )

    def audit(self, task, tool, args, result, denied=False):
        self.write(
            "INSERT INTO audit(task_id,user_id,ts,tool,args,result,denied) VALUES(?,?,?,?,?,?,?)",
            (
                task["id"],
                task["user_id"],
                self.clock(),
                tool,
                dumps(args),
                dumps(result),
                int(denied),
            ),
        )

    def get_state(self, key, default=None):
        rows = self.rows("SELECT value FROM state WHERE key=?", (key,))
        return json.loads(rows[0]["value"]) if rows else default

    def set_state(self, key, value):
        self.write("INSERT OR REPLACE INTO state VALUES (?,?)", (key, dumps(value)))

    def restore(self, memory_id):
        with self.lock, self.db:
            row = self.db.execute(
                "SELECT payload FROM recycle_bin WHERE id=?", (memory_id,)
            ).fetchone()
            if row is None:
                raise ValueError("回收站中没有该记忆")
            item = json.loads(row[0])
            self.db.execute(
                "INSERT OR REPLACE INTO memory_state VALUES(?,?,?,?,?,?,?,?,?)",
                tuple(
                    item[k]
                    for k in (
                        "id",
                        "group_id",
                        "category",
                        "kind",
                        "author",
                        "content",
                        "sources",
                        "state",
                        "updated",
                    )
                ),
            )
            self.db.execute("DELETE FROM recycle_bin WHERE id=?", (memory_id,))
        self.memory_change(memory_id, "restore", {"category": item["category"]})
        return item

    def recycle(self, item):
        with self.lock, self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO recycle_bin VALUES(?,?,?)",
                (item["id"], dumps(item), self.clock()),
            )
            self.db.execute("DELETE FROM memory_state WHERE id=?", (item["id"],))
        self.memory_change(item["id"], "recycle", {"category": item["category"]})

    def memory_change(self, memory_id, action, details):
        self.write(
            "INSERT INTO memory_changes(memory_id,ts,action,details) VALUES(?,?,?,?)",
            (memory_id, self.clock(), action, dumps(details)),
        )

    def import_journal(self, path):
        count = 0
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                count += self.append(row.get("event", {}), row.get("received_at"))
            except (ValueError, TypeError):
                continue
        return count


def main():
    parser = argparse.ArgumentParser(description="把旧群聊日志导入 SQLite")
    parser.add_argument("journal")
    parser.add_argument("--db", default=os.environ.get("QQBOT_DB", "runtime/private/qqbot.db"))
    args = parser.parse_args()
    store = Store(args.db)
    try:
        print(f"新增 {store.import_journal(args.journal)} 条消息")
    finally:
        store.close()


if __name__ == "__main__":
    main()
