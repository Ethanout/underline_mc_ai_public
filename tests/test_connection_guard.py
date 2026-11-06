"""Connection recovery does not clear credentials, send messages, or loop on auth failures."""
# ruff: noqa: E402 -- add workspace packages before imports.

import io
import json
import unittest
import urllib.error
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from workspace_bootstrap import add_workspace_packages

add_workspace_packages()
from qqbot.connection_guard import ConnectionGuard, NapCatControl, acquire_lock


class FakeControl:
    def __init__(self):
        self.result = {"isLogin": False, "isOffline": True, "loginError": "二维码已过期，请刷新", "uin": "123"}
        self.actions = []
        self.error = None
        self.quick_error = None

    def status(self):
        if self.error:
            raise self.error
        return dict(self.result)

    def go_online(self):
        self.actions.append("online")
        raise RuntimeError("QQ 在线状态恢复失败")

    def restart(self):
        self.actions.append("restart")

    def quick_login(self, uin):
        self.actions.append("quick:" + uin)
        if self.quick_error:
            raise self.quick_error


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "state.json"
        self.now = 10000
        self.control = FakeControl()
        self.connected = True
        self.guard = ConnectionGuard(self.control, "123", self.path, lambda: self.now, lambda: self.connected)

    def tearDown(self):
        self.temp.cleanup()

    def advance(self, seconds):
        self.now += seconds
        return self.guard.step()

    def test_wait_online_attempt_restart_and_confirm_online(self):
        self.assertEqual(self.guard.step()["status"], "waiting")
        self.assertEqual(self.advance(90)["status"], "waiting_restart")
        self.assertEqual(self.advance(30)["status"], "recovering")
        self.assertEqual(self.control.actions, ["online", "restart"])
        self.control.result["isLogin"] = True
        self.assertEqual(self.advance(30)["status"], "online")
        self.assertNotIn("offline_since", self.guard.state)

    def test_no_restart_while_internet_is_down(self):
        self.connected = False
        self.guard.step()
        self.assertEqual(self.advance(90)["status"], "network_unavailable")
        self.assertEqual(self.control.actions, [])
        self.connected = True
        self.assertEqual(self.advance(30)["status"], "waiting_restart")

    def test_kick_restarts_once_then_waits_for_scan(self):
        self.control.result["loginError"] = "你的账号当前登录已失效，请重新登录"
        self.assertEqual(self.guard.step()["status"], "waiting")
        self.assertEqual(self.advance(90)["status"], "recovering")
        self.assertEqual(self.control.actions, ["restart"])
        # Fresh worker: no stale error, not logged in -> one cache login attempt.
        self.control.result.update(isOffline=False, loginError="")
        self.assertEqual(self.advance(30)["status"], "recovering")
        self.assertEqual(self.advance(100)["status"], "recovering")
        self.assertEqual(self.control.actions, ["restart", "quick:123"])
        self.control.result["loginError"] = "你的账号当前登录已失效，请重新登录"
        self.assertEqual(self.advance(130)["status"], "needs_authentication")
        self.control.error = RuntimeError("offline")
        self.assertEqual(self.advance(30)["status"], "unreachable")
        self.control.error = None
        self.assertEqual(self.advance(400)["status"], "needs_authentication")
        self.assertEqual(self.control.actions, ["restart", "quick:123"])
        self.control.result["isLogin"] = True
        self.assertEqual(self.advance(30)["status"], "online")
        self.assertNotIn("kick_attempted", self.guard.state)

    def test_kick_recovered_by_restart_clears_attempt(self):
        self.control.result["loginError"] = "你的账号当前登录已失效，请重新登录"
        self.guard.step()
        self.advance(90)
        self.control.result.update(isLogin=True, loginError="")
        self.assertEqual(self.advance(130)["status"], "online")
        self.assertEqual(self.control.actions, ["restart"])
        self.assertNotIn("kick_attempted", self.guard.state)

    def test_kick_still_rejected_after_restart_needs_scan(self):
        self.control.result["loginError"] = "你的账号当前登录已失效，请重新登录"
        self.guard.step()
        self.advance(90)
        self.assertEqual(self.advance(130)["status"], "needs_authentication")
        self.assertEqual(self.control.actions, ["restart"])

    def test_cache_login_attempt_wait_and_failure_latch(self):
        self.control.result["isOffline"] = False
        self.guard.step()
        self.assertEqual(self.advance(90)["status"], "recovering")
        self.assertEqual(self.advance(30)["status"], "recovering")
        self.assertEqual(self.advance(120)["status"], "needs_authentication")
        self.assertEqual(self.advance(30)["status"], "needs_authentication")
        self.assertEqual(self.control.actions, ["quick:123"])

    def test_limits_persist_across_guard_restart(self):
        self.guard.step()
        self.advance(90)
        for _ in range(3):
            self.advance(300)
        self.assertEqual(self.control.actions.count("restart"), 3)
        reloaded = ConnectionGuard(self.control, "123", self.path, lambda: self.now, lambda: True)
        self.now += 300
        self.assertEqual(reloaded.step()["status"], "retry_limit")
        self.now += 3601
        self.assertEqual(reloaded.step()["status"], "recovering")

    def test_cooldown_and_boot_grace(self):
        self.guard.step()
        self.advance(90)
        self.advance(30)
        self.assertEqual(self.advance(30)["status"], "recovering")
        self.assertEqual(self.advance(100)["status"], "cooldown")
        self.assertEqual(self.control.actions.count("restart"), 1)

    def test_other_account_is_never_restarted(self):
        self.control.result["uin"] = "456"
        self.assertEqual(self.guard.step()["status"], "account_mismatch")
        self.assertEqual(self.control.actions, [])

    def test_unreachable_webui_does_not_launch_duplicate_qq(self):
        self.control.error = RuntimeError("offline")
        self.assertEqual(self.guard.step()["status"], "unreachable")
        self.assertEqual(self.control.actions, [])

    def test_lock_is_singleton_and_released_on_close(self):
        path = Path(self.temp.name) / "lock"
        first = acquire_lock(path)
        self.assertIsNotNone(first)
        try:
            self.assertIsNone(acquire_lock(path))
        finally:
            first.close()
        second = acquire_lock(path)
        self.assertIsNotNone(second)
        second.close()


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.directory = Path(self.temp.name)
        (self.directory / "config").mkdir()
        (self.directory / "config" / "webui.json").write_text(json.dumps({"token": "private-token"}), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_http_auth_expiry_reauthenticates_without_leaking_token(self):
        calls = []
        def open_request(request, timeout):
            calls.append(request.full_url)
            if request.full_url.endswith("/login"):
                return io.BytesIO(json.dumps({"code": 0, "data": {"Credential": "private-credential"}}).encode())
            if calls.count(request.full_url) == 1:
                raise urllib.error.HTTPError(request.full_url, 401, "private", {}, None)
            return io.BytesIO(b'{"code":0,"data":{"isLogin":false,"isOffline":false}}')
        control = NapCatControl(self.directory, "http://127.0.0.1:3000", "private-api", open_request)
        self.assertFalse(control.status()["isLogin"])
        self.assertEqual(sum(url.endswith("/login") for url in calls), 2)

    def test_expired_credential_with_code_minus_one_reauthenticates(self):
        calls = []
        def open_request(request, timeout):
            calls.append(request.full_url)
            if request.full_url.endswith("/login"):
                return io.BytesIO(json.dumps({"code": 0, "data": {"Credential": "c"}}).encode())
            if calls.count(request.full_url) == 1:
                return io.BytesIO(b'{"code":-1,"message":"Unauthorized"}')
            return io.BytesIO(b'{"code":0,"data":{"isLogin":true,"isOffline":false}}')
        control = NapCatControl(self.directory, "http://127.0.0.1:3000", "private-api", open_request)
        control.credential = "stale"
        self.assertTrue(control.web_call("/api/QQLogin/CheckLoginStatus")["isLogin"])
        self.assertEqual(sum(url.endswith("/login") for url in calls), 1)

    def test_restart_uses_only_authenticated_webui_endpoint(self):
        calls = []
        def open_request(request, timeout):
            calls.append((request.full_url, dict(request.header_items())))
            payload = {"code": 0, "data": {"Credential": "credential"} if request.full_url.endswith("/login") else {}}
            return io.BytesIO(json.dumps(payload).encode())
        control = NapCatControl(self.directory, "http://127.0.0.1:3000", "private-api", open_request)
        control.restart()
        self.assertTrue(calls[-1][0].endswith("/api/QQLogin/RestartNapCat"))
        self.assertEqual(calls[-1][1]["Authorization"], "Bearer credential")
        self.assertEqual(control.credential, "")

    def test_launcher_hidden_and_no_global_process_kill(self):
        from qqbot.connection_guard import launch_guard
        with patch("qqbot.connection_guard.napcat.napcat_dir", return_value=self.directory), \
                patch("qqbot.connection_guard.subprocess.Popen") as spawn:
            launch_guard()
        self.assertEqual(spawn.call_args.args[0][-1], "connection-guard")
        self.assertIn("creationflags", spawn.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
