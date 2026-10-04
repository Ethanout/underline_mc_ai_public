"""Low-cost OneBot event observation for the QQ agent."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any


class EventJournal:
    """Append deduplicated group messages without invoking an LLM."""

    def __init__(self, path: Path, max_bytes: int = 50_000_000, store=None) -> None:
        self.path = path
        self.max_bytes = max_bytes
        self._seen: set[str] = set()
        self._lock = threading.Lock()
        self.store = store

    @staticmethod
    def event_key(event: dict[str, Any]) -> str:
        for key in ("message_id", "message_seq"):
            if event.get(key) is not None:
                return str(event[key])
        raw = json.dumps(event, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def append(self, event: dict[str, Any]) -> bool:
        if event.get("post_type") != "message" or event.get("message_type") != "group":
            return False
        key = self.event_key(event)
        stable_key = f"{event.get('group_id', '')}:{key}"
        with self._lock:
            if stable_key in self._seen:
                return False
            if self.store is not None and self.store.message(str(event.get("group_id", "")), key):
                return False
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists() and self.path.stat().st_size >= self.max_bytes:
                raise RuntimeError("群消息观察日志已达到大小上限")
            row = {"received_at": time.time(), "event_key": key, "event": event}
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            if self.store is not None:
                self.store.append(event, row["received_at"])
            self._seen.add(stable_key)
            return True

    def append_bot_message(
        self,
        group_id: str,
        text: str,
        message_id: str | None = None,
        reply_to: str | None = None,
    ) -> bool:
        """Record a reply sent by this bot when OneBot does not echo self messages.

        ``reply_to`` is the id of the message that triggered this reply.  It is
        stored as a normal ``reply`` segment so a stored bot line carries the
        same shape as one the adapter would have echoed, and so the style memory
        can resolve what it was answering -- a bare reply with no trigger reads
        very differently out of context.
        """
        segments: list[dict[str, Any]] = []
        if reply_to is not None:
            segments.append({"type": "reply", "data": {"id": str(reply_to)}})
        segments.append({"type": "text", "data": {"text": text}})
        event = {
            "post_type": "message",
            "message_type": "group",
            "group_id": str(group_id),
            "user_id": "self",
            "message_id": message_id,
            "time": time.time(),
            "sender": {"user_id": "self", "nickname": "毯毯", "role": "bot"},
            "message": segments,
        }
        return self.append(event)

    def recent_context(self, group_id: str, max_chars: int = 3000, limit: int = 30) -> str:
        """Return recent same-group messages, bounded from the newest backward."""
        if not self.path.exists():
            return ""
        if max_chars <= 0 or limit <= 0:
            return ""
        rows: list[tuple[float, str]] = []
        with self._lock:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        for line in lines:
            try:
                record = json.loads(line)
                event = record.get("event", {})
            except json.JSONDecodeError:
                continue
            if str(event.get("group_id", "")) != str(group_id):
                continue
            sender = event.get("sender") if isinstance(event.get("sender"), dict) else {}
            text = "".join(
                str(segment.get("data", {}).get("text", ""))
                for segment in event.get("message", [])
                if isinstance(segment, dict) and segment.get("type") == "text"
            ).strip()
            if text:
                user_id = str(event.get("user_id", ""))
                is_bot = user_id == "self" or (
                    event.get("self_id") is not None and user_id == str(event["self_id"])
                )
                name = (
                    "毯毯"
                    if is_bot
                    else (sender.get("nickname") or sender.get("card") or user_id or "群友")
                )
                name = " ".join(str(name).splitlines())
                timestamp = event.get("time") or record.get("received_at", 0)
                rows.append((float(timestamp), f"{name}：{text}"))
        rows.sort(key=lambda item: item[0])
        result: list[str] = []
        size = 0
        for _, row in reversed(rows[-limit:]):
            if size + len(row) + 1 > max_chars:
                break
            result.append(row)
            size += len(row) + 1
        return "\n".join(reversed(result))
