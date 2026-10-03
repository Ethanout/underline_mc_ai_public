"""Pluggable text embedding backends for the QQ style memory.

Importing this module loads no model and opens no socket: the QQ bot keeps
running on the CPU-only base dependencies.  A backend is only built when
``build_embedder`` is called, so the FastAPI process never pays for it.

The default backend is ``api``: SiliconFlow serves the same ``bge-m3`` weights
over an OpenAI-compatible endpoint, so nothing has to be downloaded and no
several-GB model is held in memory.  The trade is that the default now needs
``QQBOT_EMBED_API_KEY`` -- and it fails loudly without one, which is the point.
The alternative default fails quietly: ``local`` would pull ``BAAI/bge-m3``
from HuggingFace on first use, and someone who never meant to run it locally
would sit through a multi-gigabyte download before learning they had a choice.
Set ``QQBOT_EMBED_BACKEND=local`` to keep everything on this machine; that path
runs on the **CPU** so the GPU stays free for the user's own work.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Protocol, Sequence, runtime_checkable


DEFAULT_LOCAL_MODEL = "BAAI/bge-m3"
DEFAULT_API_BASE = "https://api.siliconflow.cn/v1"
DEFAULT_API_MODEL = "BAAI/bge-m3"


@runtime_checkable
class Embedder(Protocol):
    """Turns a batch of strings into vectors that share one space."""

    name: str

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one vector per input string, in the same order."""


class LocalEmbedder:
    """sentence-transformers backend.  CPU by default, so the GPU stays free."""

    def __init__(
        self,
        model_name: str = DEFAULT_LOCAL_MODEL,
        device: str = "cpu",
        batch_size: int = 16,
    ) -> None:
        from sentence_transformers import SentenceTransformer

        self.name = f"local:{model_name}:{device}"
        self.batch_size = batch_size
        self._model = SentenceTransformer(model_name, device=device)

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [[float(value) for value in vector] for vector in vectors]


class ApiEmbedder:
    """OpenAI-compatible ``/embeddings`` backend (SiliconFlow, OpenAI, ...)."""

    def __init__(
        self,
        base_url: str = DEFAULT_API_BASE,
        api_key: str = "",
        model: str = DEFAULT_API_MODEL,
        batch_size: int = 32,
        timeout: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("API embedding 后端需要 api_key")
        self.name = f"api:{model}"
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.batch_size = batch_size
        self.timeout = timeout

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            vectors.extend(self._request_batch(list(texts[start : start + self.batch_size])))
        return vectors

    def _request_batch(self, texts: list[str]) -> list[list[float]]:
        payload = json.dumps({"model": self.model, "input": texts}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/embeddings",
            data=payload,
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        rows = sorted(data["data"], key=lambda row: row.get("index", 0))
        return [[float(value) for value in row["embedding"]] for row in rows]


def build_embedder(
    backend: str | None = None,
    model: str | None = None,
    device: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> Embedder:
    """Build the configured backend.  Explicit arguments beat environment."""
    selected = (backend or os.environ.get("QQBOT_EMBED_BACKEND", "api")).strip().lower()
    if selected == "api":
        return ApiEmbedder(
            base_url=base_url or os.environ.get("QQBOT_EMBED_BASE_URL", DEFAULT_API_BASE),
            api_key=api_key or os.environ.get("QQBOT_EMBED_API_KEY", ""),
            model=model or os.environ.get("QQBOT_EMBED_MODEL", DEFAULT_API_MODEL),
        )
    if selected != "local":
        raise ValueError(f"未知的 embedding 后端：{selected}")
    return LocalEmbedder(
        model_name=model or os.environ.get("QQBOT_EMBED_MODEL", DEFAULT_LOCAL_MODEL),
        device=device or os.environ.get("QQBOT_EMBED_DEVICE", "cpu"),
    )
