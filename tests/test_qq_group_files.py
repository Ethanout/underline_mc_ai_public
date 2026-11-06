"""Group provenance, bounded downloads, permissions, and immutable Wiki imports."""
# ruff: noqa: E402 -- add workspace packages before imports.

import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from workspace_bootstrap import add_workspace_packages

add_workspace_packages()
from qqbot.group_files import GroupFiles, install_group_file_tools, safe_filename
from qqbot.store import Store
from qqbot.tools import ToolRegistry


class Download(io.BytesIO):
    headers = {}

    def geturl(self):
        return "https://files.example/test"


class GroupFileTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "db.sqlite")
        self.member = self.store.create_task("123", "member", "1")
        self.admin = self.store.create_task("123", "admin", "2")
        self.calls = []
        self.downloads = 0
        self.row = {"group_id": 123, "file_id": "file1", "file_name": "../../CON.txt",
                    "file_size": 3, "busid": 104, "uploader": 99, "upload_time": 10}
        self.content = b"abc"
        self.library = GroupFiles(self.onebot, self.root / "wiki", self.open)
        self.registry = ToolRegistry(self.store, self.onebot)
        install_group_file_tools(self.registry, self.library)
        self.env = patch.dict("os.environ", {"QQBOT_ADMIN_IDS": "admin", "QQBOT_GROUP_FILE_TRANSPORT": "url"})
        self.env.start()
        self.urls = patch("qqbot.group_files.public_url", side_effect=lambda url: url)
        self.urls.start()

    def tearDown(self):
        self.urls.stop()
        self.env.stop()
        self.store.close()
        self.temp.cleanup()

    def onebot(self, action, args):
        self.calls.append((action, args))
        if action == "get_group_root_files":
            return {"files": [self.row], "folders": [{"folder_id": "/folder", "folder_name": "资料"}]}
        if action == "get_group_files_by_folder":
            return {"files": [self.row], "folders": []}
        if action == "get_group_file_url":
            return {"url": "https://files.example/test?secret=private"}
        raise AssertionError(action)

    def open(self, request, timeout):
        self.downloads += 1
        return Download(self.content)

    def export(self, **args):
        return self.registry.execute(self.admin, "export_group_file", {"file_id": "file1", **args})

    def test_list_filter_and_pagination(self):
        first = self.registry.execute(self.member, "list_group_files", {"limit": 1})
        self.assertEqual(first["next_offset"], 1)
        self.assertEqual(first["results"][0]["folder_id"], "/folder")
        second = self.registry.execute(self.member, "list_group_files", {"offset": 1})
        self.assertEqual(second["results"][0]["file_id"], "file1")
        self.assertEqual(self.registry.execute(self.member, "list_group_files", {"keyword": "missing"})["total"], 0)

    def test_export_original_provenance_and_reuse(self):
        receipt = self.export()
        self.assertEqual(receipt["status"], "exported")
        path = Path(receipt["path"])
        self.assertTrue(path.resolve().is_relative_to(self.library.root))
        self.assertEqual(path.read_bytes(), b"abc")
        self.assertEqual(receipt["file"]["uploader"], 99)
        self.assertEqual(receipt["verification"], "原始群文件，未验证")
        self.assertNotIn("private", json.dumps(receipt))
        self.assertEqual(self.export()["status"], "already_exported")
        self.assertEqual(self.downloads, 1)
        self.assertEqual(self.calls[1][1]["busid"], 104)

    def test_member_cannot_export_or_forge_admin(self):
        self.assertIn("error", self.registry.execute(self.member, "export_group_file", {"file_id": "file1"}))
        self.assertIn("error", self.registry.execute({**self.member, "user_id": "admin"}, "export_group_file", {"file_id": "file1"}))
        self.assertEqual(self.calls, [])
        names = {tool["function"]["name"] for tool in self.registry.tools_for(self.member)}
        self.assertNotIn("export_group_file", names)

    def test_cross_group_and_unknown_file_folder_denied(self):
        self.assertIn("error", self.registry.execute(self.member, "list_group_files", {"group_id": "456"}))
        self.assertIn("error", self.export(folder_id="/other-group"))
        self.assertIn("error", self.registry.execute(self.admin, "export_group_file", {"file_id": "other"}))
        self.row["group_id"] = 456
        self.assertIn("error", self.export())
        self.assertEqual(self.downloads, 0)

    def test_valid_folder_export(self):
        self.assertEqual(self.export(folder_id="/folder")["folder_id"], "/folder")
        self.assertEqual(self.calls[1][0], "get_group_files_by_folder")

    def test_size_limit_before_and_during_download(self):
        self.library.max_bytes = 2
        self.assertIn("error", self.export())
        self.assertEqual(self.downloads, 0)
        self.row["file_size"] = 0
        self.assertIn("error", self.export())
        self.assertEqual(list(self.library.root.rglob("*.json")), [])
        self.assertFalse(any(path.is_file() for path in self.library.root.rglob("*")))

    def test_partial_download_and_modified_file_not_overwritten(self):
        self.content = b"ab"
        self.assertIn("error", self.export())
        self.content = b"abc"
        receipt = self.export()
        Path(receipt["path"]).write_bytes(b"human edit")
        self.assertIn("error", self.export())
        self.assertEqual(Path(receipt["path"]).read_bytes(), b"human edit")

    def test_new_metadata_preserves_previous_version(self):
        old = self.export()
        self.row["modify_time"] = 20
        self.content = b"xyz"
        new = self.export()
        self.assertNotEqual(old["path"], new["path"])
        self.assertEqual(Path(old["path"]).read_bytes(), b"abc")

    def test_filename_rules(self):
        self.assertEqual(safe_filename("CON.txt"), "_CON.txt")
        self.assertNotIn("/", safe_filename("../../x.txt"))

    def test_rotating_napcat_id_survives_registry_restart(self):
        library = GroupFiles(self.onebot, self.library.root, self.open, store=self.store)
        library.list_files(self.admin, {})
        self.row["file_id"] = "new-napcat-id"
        restarted = GroupFiles(self.onebot, self.library.root, self.open, store=self.store)
        first = restarted.export_file(self.admin, {"file_id": "file1"})
        self.assertEqual(first["file"]["file_id"], "new-napcat-id")
        self.row["file_id"] = "another-napcat-id"
        self.assertEqual(restarted.export_file(self.admin, {"file_id": "file1"})["status"], "already_exported")
        self.assertEqual(self.downloads, 1)

    def test_download_failure_does_not_disclose_url(self):
        def failed(*args, **kwargs):
            raise OSError("https://files.example/?secret=private")
        self.library.opener = failed
        self.assertNotIn("private", self.export()["error"])

    def test_native_download_uses_only_observed_file_id(self):
        source = self.root / "napcat-cache"
        source.write_bytes(b"abc")
        actions = []
        def native(action, args):
            actions.append(action)
            if action == "get_file":
                self.assertEqual(args, {"file_id": "file1"})
                return {"file": str(source)}
            return self.onebot(action, args)
        self.library.onebot = native
        with patch.dict("os.environ", {"QQBOT_GROUP_FILE_TRANSPORT": "native"}):
            receipt = self.export()
        self.assertEqual(Path(receipt["path"]).read_bytes(), b"abc")
        self.assertNotIn("get_group_file_url", actions)

    def test_http_list_export_audit_and_plugin_export_denial(self):
        from fastapi.testclient import TestClient
        from qqbot import web
        with patch.object(web, "event_store", self.store), patch.object(web, "_onebot", self.onebot), \
                patch.object(web, "GroupFiles", return_value=self.library), \
                patch.dict("os.environ", {"QQBOT_GROUPS": "123", "QQBOT_PLUGIN_TOKEN": "test-token"}):
            client = TestClient(web.app, client=("127.0.0.1", 50000))
            self.assertEqual(client.get("/api/group-files", params={"group_id": "456"}).status_code, 403)
            self.assertEqual(client.get("/api/group-files", params={"group_id": "123"}).json()["total"], 2)
            response = client.post("/api/group-files/export", json={"group_id": "123", "file_id": "file1"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.store.task(response.json()["task_id"])["status"], "done")
            self.assertTrue(self.store.rows("SELECT * FROM audit WHERE tool='export_group_file'"))
            self.assertEqual(client.post("/api/plugin/tool", json={"group_id": "123", "tool": "export_group_file", "args": {"file_id": "file1"}}, headers={"Authorization": "Bearer test-token"}).status_code, 403)


if __name__ == "__main__":
    unittest.main()
