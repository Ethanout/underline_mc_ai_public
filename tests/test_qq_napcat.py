import contextlib
import io
import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from workspace_bootstrap import add_workspace_packages

add_workspace_packages()
from qqbot import napcat, settings  # noqa: E402
from qqbot.start import event_url  # noqa: E402


def napcat_config(clients=None, servers=None):
    return {
        "network": {
            "httpServers": servers if servers is not None else [
                {"name": "off", "enable": False, "host": "127.0.0.1", "port": 1, "token": "nope"},
                {"name": "api", "enable": True, "host": "0.0.0.0", "port": 3001, "token": "api-token"},
            ],
            "httpClients": clients if clients is not None else [],
            "websocketServers": [],
        },
        "musicSignUrl": "",
    }


def write_napcat(directory, config, uin="123"):
    path = Path(directory) / "config" / f"onebot11_{uin}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


class FindConfigTests(unittest.TestCase):
    def test_single_account_is_found_without_uin(self):
        with TemporaryDirectory() as directory:
            path = write_napcat(directory, napcat_config())
            self.assertEqual(napcat.find_config(Path(directory)), path)
            self.assertEqual(napcat.config_uin(path), "123")

    def test_several_accounts_need_uin(self):
        with TemporaryDirectory() as directory:
            write_napcat(directory, napcat_config(), "1")
            second = write_napcat(directory, napcat_config(), "2")
            with self.assertRaises(ValueError):
                napcat.find_config(Path(directory))
            self.assertEqual(napcat.find_config(Path(directory), "2"), second)
            with self.assertRaises(FileNotFoundError):
                napcat.find_config(Path(directory), "3")

    def test_api_server_uses_first_enabled_and_loopback(self):
        server = napcat.api_server(napcat_config())
        self.assertEqual(server, napcat.OneBotServer("http://127.0.0.1:3001", "api-token"))
        self.assertIsNone(napcat.api_server(napcat_config(servers=[])))


class SyncTests(unittest.TestCase):
    def test_sync_adds_client_then_is_idempotent(self):
        with TemporaryDirectory() as directory:
            path = write_napcat(directory, napcat_config())
            url = event_url("127.0.0.1", 18787)
            self.assertTrue(napcat.sync(path, url, "evt"))
            self.assertTrue(path.with_suffix(".json.bak").is_file())
            client = json.loads(path.read_text(encoding="utf-8"))["network"]["httpClients"][0]
            self.assertEqual(client["url"], "http://127.0.0.1:18787/api/onebot/event")
            self.assertEqual(client["token"], "evt")
            self.assertEqual(client["messagePostFormat"], "array")
            self.assertFalse(napcat.sync(path, url, "evt"))

    def test_sync_updates_in_place_and_keeps_other_entries(self):
        with TemporaryDirectory() as directory:
            other = {"name": "someone-else", "enable": True, "url": "http://x"}
            old = {"name": napcat.CLIENT_NAME, "enable": False, "url": "http://127.0.0.1:8787/api/onebot/event", "token": "old", "debug": True}
            path = write_napcat(directory, napcat_config(clients=[other, old]))
            self.assertTrue(napcat.sync(path, event_url("0.0.0.0", 18787), "new"))
            saved = json.loads(path.read_text(encoding="utf-8"))
            clients = saved["network"]["httpClients"]
            self.assertEqual(clients[0], other)
            self.assertEqual(len(clients), 2)
            self.assertEqual(clients[1]["url"], "http://127.0.0.1:18787/api/onebot/event")
            self.assertTrue(clients[1]["enable"])
            self.assertTrue(clients[1]["debug"])
            self.assertEqual(saved["musicSignUrl"], "")


