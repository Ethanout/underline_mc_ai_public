"""Short-lived DeepSeek file references for cached group images."""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import time
import urllib.request
import uuid
import base64
import threading
from pathlib import Path

from .store import Store
from .images import sniff_image, image_segments

MIN_TTL = 3600
MAX_TTL = 2592000


def image_part(file_id: str) -> dict:
    """Build the image content part in one place for future API changes."""
    return {"type": "file", "file_id": file_id}


def clamp_ttl(value=None) -> int:
    try:
        number = int(value if value is not None else os.environ.get("QQBOT_IMAGE_FILE_TTL", "86400"))
    except ValueError:
        number = 86400
    return max(MIN_TTL, min(MAX_TTL, number))


class DeepSeekImageFiles:
    def __init__(self, store: Store, api_key: str, post=None, now=time.time, ttl=None):
        self.store, self.api_key, self.post, self.now = store, api_key, post, now
        self.ttl = clamp_ttl(ttl)
        self.lock = threading.RLock()

    def file_id(self, path: str | Path) -> str:
        with self.lock:
            return self._file_id(path)

    def _file_id(self, path: str | Path) -> str:
        image = Path(path)
        if not image.is_file():
            raise FileNotFoundError("图片未缓存，不能上传")
        raw = image.read_bytes()
        if len(raw) > 64 * 1024 * 1024:
            raise ValueError("图片超过 64 MiB")
        sniffed = sniff_image(raw)
        if not sniffed or sniffed[0] not in {"image/jpeg", "image/png", "image/gif", "image/webp"}:
            raise ValueError("图片格式必须是 JPEG、PNG、GIF 或 WebP")
        digest = hashlib.sha256(raw).hexdigest()
        rows = self.store.rows("SELECT file_id,expires_at FROM image_files WHERE sha256=?", (digest,))
        if rows and float(rows[0]["expires_at"]) - self.now() >= 600:
            return rows[0]["file_id"]
        file_id, expires = self.upload(image)
        self.store.write("INSERT OR REPLACE INTO image_files VALUES(?,?,?,?)", (digest, file_id, expires, str(image)))
        return file_id

    def cached_parts(self, event, cache):
        parts, missing = [], []
        for ref in image_segments(event):
            path = cache.get(ref)
            if path is None:
                missing.append("[图片:未缓存]")
            else:
                parts.append(image_part(self.file_id(path)))
        return parts, missing

    def summarize(self, event, cache, completion_post, model="deepseek-flash"):
        """Cache one summary per image content without fetching remote links."""
        summaries = []
        with self.lock:
            for ref in image_segments(event):
                path = cache.get(ref)
                if path is None:
                    summaries.append("未缓存")
                    continue
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                summary = self.store.get_state(f"image_summary:{digest}")
                if summary is None:
                    payload = {"model": model, "max_tokens": 100, "messages": [{"role": "user", "content": [
                        {"type": "text", "text": "用一句话描述图片。"}, image_part(self.file_id(path))]}]}
                    try:
                        data = completion_post(payload)
                        summary = str(data["choices"][0]["message"].get("content") or "摘要为空")
                    except Exception:
                        summary = "摘要失败"
                    self.store.set_state(f"image_summary:{digest}", summary)
                summaries.append(summary)
            row = self.store.message(str(event.get("group_id", "")), str(event.get("message_id", "")))
            if row:
                segments = json.loads(row["segments"])
                index = 0
                for segment in segments:
                    if segment.get("type") == "image":
                        segment.setdefault("data", {})["summary"] = summaries[index] if index < len(summaries) else "未缓存"
                        index += 1
                self.store.write("UPDATE messages SET image_summary=?,segments=? WHERE id=?", (" | ".join(summaries), json.dumps(segments, ensure_ascii=False), row["id"]))
        return summaries

    def upload(self, path: Path) -> tuple[str, float]:
        body, content_type = multipart(path, self.ttl)
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": content_type}
        try:
            data = self.post(body, headers) if self.post else _request(body, headers)
            file_id = str(data["id"])
        except Exception as exc:
            raise RuntimeError(f"上传图片到 DeepSeek 失败：{exc}") from exc
        if not file_id.startswith("file-api-"):
            raise RuntimeError("上传图片失败：接口没有返回 file-api ID")
        return file_id, float(data.get("expires_at") or self.now() + self.ttl)


def multipart(path: Path, ttl: int) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    chunks = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nuser_data\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"expires_after[anchor]\"\r\n\r\ncreated_at\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"expires_after[seconds]\"\r\n\r\n{ttl}\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"image{path.suffix}\"\r\nContent-Type: {mime}\r\n\r\n".encode(),
        path.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _request(body, headers):
    request = urllib.request.Request("https://api.deepseek.com/files", data=body, method="POST", headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))
