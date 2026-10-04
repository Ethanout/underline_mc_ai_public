"""Editable technical records retain raw provenance and conflicting claims."""
from __future__ import annotations

import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

from .store import dumps


class TrickStore:
    def __init__(self, store, root="runtime/private/qq_tricks", classifier=None):
        self.store, self.root, self.classifier = store, Path(root), classifier

    def add(self, group_id, item, source_id, author="未知"):
        group_id = str(group_id)
        if not re.fullmatch(r"[\w-]+", group_id):
            raise ValueError("群号路径无效")
        title = str(item.get("title") or "未知")
        identity = str(item.get("identity") or title)
        key = hashlib.sha256(f"{group_id}:{identity}".encode()).hexdigest()[:24]
        path = self.root / group_id / f"{key}.md"
        record = self.store.get_state("trick:" + key, {"title": title, "sources": [], "claims": [], "history": []})
        normalized = {field: str(item.get(field) or "未知") for field in
                      ("purpose", "version", "code", "limits", "conclusion")}
        normalized["author"] = str(author or "未知")
        normalized["source"] = str(source_id)
        if normalized not in record["claims"]:
            record["claims"].append(normalized)
            record["history"].append({"at": self.store.clock(), "source": str(source_id), "action": "补充来源和结论"})
        if str(source_id) not in record["sources"]:
            record["sources"].append(str(source_id))
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            previous = path.read_text(encoding="utf-8")
            self.store.set_state(f"trick_revision:{key}:{hashlib.sha256(previous.encode()).hexdigest()}", previous)
        text = self._markdown(record)
        path.write_text(text, encoding="utf-8")
        self.store.set_state("trick:" + key, record)
        mid = "trick:" + key
        self.store.write("INSERT OR REPLACE INTO memory_state VALUES(?,?,?,?,?,?,?,?,?)", (mid, group_id,
            "related", "trick", str(author), text, dumps(record["sources"]), dumps({"path": str(path), "hash": hashlib.sha256(text.encode()).hexdigest()}), self.store.clock()))
        return {"stored": True, "id": mid, "path": str(path), "sources": record["sources"]}

    @staticmethod
    def _markdown(record):
        lines = [f"# {record['title']}", "", "状态：AI 整理、未验证", "",
                 "来源消息：" + "、".join(record["sources"]), ""]
        for index, claim in enumerate(record["claims"], 1):
            lines.extend([f"## 结论 {index}（来源：{claim['source']}）", "",
                f"作者：{claim['author']}", f"用途：{claim['purpose']}", f"适用版本：{claim['version']}",
                f"限制：{claim['limits']}", f"结论：{claim['conclusion']}", "", "```mcfunction", claim["code"], "```", ""])
        lines.extend(["## 修改历史", ""])
        lines.extend(f"- {entry['at']}：{entry['action']}（{entry['source']}）" for entry in record["history"])
        return "\n".join(lines) + "\n"

    def sync(self, group_id, messages):
        if self.classifier is None:
            raise RuntimeError("技术资料分类器未配置")
        results = []
        for message in messages:
            mid = str(message.get("message_id") or hashlib.sha256(dumps(message).encode()).hexdigest())
            source = f"{group_id}:{mid}"
            if self.store.rows("SELECT id FROM essence_processed WHERE id=?", (source,)):
                continue
            item = self.classifier(message)
            if item:
                sender = message.get("sender") or {}
                author = sender.get("nickname") or message.get("sender_nick") or message.get("sender_id") or "未知"
                results.append(self.add(group_id, item, source, author))
            self.store.write("INSERT OR IGNORE INTO essence_processed VALUES(?)", (source,))
        return results

    def reindex(self):
        changed = []
        for row in self.store.rows("SELECT * FROM memory_state WHERE kind='trick'"):
            state = json.loads(row["state"])
            path = Path(state["path"])
            if not path.is_file(): continue
            text = path.read_text(encoding="utf-8")
            digest = hashlib.sha256(text.encode()).hexdigest()
            if digest != state["hash"]:
                self.store.set_state(f"trick_revision:{row['id']}:{state['hash']}", row["content"])
                state["hash"] = digest
                self.store.write("UPDATE memory_state SET content=?,state=?,updated=? WHERE id=?",
                    (text, dumps(state), self.store.clock(), row["id"]))
                changed.append(row["id"])
        return changed


def safe_extract_archive(archive, target, max_bytes=50_000_000, max_files=1000):
    target = Path(target).resolve()
    with zipfile.ZipFile(archive) as zipped:
        members = zipped.infolist()
        if len(members) > max_files:
            raise ValueError("压缩包文件数超过限制")
        total = 0
        for member in members:
            name = member.filename.replace("\\", "/")
            parts = PurePosixPath(name).parts
            if not parts or name.startswith("/") or ".." in parts or ":" in name or stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError("压缩包包含不允许的路径")
            destination = (target / name).resolve()
            if not destination.is_relative_to(target):
                raise ValueError("压缩包包含路径穿越")
            total += member.file_size
            if total > max_bytes:
                raise ValueError("压缩包总大小超过限制")
        target.mkdir(parents=True, exist_ok=True)
        for member in members:
            name = member.filename.replace("\\", "/")
            destination = target / name
            if member.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with zipped.open(member) as source, destination.open("wb") as output:
                remaining = member.file_size
                while remaining:
                    chunk = source.read(min(65536, remaining))
                    if not chunk: break
                    output.write(chunk)
                    remaining -= len(chunk)
    return [str(target / member.filename) for member in members]


def read_code_attachment(path, max_bytes=1_000_000):
    with Path(path).open("rb") as source:
        raw = source.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError("代码附件超过大小限制")
    return raw.decode("utf-8-sig")


def video_source(segment):
    return {"type": "video", "source": segment.get("data", {}).get("url") or segment.get("data", {}).get("file"),
            "status": "只保存来源"}
