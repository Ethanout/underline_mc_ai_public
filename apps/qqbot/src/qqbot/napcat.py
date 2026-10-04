"""Keep NapCat's OneBot config in step with ``.env``, so each value is set once.

Without this, three values had to be typed twice and kept in sync by hand: the
web port (in ``.env`` and in NapCat's push URL), the event token (in a key file
and in NapCat's ``httpClients``), and the OneBot API token (in NapCat's
``httpServers`` and in ``ONEBOT_ACCESS_TOKEN``).  Get one wrong and the symptom
is a bare 401 or a refused connection, far from the cause.

Now NapCat's config is the source for the API side -- endpoint and token are
read from its ``httpServers`` entry -- and ``.env`` is the source for the push
side, which :func:`sync` writes into ``httpClients``.  The event token is
generated on first use and kept in ``config/api/`` (gitignored).

Nothing here prints a token.  The NapCat file is backed up before each write.
"""
from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CLIENT_NAME = "tantan"
DEFAULT_EVENT_TOKEN_FILE = "config/api/qqbot_event.txt"
DEFAULT_LAUNCHER = "launcher-user.bat"


@dataclass(frozen=True)
class OneBotServer:
    endpoint: str
    token: str


def napcat_dir() -> Path | None:
    raw = os.environ.get("NAPCAT_DIR", "").strip()
    return Path(raw).expanduser() if raw else None


def find_config(directory: Path, uin: str = "") -> Path:
    """Return NapCat's ``onebot11_<uin>.json``; ``uin`` picks one of several."""
    config_dir = directory / "config"
    if uin:
        candidate = config_dir / f"onebot11_{uin}.json"
        if not candidate.is_file():
            raise FileNotFoundError(f"没找到 {candidate}，NAPCAT_UIN 填对了吗？")
        return candidate
    found = sorted(config_dir.glob("onebot11_*.json"))
    if not found:
        raise FileNotFoundError(f"{config_dir} 里没有 onebot11_*.json，先用 NapCat 登录一次机器人账号")
    if len(found) > 1:
        names = ", ".join(path.stem.removeprefix("onebot11_") for path in found)
        raise ValueError(f"NapCat 里有多个账号（{names}），在 .env 里用 NAPCAT_UIN 指定一个")
    return found[0]


def config_uin(path: Path) -> str:
    return path.stem.removeprefix("onebot11_")


def read_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def api_server(config: dict[str, Any]) -> OneBotServer | None:
    """The first enabled ``httpServers`` entry, as an endpoint plus its token."""
    for server in config.get("network", {}).get("httpServers", []):
        if not server.get("enable"):
            continue
        host = str(server.get("host") or "127.0.0.1")
        if host in ("0.0.0.0", "::", ""):
            host = "127.0.0.1"
        return OneBotServer(f"http://{host}:{int(server.get('port', 3000))}", str(server.get("token") or ""))
    return None


def ensure_event_token(path: str | Path = DEFAULT_EVENT_TOKEN_FILE) -> str:
    """Return the event token, generating and saving one the first time."""
    token_file = Path(path)
    if token_file.is_file():
        token = token_file.read_text(encoding="utf-8").strip()
        if token:
            return token
    token = secrets.token_urlsafe(32)
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(token + "\n", encoding="utf-8")
    return token


def desired_client(url: str, token: str, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    client = dict(existing or {})
    client.update(
        {
            "enable": True,
            "name": CLIENT_NAME,
            "url": url,
            "reportSelfMessage": False,
            "messagePostFormat": "array",
            "token": token,
        }
    )
    client.setdefault("debug", False)
    return client


def sync(path: Path, url: str, token: str) -> bool:
    """Point NapCat's push client at ``url`` with ``token``.  True if changed."""
    config = read_config(path)
    network = config.setdefault("network", {})
    clients = network.setdefault("httpClients", [])
    index = next((i for i, item in enumerate(clients) if item.get("name") == CLIENT_NAME), None)
    current = clients[index] if index is not None else None
    wanted = desired_client(url, token, current)
    if current == wanted:
        return False
    if index is None:
        clients.append(wanted)
    else:
        clients[index] = wanted
    shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(partial, path)
    return True


def launch(directory: Path, uin: str = "", launcher: str = "") -> subprocess.Popen:
    """Start NapCat in its own console window.  ``uin`` enables quick login."""
    script = directory / (launcher or os.environ.get("NAPCAT_LAUNCHER", "") or DEFAULT_LAUNCHER)
    if not script.is_file():
        raise FileNotFoundError(f"没找到 NapCat 启动脚本 {script}")
    command = ["cmd", "/c", str(script)]
    if uin:
        command += ["-q", uin]
    # The launcher resolves its own files from %cd%, so cwd must be its folder.
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    return subprocess.Popen(command, cwd=directory, creationflags=flags)