class MaiBotWebSocketTests(unittest.TestCase):
    def test_ws_server_is_added_on_loopback_and_kept_alongside_others(self):
        with TemporaryDirectory() as directory:
            config = napcat_config()
            other = {"name": "someone-else", "enable": True, "host": "0.0.0.0", "port": 9}
            config["network"]["websocketServers"] = [other]
            path = write_napcat(directory, config)
            self.assertTrue(napcat.sync_ws_server(path, 3001, "ws"))
            saved = json.loads(path.read_text(encoding="utf-8"))
            servers = saved["network"]["websocketServers"]
            self.assertEqual(servers[0], other)
            self.assertEqual(servers[1]["name"], napcat.WS_SERVER_NAME)
            self.assertEqual(servers[1]["host"], "127.0.0.1")
            self.assertEqual(servers[1]["port"], 3001)
            self.assertEqual(servers[1]["token"], "ws")
            self.assertEqual(servers[1]["messagePostFormat"], "array")
            self.assertTrue(path.with_suffix(".json.bak").is_file())
            # The push client to our service is untouched.
            self.assertEqual(saved["network"]["httpServers"], napcat_config()["network"]["httpServers"])
            self.assertFalse(napcat.sync_ws_server(path, 3001, "ws"))
            self.assertTrue(napcat.sync_ws_server(path, 3002, "ws"))

    def test_start_opens_ws_only_when_maibot_is_configured(self):
        from qqbot import start

        with TemporaryDirectory() as directory:
            path = write_napcat(directory, napcat_config())
            token_file = Path(directory) / "ws.txt"
            env = {"MAIBOT_NAPCAT_WS_PORT": "3005"}
            with mock.patch.dict(os.environ, env), \
                    mock.patch.object(napcat, "DEFAULT_WS_TOKEN_FILE", str(token_file)), \
                    mock.patch("builtins.print") as printed:
                self.assertTrue(start.sync_maibot_ws(path))
            server = json.loads(path.read_text(encoding="utf-8"))["network"]["websocketServers"][0]
            self.assertEqual(server["port"], 3005)
            token = token_file.read_text(encoding="utf-8").strip()
            self.assertEqual(server["token"], token)
            self.assertNotIn(token, str(printed.call_args_list))
            with mock.patch.dict(os.environ, {"MAIBOT_NAPCAT_WS_PORT": "x"}):
                with self.assertRaises(ValueError):
                    start.maibot_ws_port()


class MaiBotLaunchTests(unittest.TestCase):
    def test_launch_uses_maibot_venv_in_its_own_folder(self):
        from qqbot import maibot

        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bot.py").write_text("", encoding="utf-8")
            (root / ".venv" / "Scripts").mkdir(parents=True)
            (root / ".venv" / "Scripts" / "python.exe").write_bytes(b"")
            with mock.patch.object(maibot.subprocess, "Popen") as popen:
                maibot.launch(root)
            command = popen.call_args.args[0]
            self.assertEqual(command[:6], ["cmd", "/c", "chcp", "65001", ">nul", "&&"])
            self.assertEqual(command[6:8], [str(root.resolve() / ".venv" / "Scripts" / "python.exe"), "bot.py"])
            self.assertEqual(popen.call_args.kwargs["cwd"], root.resolve())

    def test_missing_bot_py_is_reported(self):
        from qqbot import maibot

        with TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                maibot.launch_command(Path(directory))

    def test_start_skips_when_running_or_unset(self):
        from qqbot import maibot, start

        with TemporaryDirectory() as directory,                 mock.patch.object(maibot, "launch") as launch,                 mock.patch("builtins.print"):
            with mock.patch.dict(os.environ, {}, clear=True):
                start.start_maibot()
            launch.assert_not_called()
            with mock.patch.dict(os.environ, {"MAIBOT_DIR": directory}),                     mock.patch.object(start, "port_answers", return_value=True):
                start.start_maibot()
            launch.assert_not_called()
            with mock.patch.dict(os.environ, {"MAIBOT_DIR": directory}),                     mock.patch.object(start, "port_answers", return_value=False):
                start.start_maibot()
            launch.assert_called_once_with(Path(directory))


class PluginTokenTests(unittest.TestCase):
    def test_plugin_token_only_exists_once_maibot_is_configured(self):
        with TemporaryDirectory() as directory:
            token_file = Path(directory) / "plugin.txt"
            with mock.patch.dict(os.environ, {"QQBOT_PLUGIN_TOKEN_FILE": str(token_file)}, clear=True):
                self.assertEqual(settings._apply_plugin_token(), {})
                self.assertFalse(token_file.exists())
                os.environ["MAIBOT_DIR"] = directory
                self.assertEqual(settings._apply_plugin_token(), {"QQBOT_PLUGIN_TOKEN": str(token_file)})
                self.assertEqual(os.environ["QQBOT_PLUGIN_TOKEN"], token_file.read_text(encoding="utf-8").strip())

    def test_missing_generated_token_file_is_not_reported_but_missing_key_is(self):
        with TemporaryDirectory() as directory:
            env = {
                "QQBOT_PLUGIN_TOKEN_FILE": str(Path(directory) / "plugin.txt"),
                "DEEPSEEK_KEY_FILE": str(Path(directory) / "deepseek.txt"),
            }
            err = io.StringIO()
            with mock.patch.dict(os.environ, env, clear=True), contextlib.redirect_stderr(err):
                self.assertEqual(settings._apply_key_files(), {})
            self.assertNotIn("QQBOT_PLUGIN_TOKEN_FILE", err.getvalue())
            self.assertIn("DEEPSEEK_KEY_FILE", err.getvalue())


