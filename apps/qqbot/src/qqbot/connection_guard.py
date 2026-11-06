"""Recover NapCat connections with saved credentials and bounded retries."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import napcat
from .settings import load_settings

STATE_PATH = Path("runtime/private/napcat_connection.json")
LOCK_PATH = STATE_PATH.with_suffix(".lock")
AUTH_ERRORS = ("登录已失效", "登录凭证", "重新登录", "新设备", "安全验证", "被冻结", "被盗", "异地登录", "密码错误")


class WebAuthenticationExpired(RuntimeError):
    pass


def network_ready():
    try:
        with socket.create_connection(("www.qq.com", 443), timeout=3):
            return True
    except OSError:
        return False


class NapCatControl:
    """Only the configured local NapCat WebUI can restart its own worker."""

    def __init__(self, directory, endpoint, token, opener=urllib.request.urlopen):
        host, port = napcat.webui_address(directory)
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("自动恢复仅使用本机 NapCat WebUI")
        self.base = f"http://{'[' + host + ']' if ':' in host else host}:{port}"
        self.endpoint, self.token, self.opener = endpoint.rstrip("/"), token, opener
        self.web_token = str(napcat.read_config(directory / "config" / "webui.json").get("token") or "")
        self.credential = ""

    def _post(self, url, body, token=""):
        request = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
            "Content-Type": "application/json", "Authorization": "Bearer " + token})
        try:
            with self.opener(request, timeout=10) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise WebAuthenticationExpired("NapCat WebUI 认证已过期") from exc
            raise RuntimeError("NapCat 接口操作失败") from exc
        except OSError as exc:
            raise RuntimeError("NapCat 接口暂时无法连接") from exc

    def web_call(self, action, body=None):
        for attempt in range(2):
            if not self.credential:
                auth = self._post(self.base + "/api/auth/login", {
                    "hash": hashlib.sha256((self.web_token + ".napcat").encode()).hexdigest()})
                self.credential = str((auth.get("data") or {}).get("Credential") or "")
                if not self.credential:
                    raise RuntimeError("NapCat WebUI 认证失败")
            try:
                response = self._post(self.base + action, body or {}, self.credential)
            except WebAuthenticationExpired:
                self.credential = ""
                if attempt == 0:
                    continue
                raise
            if response.get("code") == 0:
                return response.get("data")
            # NapCat answers an expired credential with HTTP 200 and code -1 "Unauthorized".
            expired = response.get("code") in {401, -100} or (
                response.get("code") == -1 and "unauthorized" in str(response.get("message") or "").lower())
            if expired and attempt == 0:
                self.credential = ""
                continue
            # Responses can contain private login URLs. Never record raw payloads.
            message = str(response.get("message") or response.get("msg") or "")
            if any(word in message for word in AUTH_ERRORS):
                raise PermissionError("QQ 要求重新认证，缓存登录未通过")
            raise RuntimeError("NapCat WebUI 操作失败")
        raise RuntimeError("NapCat WebUI 认证失败")

    def status(self):
        data = self.web_call("/api/QQLogin/CheckLoginStatus")
        if not isinstance(data, dict):
            raise RuntimeError("NapCat 登录状态格式无效")
        if data.get("isLogin") or data.get("isOffline"):
            account = self.web_call("/api/QQLogin/GetQQLoginInfo")
            data["uin"] = str(account.get("uin") or "") if isinstance(account, dict) else ""
        return data

    def go_online(self):
        response = self._post(self.endpoint + "/set_online_status", {
            "status": 10, "ext_status": 0, "battery_status": 0}, self.token)
        if response.get("status") != "ok" or response.get("retcode") != 0:
            raise RuntimeError("QQ 在线状态恢复失败")

    def restart(self):
        self.web_call("/api/QQLogin/RestartNapCat")
        self.credential = ""

    def quick_login(self, uin):
        self.web_call("/api/QQLogin/SetQuickLogin", {"uin": uin})


class ConnectionGuard:
    def __init__(self, control, uin, path=STATE_PATH, clock=time.time, network=network_ready):
        if not str(uin).isdecimal():
            raise ValueError("自动恢复需要配置 NAPCAT_UIN")
        self.control, self.uin, self.path, self.clock, self.network = control, str(uin), Path(path), clock, network
        try:
            self.state = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.state = {}
        if self.state.get("account") not in {None, self.uin}:
            self.state = {}
        self.offline_seconds = max(30, int(os.environ.get("QQBOT_RECOVERY_OFFLINE_SECONDS", "90")))
        self.cooldown = max(120, int(os.environ.get("QQBOT_RECOVERY_RESTART_COOLDOWN", "300")))
        self.max_restarts = max(1, min(5, int(os.environ.get("QQBOT_RECOVERY_MAX_RESTARTS", "3"))))

    def _save(self, status, detail):
        if status == "needs_authentication":
            self.state["authentication_required"] = True
        self.state.update(status=status, detail=detail, checked_at=self.clock(), account=self.uin)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".part")
        temporary.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, self.path)
        return dict(self.state)

    def step(self):
        now = self.clock()
        try:
            status = self.control.status()
        except (OSError, RuntimeError, ValueError) as exc:
            return self._save("unreachable", str(exc))
        if status.get("uin") and str(status["uin"]) != self.uin:
            return self._save("account_mismatch", "NapCat 当前账号与配置不同，未执行恢复操作")
        if status.get("isLogin"):
            self.state.pop("offline_since", None)
            self.state.pop("online_attempted", None)
            self.state.pop("quick_attempted", None)
            self.state.pop("quick_pending_until", None)
            self.state.pop("authentication_required", None)
            self.state.pop("kick_attempted", None)
            return self._save("online", "QQ 已在线")
        if self.state.get("authentication_required"):
            return self._save("needs_authentication", "缓存登录未通过，等待账号认证；已停止自动重启")
        error = str(status.get("loginError") or "")
        kicked = any(word in error for word in AUTH_ERRORS)
        self.state.setdefault("offline_since", now)
        if now - self.state["offline_since"] < self.offline_seconds:
            return self._save("waiting", "离线确认中，等待 QQ 自行重连")
        if self.state.get("last_restart") and now - self.state["last_restart"] < 120:
            return self._save("recovering", "NapCat 正在重启，等待缓存登录")
        if now < self.state.get("quick_pending_until", 0):
            return self._save("recovering", "等待缓存登录完成")
        if kicked and self.state.get("kick_attempted"):
            return self._save("needs_authentication", "重启后 QQ 仍要求重新认证；需要扫码，已停止自动重启")
        if not self.network():
            return self._save("network_unavailable", "公网暂时不可达，等待网络恢复")
        if kicked:
            # A kick often revokes only the session, not the saved login: one restart
            # plus cache login is worth trying before asking for a QR scan.
            if self.state.get("last_restart") and now - self.state["last_restart"] < self.cooldown:
                return self._save("cooldown", "被踢下线，恢复操作冷却中")
            restarts = [ts for ts in self.state.get("restarts", []) if now - ts < 3600]
            if len(restarts) >= self.max_restarts:
                return self._save("retry_limit", "一小时内重启次数已达上限，暂停重启")
            self.state.update(kick_attempted=now, last_restart=now, restarts=[*restarts, now])
            self.state.pop("quick_attempted", None)
            self.state.pop("online_attempted", None)
            self._save("restarting", "被踢下线，重启 NapCat 尝试缓存登录")
            try:
                self.control.restart()
            except (OSError, RuntimeError) as exc:
                return self._save("restart_failed", str(exc))
            return self._save("recovering", "被踢下线，NapCat 已重启，等待缓存登录")
        if not status.get("isOffline"):
            if self.state.get("quick_attempted"):
                return self._save("needs_authentication", "缓存登录未恢复在线；需要检查 QQ 登录页")
            self.state["quick_attempted"] = now
            self._save("quick_login", "正在尝试已有账号缓存")
            try:
                self.control.quick_login(self.uin)
                self.state["quick_pending_until"] = now + 120
                return self._save("recovering", "缓存登录请求已提交，等待在线确认")
            except (OSError, RuntimeError, PermissionError) as exc:
                return self._save("needs_authentication", str(exc))
        if not self.state.get("online_attempted"):
            self.state["online_attempted"] = now
            self._save("restoring_online", "正在恢复 QQ 在线状态")
            try:
                self.control.go_online()
                return self._save("recovering", "上线请求已提交，等待在线确认")
            except (OSError, RuntimeError):
                return self._save("waiting_restart", "上线失败，下一次检查将尝试缓存重启")
        if self.state.get("last_restart") and now - self.state["last_restart"] < self.cooldown:
            return self._save("cooldown", "恢复操作冷却中")
        restarts = [ts for ts in self.state.get("restarts", []) if now - ts < 3600]
        if len(restarts) >= self.max_restarts:
            return self._save("retry_limit", "一小时内重启次数已达上限，暂停重启")
        self.state.update(last_restart=now, restarts=[*restarts, now])
        self._save("restarting", "仅重启 NapCat 机器人进程，保留账号缓存")
        try:
            self.control.restart()
        except (OSError, RuntimeError) as exc:
            return self._save("restart_failed", str(exc))
        return self._save("recovering", "NapCat 重启请求已提交，等待缓存登录")


def acquire_lock(path=LOCK_PATH):
    """An OS file lock survives stale lock files but releases when a guard exits."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+b")
    try:
        if os.fstat(stream.fileno()).st_size == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        stream.close()
        return None
    return stream


def launch_guard():
    if os.environ.get("QQBOT_AUTO_RECOVERY", "true").lower() not in {"1", "true", "yes"} or not napcat.napcat_dir():
        return None
    env = dict(os.environ)
    package_root = str(Path(__file__).resolve().parents[1])
    env["PYTHONPATH"] = package_root + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.Popen([sys.executable, "-m", "qqbot", "connection-guard"], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def main():
    load_settings()
    lock = acquire_lock()
    if lock is None:
        return 0
    directory = napcat.napcat_dir()
    if not directory:
        lock.close()
        return 1
    try:
        uin = os.environ.get("NAPCAT_UIN", "") or napcat.config_uin(napcat.find_config(directory))
        guard = ConnectionGuard(NapCatControl(directory, os.environ["ONEBOT_ENDPOINT"],
                                            os.environ.get("ONEBOT_ACCESS_TOKEN", "")), uin)
        while True:
            try:
                guard.step()
            except Exception as exc:  # noqa: BLE001 -- keep diagnostics without printing secrets
                guard._save("error", "恢复检查失败：" + type(exc).__name__)
            time.sleep(30)
    finally:
        lock.close()
