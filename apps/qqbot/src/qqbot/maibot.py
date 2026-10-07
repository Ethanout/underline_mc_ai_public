"""Start MaiBot from the same one-click launcher as the web service and NapCat.

MaiBot stays in its own folder (``MAIBOT_DIR``) with its own venv; this only
opens it in a new console window, the same way NapCat is opened, so one
double-click brings up all three.  Whether it is already running is judged by
its WebUI port answering, so a second click does not start a second copy.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

DEFAULT_WEBUI_PORT = 8001


def maibot_dir() -> Path | None:
    raw = os.environ.get("MAIBOT_DIR", "").strip()
    return Path(raw).expanduser() if raw else None


def webui_port() -> int:
    raw = os.environ.get("MAIBOT_WEBUI_PORT", "").strip()
    try:
        return int(raw) if raw else DEFAULT_WEBUI_PORT
    except ValueError as exc:
        raise ValueError(f"MAIBOT_WEBUI_PORT 不是端口号：{raw}") from exc


def launch_command(directory: Path) -> list[str]:
    """Prefer MaiBot's own venv; fall back to ``uv run`` when it has none."""
    if not (directory / "bot.py").is_file():
        raise FileNotFoundError(f"没找到 {directory / 'bot.py'}，MAIBOT_DIR 是麦麦的目录吗？")
    python = directory / ".venv" / "Scripts" / "python.exe"
    run = [str(python), "bot.py"] if python.is_file() else ["uv", "run", "bot.py"]
    # chcp for the UTF-8 log; pause keeps the window open if MaiBot exits with an error.
    return ["cmd", "/c", "chcp", "65001", ">nul", "&&", *run, "&", "pause"]


def launch(directory: Path) -> subprocess.Popen:
    """Open MaiBot in its own console window."""
    directory = directory.resolve()
    command = launch_command(directory)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    return subprocess.Popen(command, cwd=directory, env=env, creationflags=flags)
