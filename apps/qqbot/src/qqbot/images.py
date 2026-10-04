"""QQ image segments: find them, and keep a local copy before the link dies.

QQ group image URLs carry a short-lived ``rkey``; a link that worked when the
message arrived is usually dead by the next day.  The style memory runs offline,
often long after the fact, so waiting until ingestion to download means most
images are already gone.  The web process therefore calls
:meth:`ImageCache.fetch_event` as each message arrives, and ingestion reads the
local copy -- only falling back to a download of its own when the cache missed.

The cache key is NapCat's ``file`` field when present (a content hash, so the
same sticker posted ten times is stored once), else the URL.  Only ``http`` and
``https`` URLs are fetched; the payload is capped and must look like an image by
its magic bytes, since the URL comes from an event body.
"""
from __future__ import annotations

import base64
import hashlib
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


DEFAULT_IMAGE_DIR = "runtime/private/qq_images"
MAX_IMAGE_BYTES = 10_000_000

_MAGIC: tuple[tuple[bytes, str, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"GIF87a", "image/gif", ".gif"),
    (b"GIF89a", "image/gif", ".gif"),
    (b"BM", "image/bmp", ".bmp"),
)
_EXTENSION_MIME = {ext: mime for _, mime, ext in _MAGIC}
_EXTENSION_MIME[".webp"] = "image/webp"


def sniff_image(data: bytes) -> tuple[str, str] | None:
    """Return ``(mime, extension)`` judged by magic bytes, or None."""
    for magic, mime, extension in _MAGIC:
        if data.startswith(magic):
            return mime, extension
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", ".webp"
    return None


@dataclass(frozen=True)
class ImageRef:
    """One ``image`` segment of a OneBot message."""

    index: int
    url: str
    file: str = ""
    summary: str = ""
    sub_type: str = ""

    @property
    def cache_key(self) -> str:
        return hashlib.sha256((self.file or self.url).encode("utf-8")).hexdigest()[:32]


def image_segments(event: dict) -> list[ImageRef]:
    """Return the fetchable image segments of one message, in order."""
    segments = event.get("message")
    if not isinstance(segments, list):
        return []
    refs: list[ImageRef] = []
    for segment in segments:
        if not isinstance(segment, dict) or segment.get("type") != "image":
            continue
        data = segment.get("data") if isinstance(segment.get("data"), dict) else {}
        url = str(data.get("url") or "")
        if urllib.parse.urlparse(url).scheme not in ("http", "https"):
            continue
        refs.append(
            ImageRef(
                index=len(refs),
                url=url,
                file=str(data.get("file") or ""),
                summary=str(data.get("summary") or ""),
                sub_type=str(data.get("sub_type") if data.get("sub_type") is not None else ""),
            )
        )
    return refs


def data_uri(path: str | Path) -> str:
    """Encode a cached image as the ``data:`` URI the embedding API expects.

    SiliconFlow rejects bare base64 with a generic "parameter is invalid", so
    the mime prefix is not optional.
    """
    raw = Path(path).read_bytes()
    sniffed = sniff_image(raw)
    mime = sniffed[0] if sniffed else _EXTENSION_MIME.get(Path(path).suffix.lower(), "image/png")
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


class ImageCache:
    """Content-addressed local copies of QQ images."""

    def __init__(self, root: str | Path, max_bytes: int = MAX_IMAGE_BYTES, timeout: float = 30.0) -> None:
        self.root = Path(root)
        self.max_bytes = max_bytes
        self.timeout = timeout

    def get(self, ref: ImageRef) -> Path | None:
        """Return the cached copy, if one exists."""
        if not self.root.is_dir():
            return None
        for candidate in self.root.glob(f"{ref.cache_key}.*"):
            if candidate.suffix != ".part":
                return candidate
        return None

    def fetch(self, ref: ImageRef) -> Path:
        """Return the cached copy, downloading it first if needed."""
        cached = self.get(ref)
        if cached is not None:
            return cached
        data = self._download(ref.url)
        sniffed = sniff_image(data)
        if sniffed is None:
            raise ValueError("下载到的不是图片")
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / f"{ref.cache_key}{sniffed[1]}"
        partial = target.with_suffix(".part")
        partial.write_bytes(data)
        os.replace(partial, target)
        return target

    def fetch_event(self, event: dict) -> int:
        """Cache every image in one message; never raises.  Returns how many."""
        cached = 0
        for ref in image_segments(event):
            try:
                self.fetch(ref)
            except Exception as exc:  # noqa: BLE001 - a dead link must not break the event path
                print(f"群图片缓存失败（{event.get('message_id')}#{ref.index}）：{exc}")
                continue
            cached += 1
        return cached

    def _download(self, url: str) -> bytes:
        if urllib.parse.urlparse(url).scheme not in ("http", "https"):
            raise ValueError("只下载 http/https 图片")
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = response.read(self.max_bytes + 1)
        if len(data) > self.max_bytes:
            raise ValueError(f"图片超过 {self.max_bytes} 字节")
        return data
