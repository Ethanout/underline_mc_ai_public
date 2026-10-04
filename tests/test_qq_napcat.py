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
    def test_console_switches_to_utf8_before_napcat(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "NapCatWinBootMain.exe").write_bytes(b"")
            with mock.patch.object(napcat, "find_qq_exe", return_value=Path("C:/QQ/QQ.exe")), \
                    mock.patch.object(napcat.subprocess, "Popen") as popen:
                napcat.launch(root, "123")
            command = popen.call_args.args[0]
            self.assertEqual(command[:6], ["cmd", "/c", "chcp", "65001", ">nul", "&&"])
            self.assertEqual(command[6], str(root.resolve() / "NapCatWinBootMain.exe"))
            self.assertEqual(command[-2:], ["-q", "123"])


if __name__ == "__main__":
    unittest.main()