class EventTokenTests(unittest.TestCase):
    def test_token_is_generated_once(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "api" / "event.txt"
            first = napcat.ensure_event_token(path)
            self.assertGreaterEqual(len(first), 32)
            self.assertEqual(napcat.ensure_event_token(path), first)


class QQExeTests(unittest.TestCase):
    def test_override_wins_and_must_exist(self):
        with TemporaryDirectory() as directory:
            exe = Path(directory) / "QQ.exe"
            exe.write_bytes(b"")
            with mock.patch.dict(os.environ, {"NAPCAT_QQ_PATH": str(exe)}):
                self.assertEqual(napcat.find_qq_exe(), exe)
            with mock.patch.dict(os.environ, {"NAPCAT_QQ_PATH": str(exe) + ".missing"}):
                with self.assertRaises(FileNotFoundError):
                    napcat.find_qq_exe()

    def test_falls_back_to_install_folders_without_registry(self):
        with TemporaryDirectory() as directory:
            exe = Path(directory) / "QQ.exe"
            exe.write_bytes(b"")
            with mock.patch.dict(os.environ, {"NAPCAT_QQ_PATH": ""}),                     mock.patch.object(napcat, "_registry_qq_exe", return_value=None),                     mock.patch.object(napcat, "QQ_EXE_CANDIDATES", ("Z:/nope/QQ.exe", str(exe))):
                self.assertEqual(napcat.find_qq_exe(), exe)


class SettingsTests(unittest.TestCase):
    def test_napcat_dir_fills_endpoint_and_tokens(self):
        with TemporaryDirectory() as directory:
            write_napcat(directory, napcat_config())
            token_file = Path(directory) / "event.txt"
            env = {"NAPCAT_DIR": directory, "QQBOT_EVENT_TOKEN_FILE": str(token_file)}
            with mock.patch.dict(os.environ, env, clear=True):
                sources = settings._apply_napcat()
                self.assertEqual(os.environ["ONEBOT_ENDPOINT"], "http://127.0.0.1:3001")
                self.assertEqual(os.environ["ONEBOT_ACCESS_TOKEN"], "api-token")
                self.assertEqual(os.environ["QQBOT_EVENT_TOKEN"], token_file.read_text(encoding="utf-8").strip())
                self.assertEqual(set(sources), {"ONEBOT_ENDPOINT", "ONEBOT_ACCESS_TOKEN", "QQBOT_EVENT_TOKEN"})

    def test_explicit_values_win(self):
        with TemporaryDirectory() as directory:
            write_napcat(directory, napcat_config())
            env = {"NAPCAT_DIR": directory, "ONEBOT_ACCESS_TOKEN": "mine", "QQBOT_EVENT_TOKEN": "evt"}
            with mock.patch.dict(os.environ, env, clear=True):
                settings._apply_napcat()
                self.assertEqual(os.environ["ONEBOT_ACCESS_TOKEN"], "mine")
                self.assertEqual(os.environ["QQBOT_EVENT_TOKEN"], "evt")

    def test_without_napcat_dir_nothing_happens(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(settings._apply_napcat(), {})
            self.assertNotIn("ONEBOT_ENDPOINT", os.environ)


class LaunchTests(unittest.TestCase):
    def test_remember_login_preserves_original_and_is_idempotent(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "napcat.mjs"
            original = 'async function login(s) {\n  s.initConfig({machineId: "", commonPath: "data", externalVersion: !1});\n}\n'
            path.write_text(original, encoding="utf-8")
            self.assertTrue(napcat.enable_login_persistence(root))
            self.assertIn("s.setRemerberPwd(true);", path.read_text(encoding="utf-8"))
            self.assertEqual(path.with_suffix(".mjs.before-remember-login.bak").read_text(encoding="utf-8"), original)
            self.assertFalse(napcat.enable_login_persistence(root))

    def test_unknown_initializer_is_reported_without_changing_vendor_file(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "napcat.mjs"
            path.write_text("unexpected initializer", encoding="utf-8")
            with self.assertRaises(ValueError):
                napcat.enable_login_persistence(root)
            self.assertEqual(path.read_text(encoding="utf-8"), "unexpected initializer")

    def test_console_switches_to_utf8_before_napcat(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "NapCatWinBootMain.exe").write_bytes(b"")
            with mock.patch.object(napcat, "find_qq_exe", return_value=Path("C:/QQ/QQ.exe")), \
                    mock.patch.object(napcat, "enable_login_persistence") as remember_login, \
                    mock.patch.object(napcat.subprocess, "Popen") as popen:
                napcat.launch(root, "123")
            remember_login.assert_called_once_with(root.resolve())
            command = popen.call_args.args[0]
            self.assertEqual(command[:6], ["cmd", "/c", "chcp", "65001", ">nul", "&&"])
            self.assertEqual(command[6], str(root.resolve() / "NapCatWinBootMain.exe"))
            self.assertEqual(command[-2:], ["-q", "123"])


if __name__ == "__main__":
    unittest.main()
