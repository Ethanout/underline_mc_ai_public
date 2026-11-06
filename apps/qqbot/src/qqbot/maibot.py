"""Start MaiBot from the same one-click launcher as the web service and NapCat.

MaiBot stays in its own folder (``MAIBOT_DIR``) with its own venv; this only
opens it in a new console window, the same way NapCat is opened, so one
double-click brings up all three.  Whether it is already running is judged by
its WebUI port answering, so a second click does not start a second copy.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

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


# Domestic APIs are reachable directly; through the system proxy their
# requests sometimes stall for tens of seconds.
DIRECT_HOSTS = ("api.siliconflow.cn", "api.deepseek.com")


def no_proxy(current: str) -> str:
    """Add ``DIRECT_HOSTS`` to an existing ``NO_PROXY`` list."""
    hosts = [h.strip() for h in current.split(",") if h.strip()]
    hosts += [h for h in DIRECT_HOSTS if h not in hosts]
    return ",".join(hosts)


def launch(directory: Path) -> subprocess.Popen:
    """Open MaiBot in its own console window."""
    directory = directory.resolve()
    command = launch_command(directory)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["NO_PROXY"] = no_proxy(env.get("NO_PROXY") or env.get("no_proxy", ""))
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    return subprocess.Popen(command, cwd=directory, env=env, creationflags=flags)


def webui_request(path: str, payload=None, method="GET"):
    """Call the local MaiBot management API without exposing its session token."""
    directory = maibot_dir()
    if directory is None:
        raise ValueError("未配置 MAIBOT_DIR")
    try:
        token = json.loads((directory / "data/webui.json").read_text(encoding="utf-8"))["access_token"]
    except (OSError, ValueError, KeyError) as exc:
        raise ValueError("无法读取麦麦本地管理凭证") from exc
    request = Request(
        f"http://127.0.0.1:{webui_port()}/api/webui" + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Cookie": "maibot_session=" + token, "Content-Type": "application/json"},
        method=method,
    )
    try:
        with build_opener(ProxyHandler({})).open(request, timeout=15) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        raise ValueError(f"麦麦管理接口返回 HTTP {exc.code}") from exc
    except OSError as exc:
        raise ValueError("无法连接麦麦管理接口，请确认麦麦已启动") from exc
