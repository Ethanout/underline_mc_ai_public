"""Dated work artifacts. SQLite audit remains the source of work history."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .admin_tools import redact
from .store import dumps

SHANGHAI = timezone(timedelta(hours=8))


def work_date(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, SHANGHAI).strftime("%Y-%m-%d")


def atomic_write_text(path: Path, text: str) -> None:
    """Publish a complete UTF-8 artifact; a failed write keeps the previous file."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".pending-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class Workspaces:
    def __init__(self, root=None):
        self.root = Path(root or os.environ.get("QQBOT_WORKSPACES_DIR", "runtime/private/agent_workspaces"))

    def directory(self, timestamp: float, group_id: str) -> Path:
        group_id = str(group_id)
        official = re.fullmatch(r"official:([0-9]{1,32}):([A-Za-z0-9_-]{1,128})", group_id)
        if official:
            parts = ("official", official[1], official[2])
        elif re.fullmatch(r"[A-Za-z0-9_-]{1,64}", group_id):
            parts = (group_id,)
        else:
            raise ValueError("工作区群标识格式错误")
        path = self.root.joinpath(work_date(timestamp), *parts)
        if not path.resolve().is_relative_to(self.root.resolve()):
            raise ValueError("工作区目录指向根目录以外，未写入")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def record(self, task: dict, tool: str, args: dict, result: dict, timestamp: float) -> str:
        record = {"task_id": task["id"], "group_id": task["group_id"], "tool": tool,
                  "args": args, "result": result, "at": timestamp}
        body = redact(dumps(record))
        name = hashlib.sha256(body.encode()).hexdigest()[:24] + ".json"
        path = self.directory(timestamp, task["group_id"]) / name
        atomic_write_text(path, body)
        return str(path)
