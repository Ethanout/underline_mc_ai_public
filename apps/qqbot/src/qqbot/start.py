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
from .settings import load_settings


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
    print(f"NapCat 配置：{path}（{'已更新，旧的备份成 .bak' if changed else '无需改动'}）")
    return changed, napcat.config_uin(path)


def main(argv: list[str] | None = None) -> int:
    from .style_memory import _force_utf8_stdout

    _force_utf8_stdout()
    parser = argparse.ArgumentParser(prog="python -m qqbot start", description="一键启动：同步 NapCat 配置，先起 web，再起 NapCat")
    parser.add_argument("--no-napcat", action="store_true", help="只起 web，不启动 NapCat")
    args = parser.parse_args(argv)

    load_settings()
    from .web import app, onebot_endpoint, web_host, web_port

    host, port = web_host(), web_port()
    error = bind_error(host, port)
    if error is not None:
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
