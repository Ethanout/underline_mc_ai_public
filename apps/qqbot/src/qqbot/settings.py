"""Local configuration, read in one place so filling ``.env`` is the whole setup.

Importing ``qqbot`` runs :func:`load_settings`, which means every entry point --
``python -m qqbot.web``, ``python -m qqbot start``, the root ``app.py`` -- sees the
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
    "DEEPSEEK_KEY_FILE": "DEEPSEEK_API_KEY",
    "ONEBOT_ACCESS_TOKEN_FILE": "ONEBOT_ACCESS_TOKEN",
    "QQBOT_EVENT_TOKEN_FILE": "QQBOT_EVENT_TOKEN",
    "QQBOT_PLUGIN_TOKEN_FILE": "QQBOT_PLUGIN_TOKEN",
}
DEFAULT_PLUGIN_TOKEN_FILE = "config/api/qqbot_plugin.txt"

# Reported by ``qqbot-config``; values are shown as set/absent, never printed.
REPORTED_VARS: tuple[str, ...] = (
    "NAPCAT_DIR",
    "NAPCAT_UIN",
    "MAIBOT_DIR",
    "MAIBOT_NAPCAT_WS_PORT",
    "DEEPSEEK_API_KEY",
    "ONEBOT_ENDPOINT",
    "ONEBOT_ACCESS_TOKEN",
    "QQBOT_EVENT_TOKEN",
    "QQBOT_PLUGIN_TOKEN",
    "QQBOT_ADMIN_IDS",
    "QQBOT_GROUPS",
    "QQBOT_MODEL",
    "QQBOT_REASONING_EFFORT",
    "QQBOT_THINKING_BUDGET",
    "QQBOT_TASK_MAX_TOKENS",
    "QQBOT_TOOL_ROUNDS",
    "QQBOT_TOOL_MAX_ITEMS",
    "QQBOT_TOOL_MAX_CHARS",
    "QQBOT_IMAGE_FILE_TTL",
    "QQBOT_EVENT_LOG",
    "QQBOT_IMAGE_DIR",
    "QQBOT_DB",
    "QQBOT_REPLY_CONTEXT_CHARS",
    "QQBOT_TRICKS_DIR",
    "QQBOT_ESSENCE_SYNC_MINUTES",
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
    _key_file_sources.update(_apply_napcat())
    _key_file_sources.update(_apply_plugin_token())
    return _env_path


def _apply_plugin_token() -> dict[str, str]:
    """Generate the token the MaiBot plugin uses, once ``MAIBOT_DIR`` is set.

    Unlike the event token, there is no "open" fallback: without this token the
    plugin endpoints refuse every call (see ``web.plugin_authorized``).
    """
    if os.environ.get("QQBOT_PLUGIN_TOKEN", "").strip():
        return {}
    if not os.environ.get("MAIBOT_DIR", "").strip():
        return {}
    from . import napcat

    token_file = os.environ.get("QQBOT_PLUGIN_TOKEN_FILE", "").strip() or DEFAULT_PLUGIN_TOKEN_FILE
    try:
        os.environ["QQBOT_PLUGIN_TOKEN"] = napcat.ensure_event_token(token_file)
    except OSError as exc:
        print(f"插件 token 文件 {token_file} 读写失败：{exc}", file=sys.stderr)
        return {}
    return {"QQBOT_PLUGIN_TOKEN": token_file}


def _apply_napcat() -> dict[str, str]:
    """Fill the OneBot side from NapCat's own config, when ``NAPCAT_DIR`` is set.

    NapCat already holds the API endpoint and token, so copying them into
    ``.env`` only creates a second place to get them wrong.  The event token is
    generated on first use.  Failures are reported, never raised: a missing
    NapCat must not stop the exporter or tests from importing ``qqbot``.
    """
    from . import napcat

    directory = napcat.napcat_dir()
    if directory is None:
        return {}
    sources: dict[str, str] = {}
    if not os.environ.get("QQBOT_EVENT_TOKEN", "").strip():
        token_file = (
            os.environ.get("QQBOT_EVENT_TOKEN_FILE", "").strip() or napcat.DEFAULT_EVENT_TOKEN_FILE
        )
        try:
            os.environ["QQBOT_EVENT_TOKEN"] = napcat.ensure_event_token(token_file)
            sources["QQBOT_EVENT_TOKEN"] = token_file
        except OSError as exc:
            print(f"事件 token 文件 {token_file} 读写失败：{exc}", file=sys.stderr)
    try:
        path = napcat.find_config(directory, os.environ.get("NAPCAT_UIN", "").strip())
        server = napcat.api_server(napcat.read_config(path))
    except (OSError, ValueError) as exc:
        print(f"读不了 NapCat 配置：{exc}", file=sys.stderr)
        return sources
    if server is None:
        print(f"{path} 里没有启用的 HTTP 服务端，导出和回复都连不上 NapCat", file=sys.stderr)
        return sources
    if not os.environ.get("ONEBOT_ENDPOINT", "").strip():
        os.environ["ONEBOT_ENDPOINT"] = server.endpoint
        sources["ONEBOT_ENDPOINT"] = "NapCat 配置"
    if server.token and not os.environ.get("ONEBOT_ACCESS_TOKEN", "").strip():
        os.environ["ONEBOT_ACCESS_TOKEN"] = server.token
        sources["ONEBOT_ACCESS_TOKEN"] = "NapCat 配置"
    return sources


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


def force_utf8_stdout() -> None:
    """Windows consoles default to GBK and would mangle the Chinese output."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    """Print what the environment resolved to, without printing any secret."""
    force_utf8_stdout()
    load_settings()
    if _env_path is not None:
        print(f"配置文件：{_env_path}")
    else:
        print(f"没找到 {DEFAULT_ENV_FILE}（可以用 {ENV_FILE_VAR} 指定路径），只读进程环境变量")
    for name, description in described():
        print(f"  {name}={description}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
