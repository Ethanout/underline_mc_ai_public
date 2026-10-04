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

MaiBot's NapCat adapter connects to a forward WebSocket server instead;
:func:`sync_ws_server` adds one, with its own generated token, so the adapter
and this service can share one NapCat login without either touching the other.

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
WS_SERVER_NAME = "maibot"
DEFAULT_EVENT_TOKEN_FILE = "config/api/qqbot_event.txt"
DEFAULT_WS_TOKEN_FILE = "config/api/maibot_napcat_ws.txt"
DEFAULT_WS_PORT = 3001


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
    """Return the token kept in ``path``, generating and saving one the first time."""
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


def _write(path: Path, config: dict[str, Any]) -> None:
    shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(partial, path)


def _upsert(config: dict[str, Any], kind: str, name: str, wanted) -> bool:
    entries = config.setdefault("network", {}).setdefault(kind, [])
    index = next((i for i, item in enumerate(entries) if item.get("name") == name), None)
    current = entries[index] if index is not None else None
    value = wanted(current)
    if current == value:
        return False
    if index is None:
        entries.append(value)
    else:
        entries[index] = value
    return True


def sync(path: Path, url: str, token: str) -> bool:
    """Point NapCat's push client at ``url`` with ``token``.  True if changed."""
    config = read_config(path)
    changed = _upsert(config, "httpClients", CLIENT_NAME, lambda c: desired_client(url, token, c))
    if changed:
        _write(path, config)
    return changed


def desired_ws_server(
    port: int, token: str, existing: dict[str, Any] | None = None
) -> dict[str, Any]:
    server = dict(existing or {})
    server.update(
        {
            "enable": True,
            "name": WS_SERVER_NAME,
            "host": "127.0.0.1",
            "port": int(port),
            "messagePostFormat": "array",
            "reportSelfMessage": False,
            "token": token,
        }
    )
    server.setdefault("enableForcePushEvent", True)
    server.setdefault("debug", False)
    server.setdefault("heartInterval", 30000)
    return server


def sync_ws_server(path: Path, port: int, token: str) -> bool:
    """Ensure the loopback WebSocket server MaiBot's adapter dials.  True if changed."""
    config = read_config(path)
    changed = _upsert(
        config, "websocketServers", WS_SERVER_NAME, lambda c: desired_ws_server(port, token, c)
    )
    if changed:
        _write(path, config)
    return changed


QQ_EXE_CANDIDATES = (
    r"C:\Program Files\Tencent\QQNT\QQ.exe",
    r"C:\Program Files (x86)\Tencent\QQNT\QQ.exe",
    r"D:\Program Files\Tencent\QQNT\QQ.exe",
)


def _registry_qq_exe() -> Path | None:
    """Where NapCat's own .bat looks: the ``Uninstall\\QQ`` key's UninstallString."""
    try:
        import winreg
    except ImportError:
        return None
    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\QQ"
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
            try:
                with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ | view) as key:
                    uninstall, _ = winreg.QueryValueEx(key, "UninstallString")
            except OSError:
                continue
            candidate = Path(str(uninstall).strip('"')).parent / "QQ.exe"
            if candidate.is_file():
                return candidate
    return None


def find_qq_exe() -> Path:
    """``NAPCAT_QQ_PATH``, else the registry, else the usual install folders.

    NapCat's bundled launcher only tries the registry, and some QQNT installs
    never write that key -- then it dies with "provided QQ path is invalid".
    """
    override = os.environ.get("NAPCAT_QQ_PATH", "").strip()
    if override:
        path = Path(override).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"NAPCAT_QQ_PATH 指向的 {path} 不存在")
        return path
    found = _registry_qq_exe()
    if found is not None:
        return found
    for candidate in QQ_EXE_CANDIDATES:
        if Path(candidate).is_file():
            return Path(candidate)
    raise FileNotFoundError("找不到 QQ.exe，在 .env 里用 NAPCAT_QQ_PATH 指定")


def launch(directory: Path, uin: str = "") -> subprocess.Popen:
    """Start NapCat in its own console window.  ``uin`` enables quick login.

    Does what ``launcher-user.bat`` does, minus its registry-only QQ lookup:
    set the NAPCAT_* paths, write ``loadNapCat.js``, run the boot exe on QQ.
    """
    directory = directory.resolve()
    boot = directory / "NapCatWinBootMain.exe"
    if not boot.is_file():
        raise FileNotFoundError(f"没找到 {boot}，NAPCAT_DIR 是 NapCat.Shell 的目录吗？")
    qq = find_qq_exe()
    main_path = (directory / "napcat.mjs").as_posix()
    load_path = directory / "loadNapCat.js"
    load_path.write_text(f'(async () => {{await import("file:///{main_path}")}})()\n', encoding="utf-8")
    env = dict(os.environ)
    env.update(
        {
            "NAPCAT_PATCH_PACKAGE": str(directory / "qqnt.json"),
            "NAPCAT_LOAD_PATH": str(load_path),
            "NAPCAT_INJECT_PATH": str(directory / "NapCatWinBootHook.dll"),
            "NAPCAT_LAUNCHER_PATH": str(boot),
            "NAPCAT_MAIN_PATH": main_path,
        }
    )
    command = [str(boot), str(qq), str(directory / "NapCatWinBootHook.dll")]
    if uin:
        # Quick login needs this QQ to have logged in to the account once
        # before; otherwise NapCat falls back to the QR code by itself.
        command += ["-q", uin]
        env["NAPCAT_QUICK_ACCOUNT"] = uin
    # NapCat logs UTF-8; a fresh console starts on the ANSI code page (GBK on a
    # Chinese Windows) and shows mojibake.  The bat ran ``chcp 65001`` first.
    command = ["cmd", "/c", "chcp", "65001", ">nul", "&&", *command]
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    return subprocess.Popen(command, cwd=directory, env=env, creationflags=flags)
