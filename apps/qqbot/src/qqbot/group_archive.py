"""Persistent, resumable exports of scoped QQ files and essence messages."""
from __future__ import annotations

import hashlib
import json
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from .essence_exporter import extract_media, find_list, has_message_content, message_id
from .group_files import EXPORT_LOCK, checked_directory

WORKERS = ThreadPoolExecutor(max_workers=1, thread_name_prefix="group-archive")
LOCK = threading.Lock()
ACTIVE = set()


class GroupArchive:
    def __init__(self, files):
        self.files = files

    def directory(self, group):
        if not str(group).isdigit():
            raise ValueError("群号须为数字")
        return checked_directory(self.files.root, "qq_archives", str(group))

    def save(self, group, state):
        directory = self.directory(group)
        temporary = directory / "progress.tmp"
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(directory / "progress.json")

    def status(self, task, args):
        path = self.directory(task["group_id"]) / "progress.json"
        if not path.exists():
            return {"status": "not_started"}
        state = json.loads(path.read_text(encoding="utf-8"))
        return {key: value for key, value in state.items() if key != "results"}

    def start(self, task, args):
        group = str(task["group_id"])
        kind = args.get("kind", "all")
        if kind not in ("all", "files", "essence"):
            raise ValueError("kind 须为 all、files 或 essence")
        with LOCK:
            if group in ACTIVE:
                return {**self.status(task, {}), "already_running": True}
            ACTIVE.add(group)
        WORKERS.submit(self.run, group, kind)
        return {"group_id": group, "status": "queued", "kind": kind,
                "path": str(self.directory(group)), "message": "后台归档已启动；用 group_archive_status 查询，完成前不能声称全部保存。"}

    def run(self, group, kind="all"):
        state = {"group_id": group, "kind": kind, "status": "running", "started": time.time(),
                 "total": 0, "completed": 0, "failed": 0, "bytes": 0, "results": []}
        self.save(group, state)
        try:
            if kind in ("all", "files"):
                self.export_files(group, state)
            if kind in ("all", "essence"):
                self.export_essence(group, state)
            state["status"] = "partial" if state["failed"] else "completed"
        except Exception as exc:
            state.update(status="failed", error=str(exc))
        finally:
            state["finished"] = time.time()
            self.save(group, state)
            with LOCK:
                ACTIVE.discard(group)

    def export_files(self, group, state):
        root = self.files._listing(group)
        listings = [("", root)]
        folders = list(root.get("folders") or [])
        seen = set()
        while folders:
            folder = folders.pop(0)
            fid = str(folder.get("folder_id") or folder.get("folder"))
            if fid in seen:
                continue
            seen.add(fid)
            data = self.files.onebot("get_group_files_by_folder", {
                "group_id": int(group), "folder_id": fid, "file_count": 10000})
            if not isinstance(data, dict):
                raise RuntimeError("群文件夹未返回列表")
            listings.append((fid, data))
            folders.extend(data.get("folders") or [])
        rows = [(folder, row) for folder, listing in listings for row in listing.get("files") or []]
        (self.directory(group) / "files.json").write_text(
            json.dumps(listings, ensure_ascii=False, indent=2), encoding="utf-8")
        state["total"] = len(rows)
        required = sum(int(row.get("file_size") or row.get("size") or 0) for _, row in rows)
        if required * 2 > shutil.disk_usage(self.files.root).free:
            raise RuntimeError("磁盘空间不足以保存原文件与下载缓存")
        for folder, row in rows:
            try:
                with EXPORT_LOCK:
                    result = self.files.export_observed(group, folder, row)
                state["completed"] += 1
                state["bytes"] += result["bytes"]
            except Exception as exc:
                result = {"status": "failed", "folder_id": folder, "file_name": row.get("file_name"), "error": str(exc)}
                state["failed"] += 1
            state["results"].append(result)
            self.save(group, state)

    def export_essence(self, group, state):
        directory = checked_directory(self.files.root, "qq_group_essence", group)
        media = checked_directory(directory, "media")
        manifest = directory / "messages.json"
        records = json.loads(manifest.read_text(encoding="utf-8"))["messages"] if manifest.exists() else []
        known = {str(row["message_id"]): row for row in records}
        seen = set()
        for page in range(10000):
            rows = find_list(self.files.onebot("get_essence_msg_list", {
                "group_id": int(group), "page": page, "offset": page * 100, "page_size": 100, "limit": 100}))
            fresh = [row for row in rows if message_id(row) not in seen]
            if not fresh:
                break
            for raw in fresh:
                mid = message_id(raw)
                seen.add(mid)
                if mid in known and not known[mid].get("incomplete"):
                    continue
                record = {**raw, "message_id": mid, "group_id": group, "media": [], "incomplete": False}
                try:
                    if not has_message_content(raw):
                        detail = self.files.onebot("get_msg", {"message_id": mid})
                        if not isinstance(detail, dict) or not has_message_content(detail):
                            raise RuntimeError("原消息正文不可取得")
                        record.update(detail)
                    for index, (kind, url, _) in enumerate(extract_media(record)):
                        target = media / f"{mid}_{index}"
                        try:
                            if not target.is_file():
                                temporary, _ = self.files._download(url, media)
                                temporary.replace(target)
                            record["media"].append({"type": kind, "file": str(target.relative_to(directory)),
                                                    "source": url})
                        except Exception as exc:
                            record["incomplete"] = True
                            record["media"].append({"type": kind, "source": url, "error": str(exc)})
                except Exception as exc:
                    record.update(incomplete=True, error=str(exc))
                known[mid] = record
                temporary = manifest.with_suffix(".tmp")
                temporary.write_text(json.dumps({"group_id": group, "messages": list(known.values())},
                                                ensure_ascii=False, indent=2), encoding="utf-8")
                temporary.replace(manifest)
            if len(rows) < 100:
                break
        state["essence_messages"] = len(known)
        state["essence_incomplete"] = sum(bool(row.get("incomplete")) for row in known.values())
        state["failed"] += state["essence_incomplete"]


def install_archive_tools(registry, files):
    archive = GroupArchive(files)
    registry.register("export_group_archive", archive.start, admin_only=True,
                      parameters={"kind": {"type": "string", "enum": ["all", "files", "essence"]}},
                      description="管理员后台导出本群全部群文件、精华消息及媒体到 underline_wiki。kind=all/files/essence。返回 queued 只表示开始，可重复发起以续跑。")
    registry.register("group_archive_status", archive.status, admin_only=True,
                      description="查询本群批量导出状态、数量与失败数。partial 表示部分失败，不能声称全部成功。")
