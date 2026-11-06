"""Read current-group files and preserve selected originals in the Wiki."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

from .web_research import PublicRedirect, public_url

MAX_BYTES = 64 * 1024 * 1024
EXPORT_LOCK = threading.Lock()
FILE_FIELDS = ("file_id", "file_name", "busid", "file_size", "size", "upload_time",
               "modify_time", "dead_time", "uploader", "uploader_name")
IDENTITY_FIELDS = ("file_name", "uploader", "upload_time")


def safe_filename(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(name)).strip(" .")[:120]
    if not name:
        name = "attachment"
    if name.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(10)), *(f"LPT{i}" for i in range(10))}:
        name = "_" + name
    return name


def checked_directory(root, *parts):
    path = root.joinpath(*parts)
    if not path.resolve().is_relative_to(root):
        raise ValueError("Wiki 导出目录指向根目录以外，未写入")
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class GroupFiles:
    def __init__(self, onebot, root=None, opener=None, clock=time.time, store=None):
        self.onebot = onebot
        self.root = Path(root or os.environ.get("UNDERLINE_WIKI_ROOT", "../underline_wiki")).resolve()
        self.opener = opener or urllib.request.build_opener(PublicRedirect()).open
        self.clock = clock
        self.store = store
        self.snapshots = {}
        self.max_bytes = max(1, int(os.environ.get("QQBOT_GROUP_FILE_MAX_BYTES", str(MAX_BYTES))))

    def _listing(self, group_id, folder_id=""):
        if not re.fullmatch(r"\d{1,32}", str(group_id)):
            raise ValueError("群号须为数字")
        if not self.onebot:
            raise RuntimeError("OneBot 工具未配置")
        root = self.onebot("get_group_root_files", {"group_id": int(group_id), "file_count": 10000})
        if not isinstance(root, dict):
            raise RuntimeError("群文件接口未返回列表")
        if not folder_id:
            return root
        if not any(str(row.get("folder_id") or row.get("folder")) == folder_id for row in root.get("folders") or []):
            raise ValueError("文件夹不在当前群的根目录列表中")
        result = self.onebot("get_group_files_by_folder", {"group_id": int(group_id), "folder_id": folder_id, "file_count": 10000})
        if not isinstance(result, dict):
            raise RuntimeError("群文件夹接口未返回列表")
        return result

    def _remember_listing(self, group, folder, rows):
        state_key = "qq-file-snapshots:" + str(group)
        snapshots = self.store.get_state(state_key, {}) if self.store else self.snapshots.get(str(group), {})
        for row in rows:
            if row.get("group_id") is not None and str(row["group_id"]) != str(group):
                raise PermissionError("群文件列表包含其他群的文件")
            key = str(row["file_id"])
            snapshot = {"folder_id": folder, "file": {key: row.get(key) for key in FILE_FIELDS}}
            snapshots[key] = snapshot
        # NapCat creates fresh IDs on each listing. Retain bounded observations.
        snapshots = dict(list(snapshots.items())[-20000:])
        if self.store:
            self.store.set_state(state_key, snapshots)
        else:
            self.snapshots[str(group)] = snapshots

    def _known_file(self, group, fid):
        snapshots = self.store.get_state("qq-file-snapshots:" + group, {}) if self.store else self.snapshots.get(group, {})
        return snapshots.get(fid, {})

    def list_files(self, task, args):
        folder = str(args.get("folder_id") or "")
        data = self._listing(task["group_id"], folder)
        self._remember_listing(task["group_id"], folder, data.get("files") or [])
        keyword = str(args.get("keyword") or "").casefold()
        rows = [{"kind": "file", **{key: row.get(key) for key in FILE_FIELDS}} for row in data.get("files") or []]
        rows += [{"kind": "folder", "folder_id": row.get("folder_id") or row.get("folder"),
                  "folder_name": row.get("folder_name"), "total_file_count": row.get("total_file_count")}
                 for row in data.get("folders") or []]
        rows.sort(key=lambda row: row["kind"] != "folder")
        rows = [row for row in rows if keyword in str(row.get("file_name") or row.get("folder_name") or "").casefold()]
        limit = max(1, min(50, int(args.get("limit", 20))))
        offset = max(0, int(args.get("offset", 0)))
        return {"group_id": task["group_id"], "folder_id": folder, "results": rows[offset:offset + limit],
                "total": len(rows), "next_offset": offset + limit if offset + limit < len(rows) else None,
                "scope": "当前文件夹；未递归扫描；仅反映 OneBot 实际返回的列表"}

    def _download(self, url, directory):
        request = urllib.request.Request(public_url(url), headers={"Accept-Encoding": "identity"})
        temp_path = None
        try:
            with self.opener(request, timeout=20) as response:
                public_url(response.geturl())
                length = response.headers.get("Content-Length")
                if length and int(length) > self.max_bytes:
                    raise ValueError("群文件超过下载大小上限")
                with tempfile.NamedTemporaryFile(dir=directory, delete=False) as stream:
                    temp_path = Path(stream.name)
                    size, started = 0, time.monotonic()
                    while chunk := response.read(64 * 1024):
                        size += len(chunk)
                        if size > self.max_bytes or time.monotonic() - started > 60:
                            raise ValueError("群文件超过下载大小或时间上限")
                        stream.write(chunk)
            return temp_path, size
        except (OSError, ValueError) as exc:
            if temp_path:
                temp_path.unlink(missing_ok=True)
            # QQ download URLs can carry credentials. Keep them out of tool audits.
            raise RuntimeError(f"群文件下载失败：{type(exc).__name__}，未导出") from exc

    def export_file(self, task, args):
        with EXPORT_LOCK:
            return self._export_file(task, args)

    def _obtain_file(self, group, row, directory):
        transport = os.environ.get("QQBOT_GROUP_FILE_TRANSPORT", "native")
        if transport == "url":
            params = {"group_id": int(group), "file_id": str(row["file_id"])}
            if row.get("busid") is not None:
                params["busid"] = row["busid"]
            result = self.onebot("get_group_file_url", params)
            url = result.get("url") if isinstance(result, dict) else None
            if not url:
                raise RuntimeError("OneBot 未返回群文件下载地址")
            return self._download(url, directory)
        if transport != "native":
            raise ValueError("QQBOT_GROUP_FILE_TRANSPORT 须为 native 或 url")
        # get_file uses the QQ client's native downloader, without PacketBackend.
        result = self.onebot("get_file", {"file_id": str(row["file_id"])})
        source = Path(result.get("file") or "") if isinstance(result, dict) else Path()
        if not source.is_absolute() or not source.is_file():
            raise RuntimeError("NapCat 原生下载未返回可读取的本地文件")
        if source.stat().st_size > self.max_bytes:
            raise ValueError("群文件超过下载大小上限")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=directory, delete=False) as output, source.open("rb") as stream:
                temporary, size = Path(output.name), 0
                for chunk in iter(lambda: stream.read(64 * 1024), b""):
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise ValueError("群文件超过下载大小上限")
                    output.write(chunk)
            return temporary, size
        except (OSError, ValueError):
            if temporary:
                temporary.unlink(missing_ok=True)
            raise

    def _export_file(self, task, args):
        group, folder, fid = str(task["group_id"]), str(args.get("folder_id") or ""), str(args["file_id"])
        known = self._known_file(group, fid)
        data = self._listing(group, folder)
        row = next((row for row in data.get("files") or [] if str(row.get("file_id")) == fid), None)
        # NapCat encodes a fresh model ID for every listing. Refresh only from
        # a scoped, persisted observation; never accept a model-invented filename.
        if row is None and known.get("folder_id") == folder:
            candidates = [row for row in data.get("files") or []
                          if all(row.get(key) == known["file"].get(key) for key in IDENTITY_FIELDS)]
            if len(candidates) > 1:
                raise ValueError("多个群文件具有相同来源信息，请重新查询并指定文件")
            row = candidates[0] if candidates else None
        if row is None or (row.get("group_id") is not None and str(row["group_id"]) != group):
            raise ValueError("文件不在当前群指定文件夹的实际列表中")
        return self.export_observed(group, folder, row)

    def export_observed(self, group, folder, row):
        """Archive an actual scoped listing row, without refreshing ephemeral IDs."""
        metadata = {key: row.get(key) for key in FILE_FIELDS}
        size = int(row.get("file_size") or row.get("size") or 0)
        if size < 0 or size > self.max_bytes:
            raise ValueError("群文件超过下载大小上限")
        source_id = hashlib.sha256(json.dumps([group, folder, *[row.get(key) for key in IDENTITY_FIELDS]], ensure_ascii=False).encode()).hexdigest()
        directory = checked_directory(self.root, "qq_group_files", group, source_id)
        stamp = hashlib.sha256(json.dumps({key: value for key, value in metadata.items() if key != "file_id"}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        receipt_path = directory / (stamp + ".json")
        if receipt_path.exists():
            if not receipt_path.resolve().is_relative_to(self.root):
                raise ValueError("来源清单指向 Wiki 根目录以外")
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            saved = Path(receipt["path"])
            if not saved.resolve().is_relative_to(directory.resolve()):
                raise ValueError("来源清单的文件路径无效")
            if saved.is_file() and file_hash(saved) == receipt["sha256"]:
                return {**receipt, "status": "already_exported"}
            raise ValueError("已导出文件被修改或移除，请检查来源清单；未覆盖")
        temporary, downloaded_size = self._obtain_file(group, row, directory)
        try:
            if size and downloaded_size != size:
                raise ValueError("下载大小与群文件列表不一致，未导出")
            sha256 = file_hash(temporary)
            version = checked_directory(self.root, "qq_group_files", group, source_id, sha256)
            path = version / safe_filename(row.get("file_name") or "attachment")
            if path.exists() or path.is_symlink():
                if not path.resolve().is_relative_to(self.root) or file_hash(path) != sha256:
                    raise ValueError("导出目标已有不同内容，未覆盖")
            else:
                # Exclusive creation preserves any file created by another process.
                with path.open("xb") as output, temporary.open("rb") as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        output.write(chunk)
            receipt = {"status": "exported", "source_id": "qq-file:" + source_id, "group_id": group,
                       "folder_id": folder, "file": metadata, "sha256": sha256, "bytes": downloaded_size,
                       "path": str(path), "exported_at": self.clock(), "verification": "原始群文件，未验证"}
            with receipt_path.open("x", encoding="utf-8") as output:
                json.dump(receipt, output, ensure_ascii=False, indent=2)
            return receipt
        finally:
            temporary.unlink(missing_ok=True)


def install_group_file_tools(registry, library=None):
    library = library or GroupFiles(registry.onebot, clock=registry.store.clock, store=registry.store)
    def list_bounded(task, args):
        return library.list_files(task, {**args, "limit": min(registry.max_items, int(args.get("limit", 20)))})
    registry.register("list_group_files", list_bounded, parameters={
        "folder_id": {"type": "string"}, "keyword": {"type": "string"},
        "offset": {"type": "integer"}, "limit": {"type": "integer"}},
        description="列出本群根目录或指定文件夹的群文件。返回真实 file_id 和 folder_id，可用 keyword 筛选名称和 offset 分页。未递归扫描。文件名称仅作资料。")
    registry.register("export_group_file", library.export_file, admin_only=True, parameters={
        "file_id": {"type": "string"}, "folder_id": {"type": "string"}},
        description="管理员将本群选定文件导出到固定 underline_wiki/qq_group_files 目录，保留原文件和来源清单。先查列表取得真实 ID。返回 exported/already_exported 才能说成功。文件未经验证，压缩包原样保存。")
    from .group_archive import install_archive_tools
    install_archive_tools(registry, library)
    return library
