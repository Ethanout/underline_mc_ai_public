"""``python -m qqbot start`` -- sync NapCat, start the web service, then NapCat.

The order matters.  NapCat pushes every group message to the web service the
moment it logs in; if the web side is not listening yet those pushes fail.  So
the web server comes up first, and NapCat is launched only once uvicorn reports
it is serving.  If NapCat is already running (its API port answers) it is left
alone -- but if this run changed its config, NapCat has to be restarted to see
the change, and that is said plainly rather than killed for you: NapCat shares
the QQ install with the desktop QQ, and killing the wrong process logs you out.
"""
from __future__ import annotations

import argparse
import os
import socket
import threading
import time
from urllib.parse import urlparse

from . import napcat
from .settings import force_utf8_stdout, load_settings


def port_answers(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def bind_error(host: str, port: int) -> OSError | None:
    """Try the bind uvicorn is about to do, so the failure comes with advice."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
        except OSError as exc:
            return exc
    return None


def our_web_running(host: str, port: int) -> bool:
    """Is the port held by a qqbot web (its /api/health answers), not a stranger?"""
    import json
    import urllib.request

    if host in ("0.0.0.0", "::", ""):
        host = "127.0.0.1"
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/api/health", timeout=1) as response:
            return json.loads(response.read()).get("status") == "ok"
    except Exception:  # noqa: BLE001 - anything else means "not ours"
        return False


def event_url(host: str, port: int) -> str:
    if host in ("0.0.0.0", "::", ""):
        host = "127.0.0.1"
    return f"http://{host}:{port}/api/onebot/event"


def sync_napcat() -> tuple[bool, str]:
    """Point NapCat at this web service.  Returns ``(changed, uin)``."""
    from .web import web_host, web_port

    directory = napcat.napcat_dir()
    path = napcat.find_config(directory, os.environ.get("NAPCAT_UIN", "").strip())
    token = os.environ.get("QQBOT_EVENT_TOKEN", "").strip()
    if not token:
        raise ValueError("事件 token 没准备好，看上面 settings 的报错")
    changed = napcat.sync(path, event_url(web_host(), web_port()), token)
    if os.environ.get("MAIBOT_DIR", "").strip():
        changed = sync_maibot_ws(path) or changed
    print(f"NapCat 配置：{path}（{'已更新，旧的备份成 .bak' if changed else '无需改动'}）")
    return changed, napcat.config_uin(path)


def maibot_ws_port() -> int:
    raw = os.environ.get("MAIBOT_NAPCAT_WS_PORT", "").strip()
    try:
        return int(raw) if raw else napcat.DEFAULT_WS_PORT
    except ValueError as exc:
        raise ValueError(f"MAIBOT_NAPCAT_WS_PORT 不是端口号：{raw}") from exc


def sync_maibot_ws(path) -> bool:
    """Open the loopback WebSocket MaiBot's NapCat adapter connects to.

    MaiBot itself is not started from here: it has its own launcher and its
    own EULA prompt.  The token stays in its file; only the path is printed.
    """
    port = maibot_ws_port()
    token = napcat.ensure_event_token(napcat.DEFAULT_WS_TOKEN_FILE)
    changed = napcat.sync_ws_server(path, port, token)
    print(
        f"MaiBot 连接：NapCat 正向 WebSocket 127.0.0.1:{port}，"
        f"token 在 {napcat.DEFAULT_WS_TOKEN_FILE}（填进 MaiBot NapCat 适配器的 [napcat_server]）"
    )
    return changed


def main(argv: list[str] | None = None) -> int:
    force_utf8_stdout()
    parser = argparse.ArgumentParser(prog="python -m qqbot start", description="一键启动：同步 NapCat 配置，先起 web，再起 NapCat")
    parser.add_argument("--no-napcat", action="store_true", help="只起 web，不启动 NapCat")
    args = parser.parse_args(argv)

    load_settings()
    from .web import app, onebot_endpoint, web_host, web_port

    host, port = web_host(), web_port()
    web_already = False
    error = bind_error(host, port)
    if error is not None and our_web_running(host, port):
        web_already = True
        print(f"web 已经在 {host}:{port} 跑着，这次只管 NapCat。改过代码的话先关掉那个 web 窗口再启动。")
    elif error is not None:
        print(f"端口 {host}:{port} 用不了：{error}")
        print("  可能已经有一个 web 在跑；或者端口落在 Windows 保留区间里（WinError 10013）。")
        print("  查保留区间：netsh int ipv4 show excludedportrange protocol=tcp")
        print("  换端口只改 .env 里的 QQBOT_WEB_PORT，再跑一次本命令，NapCat 那边会自动跟着改。")
        return 1

    directory = napcat.napcat_dir()
    launch_napcat = not args.no_napcat and directory is not None
    uin = os.environ.get("NAPCAT_UIN", "").strip()
    if directory is None:
        print("没设 NAPCAT_DIR：只起 web，NapCat 的配置和启动要自己管。")
    else:
        try:
            changed, uin = sync_napcat()
        except (OSError, ValueError) as exc:
            print(f"同步 NapCat 配置失败：{exc}")
            return 1
        api = urlparse(onebot_endpoint())
        if port_answers(api.hostname or "127.0.0.1", api.port or 80):
            launch_napcat = False
            if changed:
                print("NapCat 已经在跑，但配置刚改过：关掉 NapCat 窗口再跑一次本命令，新配置才生效。")
            else:
                print("NapCat 已经在跑，不再重复启动。")

    if web_already:
        if launch_napcat:
            try:
                napcat.launch(directory, uin)
            except OSError as exc:
                print(f"NapCat 启动失败：{exc}")
                return 1
            print(f"NapCat 已在新窗口启动{'（快速登录 ' + uin + '）' if uin else ''}。")
        return 0

    import uvicorn

    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port))

    def launch_when_ready() -> None:
        while not server.started:
            if server.should_exit:
                return
            time.sleep(0.2)
        try:
            napcat.launch(directory, uin)
        except OSError as exc:
            print(f"NapCat 启动失败：{exc}")
            return
        print(f"NapCat 已在新窗口启动{'（快速登录 ' + uin + '）' if uin else ''}；首次登录要在那个窗口扫码。")

    if launch_napcat:
        threading.Thread(target=launch_when_ready, name="napcat-launcher", daemon=True).start()
    print(f"WebUI：http://{'127.0.0.1' if host in ('0.0.0.0', '::') else host}:{port}")
    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
