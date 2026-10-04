"""Offline technical ingestion and host-tool acceptance tests."""
from __future__ import annotations
import os
import subprocess
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from workspace_bootstrap import add_workspace_packages
add_workspace_packages()
from qqbot.store import Store
from qqbot.tools import ToolRegistry
from qqbot.admin_tools import install_admin_tools
from qqbot.tricks import TrickStore, safe_extract_archive, read_code_attachment, video_source
from qqbot.collection import install_collection_tools


class TricksTests(unittest.TestCase):
    def test_manual_history_and_forward_collection_use_actual_sources(self):
        with TemporaryDirectory() as directory:
            store = Store(":memory:")
            event = {"post_type": "message", "message_type": "group", "group_id": "123", "message_id": "1",
                     "user_id": "admin", "message": [{"type": "text", "data": {"text": "execute"}},
                         {"type": "forward", "data": {"id": "forward"}}]}
            store.append(event)
            registry = ToolRegistry(store, onebot=lambda action, args: {"messages": [
                {"message_id": "f1", "time": 1, "message": [{"type": "text", "data": {"text": "execute"}}]}]})
            install_collection_tools(registry, lambda m: {"title": "技巧", "code": "execute"}, directory)
            task = store.create_task("123", "admin", "1")
            with patch.dict(os.environ, {"QQBOT_ADMIN_IDS": "admin"}):
                result = registry.execute(task, "collect_tricks", {"source": "forward", "forward_id": "forward"})
                self.assertEqual(result["entries"][0]["sources"], ["123:f1"])
                self.assertIn("error", registry.execute(task, "read_forward", {"forward_id": "unknown"}))
            store.close()
    def test_classifier_dedup_sources_conflicts_reindex(self):
        with TemporaryDirectory() as directory:
            store = Store(":memory:")
            calls = []
            def classify(message):
                calls.append(message)
                return {"title": "检测", "code": "say 1", "conclusion": message["text"]} if message["technical"] else None
            tricks = TrickStore(store, directory, classify)
            messages = [{"message_id": "1", "technical": False, "text": "吃饭"},
                        {"message_id": "2", "technical": True, "text": "有效", "sender": {"nickname": "伊桑"}},
                        {"message_id": "3", "technical": True, "text": "无效", "sender": {"nickname": "群友"}}]
            results = tricks.sync("123", messages)
            self.assertEqual(len(results), 2)
            self.assertEqual(len(list(Path(directory).rglob("*.md"))), 1)
            text = Path(results[0]["path"]).read_text(encoding="utf-8")
            for value in ("AI 整理、未验证", "伊桑", "123:2", "123:3", "有效", "无效", "未知"):
                self.assertIn(value, text)
            self.assertEqual(tricks.sync("123", messages), [])
            self.assertEqual(len(calls), 3)
            path = Path(results[0]["path"])
            path.write_text(text + "人工补充", encoding="utf-8")
            self.assertEqual(len(tricks.reindex()), 1)
            self.assertIn("人工补充", store.rows("SELECT content FROM memory_state")[0]["content"])
            store.close()

    def test_archive_paths_sizes_and_code_video(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("../bad", "/bad", "C:/bad", "..\\bad"):
                archive = root / "bad.zip"
                with zipfile.ZipFile(archive, "w") as zipped: zipped.writestr(name, "x")
                with self.assertRaises(ValueError): safe_extract_archive(archive, root / "out")
            with zipfile.ZipFile(root / "bad.zip", "w") as zipped: zipped.writestr("safe.mcfunction", "say 1")
            with self.assertRaises(ValueError): safe_extract_archive(root / "bad.zip", root / "out", max_bytes=1)
            safe_extract_archive(root / "bad.zip", root / "out")
            self.assertEqual(read_code_attachment(root / "out/safe.mcfunction"), "say 1")
            self.assertEqual(video_source({"data": {"url": "video"}})["source"], "video")

    def test_admin_timeout_truncation_full_audit(self):
        store = Store(":memory:")
        registry = ToolRegistry(store, max_chars=500)
        def runner(command, **kwargs):
            if command == "timeout": raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            return subprocess.CompletedProcess(command, 0, "x" * 2000, "")
        install_admin_tools(registry, runner=runner, web_search=lambda q: [{"title": q}])
        admin = store.create_task("g", "admin", "1")
        member = store.create_task("g", "member", "2")
        with patch.dict(os.environ, {"QQBOT_ADMIN_IDS": "admin"}):
            self.assertNotIn("run_command", {s["function"]["name"] for s in registry.tools_for(member)})
            self.assertIn("error", registry.execute(member, "run_command", {"command": "x"}))
            self.assertIn("超时", registry.execute(admin, "run_command", {"command": "timeout"})["error"])
            self.assertTrue(registry.execute(admin, "run_command", {"command": "long"})["truncated"])
            self.assertIn("x" * 2000, store.rows("SELECT result FROM audit ORDER BY id DESC")[0]["result"])
            self.assertIn("error", registry.execute(admin, "read_file", {"path": "config/api/x.txt"}))
        store.close()
