"""Local configuration, read in one place so filling ``.env`` is the whole setup.

Importing ``qqbot`` runs :func:`load_settings`, which means every entry point --
``python -m qqbot.web``, ``qqbot-style-memory``, the root ``app.py`` -- sees the
same values without a per-shell ``$env:`` line.  Order matters: ``web.py`` reads
four variables at *module import* time, so the load has to happen before that
module is imported, and ``qqbot/__init__.py`` is the earliest shared point.

Secrets do not have to live here.  ``web.py`` already read ``DEEPSEEK_KEY_FILE``
and treated its contents as the key; ``KEY_FILES`` generalises that, so an API
key stays in whatever file it already lives in and ``.env`` only names the path.
A real environment variable always wins over both, so a one-off override still
works the way it always did.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ENV_FILE_VAR = "QQBOT_ENV_FILE"
DEFAULT_ENV_FILE = ".env"

# ``<NAME>_FILE`` names a file; the paired ``<NAME>`` gets its stripped contents.
KEY_FILES: dict[str, str] = {
    "QQBOT_EMBED_API_KEY_FILE": "QQBOT_EMBED_API_KEY",
    "DEEPSEEK_KEY_FILE": "DEEPSEEK_API_KEY",
    "ONEBOT_ACCESS_TOKEN_FILE": "ONEBOT_ACCESS_TOKEN",
    "QQBOT_EVENT_TOKEN_FILE": "QQBOT_EVENT_TOKEN",
}

# Reported by ``qqbot-config``; values are shown as set/absent, never printed.
REPORTED_VARS: tuple[str, ...] = (
    "QQBOT_EMBED_BACKEND",
    "QQBOT_EMBED_BASE_URL",
    "QQBOT_EMBED_MODEL",
    "QQBOT_EMBED_DEVICE",
    "QQBOT_EMBED_API_KEY",
    "DEEPSEEK_API_KEY",
    "ONEBOT_ACCESS_TOKEN",
    "QQBOT_EVENT_TOKEN",
    "QQBOT_EVENT_LOG",
    "QQBOT_STYLE_DB",
    "QQBOT_IMAGE_DIR",
    "QQBOT_WEB_HOST",
    "QQBOT_WEB_PORT",
)

_loaded = False
_env_path: Path | None = None
_key_file_sources: dict[str, str] = {}


def find_env_file(start: Path | None = None) -> Path | None:
    """Locate the ``.env`` to load: ``QQBOT_ENV_FILE``, else nearest upward.

    Searching upward from the working directory matches how every other path in
    this repo resolves, so running from the repo root or from ``apps/qqbot/``
    both find the same file.
    """
    override = os.environ.get(ENV_FILE_VAR, "").strip()
    if override:
        candidate = Path(override).expanduser()
        return candidate if candidate.is_file() else None
    directory = (start or Path.cwd()).resolve()
    for parent in (directory, *directory.parents):
        candidate = parent / DEFAULT_ENV_FILE
        if candidate.is_file():
            return candidate
    return None


def _apply_key_files() -> dict[str, str]:
    """Fill ``<NAME>`` from the file named by ``<NAME>_FILE``, when unset."""
    sources: dict[str, str] = {}
    for path_var, value_var in KEY_FILES.items():
        if os.environ.get(value_var, "").strip():
            continue
        raw_path = os.environ.get(path_var, "").strip()
        if not raw_path:
            continue
        candidate = Path(raw_path).expanduser()
        try:
            secret = candidate.read_text(encoding="utf-8").strip()
        except OSError as exc:
            print(f"读不了 {path_var} 指向的文件：{exc}", file=sys.stderr)
            continue
        if secret:
            os.environ[value_var] = secret
            sources[value_var] = raw_path
    return sources


def load_settings(force: bool = False) -> Path | None:
    """Load ``.env`` once and resolve the key-file variables.  Idempotent."""
    global _loaded, _env_path
    if _loaded and not force:
        return _env_path
    _loaded = True

    found = find_env_file()
    if found is not None:
        try:
            from dotenv import load_dotenv
        except ImportError:
            print(
                "找到了 .env 但没装 python-dotenv，这次不会读它：pip install python-dotenv",
                file=sys.stderr,
            )
        else:
            load_dotenv(found, override=False)
            _env_path = found

    _key_file_sources.update(_apply_key_files())
    return _env_path


def described() -> list[tuple[str, str]]:
    """Return ``(variable, description)`` pairs for the config report."""
    rows: list[tuple[str, str]] = []
    for name in REPORTED_VARS:
        value = os.environ.get(name, "").strip()
        source = _key_file_sources.get(name, "")
        if not value:
            rows.append((name, "未设置"))
        elif source:
            rows.append((name, f"已设置（长度 {len(value)}，来自 {source}）"))
        else:
            rows.append((name, f"已设置（长度 {len(value)}）"))
    return rows


def main() -> int:
    """Print what the environment resolved to, without printing any secret."""
    from .style_memory import _force_utf8_stdout

    _force_utf8_stdout()
    load_settings()
    if _env_path is not None:
        print(f"配置文件：{_env_path}")
    else:
        print(f"没找到 {DEFAULT_ENV_FILE}（可以用 {ENV_FILE_VAR} 指定路径），只读进程环境变量")
    for name, description in described():
        print(f"  {name}={description}")

    from .embedding import build_embedder

    backend = os.environ.get("QQBOT_EMBED_BACKEND", "api").strip().lower()
    print(f"\nembedding 后端：{backend}")
    try:
        embedder = build_embedder()
    except ValueError as exc:
        print(f"  建不起来：{exc}")
        return 1
    print(f"  {embedder.name}")
    if backend == "api":
        # One short request proves the key, the base URL and the model at once.
        try:
            vector = embedder.encode(["连接测试"])[0]
        except Exception as exc:  # noqa: BLE001 - report whatever the endpoint said
            print(f"  连不上：{exc}")
            return 1
        print(f"  通得过，向量维度 {len(vector)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
