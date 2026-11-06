"""Research provenance, isolation, dated work, and recoverable Markdown export."""
# ruff: noqa: E402 -- workspace packages must be added before their imports.

import json
import base64
import hashlib
import os
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from workspace_bootstrap import add_workspace_packages

add_workspace_packages()
from qqbot.research import ResearchLibrary, install_research_tools
from qqbot.store import Store
from qqbot.tools import ToolRegistry
from qqbot.web_research import PageText, PublicRedirect, public_url
from qqbot.workspaces import Workspaces


class FakeReader:
    def __init__(self):
        self.reads = 0

    def fetch(self, url):
        self.reads += 1
        return {"title": "execute 文档", "url": url, "content": "execute positioned 示例与适用限制"}

    def search(self, query):
        return [{"title": "execute 文档", "url": "https://example.com/doc", "summary": query}]


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.now = datetime(2026, 10, 7, 16, 30, tzinfo=timezone.utc).timestamp()
        self.store = Store(self.root / "db.sqlite", clock=lambda: self.now)
        self.task = self.store.create_task("123", "member", "1")
        self.other = self.store.create_task("456", "member", "2")
        self.registry = ToolRegistry(self.store)
        self.reader = FakeReader()
        self.workspaces = Workspaces(self.root / "work")
        self.library = install_research_tools(self.registry, self.reader, self.workspaces)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def read(self):
        return self.registry.execute(self.task, "research_read", {"url": "https://example.com/doc"})

    def save(self, source_id, content="execute positioned 用于相对定位", tags=None, task=None):
        return self.registry.execute(task or self.task, "save_research", {
            "title": "位置技巧", "content": content, "source_ids": [source_id],
            "tags": tags or ["minecraft", "vanilla-dev"], "version": "未知"})

    def test_read_cache_and_expiration_reuse_content_source(self):
        first = self.read()
        self.assertEqual(first["source_id"], self.read()["source_id"])
        self.assertEqual(self.reader.reads, 1)
        self.now += 21601
        self.assertEqual(first["source_id"], self.read()["source_id"])
        self.assertEqual(self.reader.reads, 2)
        self.read()
        self.assertEqual(self.reader.reads, 2)

    def test_snippet_and_cross_group_cannot_back_saved_knowledge(self):
        search = self.registry.execute(self.task, "research_search", {"query": "execute"})
        self.assertTrue(search["results"])
        self.assertIn("error", self.save("invented:source"))
        source = self.read()["source_id"]
        self.assertIn("error", self.save(source, task=self.other))
        self.assertEqual(self.store.rows("SELECT * FROM research_knowledge"), [])

    def test_persist_deduplicate_conflicting_claims_and_reopen(self):
        source = self.read()["source_id"]
        saved = self.save(source)
        self.assertEqual(saved["knowledge_id"], self.save(source)["knowledge_id"])
        self.assertNotEqual(saved["knowledge_id"], self.save(source, "不同结论，需要对照测试")["knowledge_id"])
        self.assertEqual(len(self.library.search("123", "位置")), 2)
        self.assertEqual(self.library.search("456", "位置"), [])
        self.store.close()
        self.store = Store(self.root / "db.sqlite", clock=lambda: self.now)
        self.assertEqual(len(ResearchLibrary(self.store).search("123", "位置")), 2)

    def test_official_alias_save_has_canonical_source_and_real_markdown(self):
        group = "official:123:group_openid"
        mid = "official:123:platform-message-id-longer-than-twelve"
        alias = "m" + base64.b32encode(hashlib.sha1(mid.encode()).digest()).decode().lower()[:6]
        task = self.store.create_task(group, "maibot", "official-task")
        self.store.append({"post_type": "message", "message_type": "group", "group_id": group,
                           "message_id": mid, "user_id": "user", "message": "block_transformer 实际来源"})
        saved = self.save("msg:" + alias, task=task)
        self.assertEqual(saved["status"], "saved")
        self.assertEqual(saved["source_ids"], ["msg:" + mid])
        path = Path(saved["path"])
        self.assertEqual(path.parent, self.root / "work" / "2026-10-08" / "official" / "123" / "group_openid")
        self.assertIn("位置技巧", path.read_text(encoding="utf-8"))
        self.assertEqual(self.save("msg:" + mid, task=task)["knowledge_id"], saved["knowledge_id"])
        self.assertEqual(len(self.library.search(group, "位置")), 1)
        other = self.store.create_task("official:123:other", "maibot", "other-task")
        self.assertIn("error", self.save("msg:" + alias, task=other))

    def test_markdown_failure_rolls_back_knowledge_and_retry_succeeds(self):
        source = self.read()["source_id"]
        with patch("qqbot.research.atomic_write_text", side_effect=OSError("磁盘写入失败")):
            result = self.save(source)
        self.assertIn("磁盘写入失败", result["error"])
        self.assertNotIn("knowledge_id", result)
        self.assertFalse(self.library.search("123", "位置"))
        self.assertEqual(self.save(source)["status"], "saved")

    def test_work_log_failure_preserves_original_error_and_success_receipt(self):
        source = self.read()["source_id"]
        with patch.object(self.workspaces, "record", side_effect=OSError("日志写入失败")):
            failed = self.save("msg:missing")
            self.assertIn("群消息不在本群", failed["error"])
            saved = self.save(source)
        self.assertEqual(saved["status"], "saved")
        self.assertIn("knowledge_id", saved)
        self.assertIn("日志写入失败", saved["workspace_warning"])
        audits = self.store.rows("SELECT result FROM audit WHERE tool='save_research'")
        self.assertEqual(len(audits), 2)

    def test_workspace_official_paths_are_isolated_and_reject_traversal(self):
        first = self.workspaces.directory(self.now, "official:123:same")
        second = self.workspaces.directory(self.now, "official:456:same")
        self.assertNotEqual(first, second)
        for invalid in ("../escape", "official:123:../escape", "official:../:group", "official:123:group:extra"):
            with self.assertRaisesRegex(ValueError, "群标识"):
                self.workspaces.directory(self.now, invalid)

    def test_timezone_files_audit_recall_and_failure_record(self):
        result = self.read()
        self.assertTrue((self.root / "work" / "2026-10-08" / "123").is_dir())
        recalled = self.registry.execute(self.task, "recall_work", {"date": "2026-10-08"})
        self.assertEqual(recalled["results"][0]["title"], "research_read")
        self.assertFalse(self.library.recall(self.other, {})["results"])
        with patch.object(self.reader, "fetch", side_effect=RuntimeError("读取失败")):
            failed = self.registry.execute(self.task, "research_read", {"url": "https://example.com/fail"})
        self.assertIn("读取失败", failed["error"])
        logs = list((self.root / "work" / "2026-10-08" / "123").glob("*.json"))
        self.assertTrue(any(json.loads(p.read_text(encoding="utf-8"))["result"].get("error") for p in logs))
        self.assertNotIn("knowledge_id", result)

    def test_actual_failure_experience_is_sourced_and_group_scoped(self):
        self.store.audit(self.task, "run_command", {"command": "python sample.py"}, {"returncode": 1, "stderr": "syntax error"})
        evidence = self.library.recall(self.task, {})["results"][0]["sources"][0]
        result = self.save(evidence, "运行失败，出现 syntax error", ["programming"])
        self.assertEqual(result["status"], "saved")
        self.assertIn("error", self.save(evidence, task=self.other))
        rows = self.store.rows("SELECT * FROM research_sources WHERE id=?", (evidence,))
        self.assertIn("syntax error", rows[0]["content"])

    def test_group_message_and_its_quote_back_saved_knowledge(self):
        def add(mid, segments, quote=""):
            self.store.write("INSERT INTO messages VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                             (f"123:{mid}", "123", mid, "u" + mid, "群友" + mid, "", self.now, quote,
                              json.dumps(segments, ensure_ascii=False), 0, "{}", ""))
        add("10", [{"type": "image", "data": {"file": "abc.png", "url": "https://x/download?rkey=secret"}}])
        add("11", [{"type": "text", "data": {"text": "block_transformer 右键任何方块都会生成战利品表"}}], "10")
        result = self.save("msg:11", "block_transformer 可检测右键方块位置和点击面")
        self.assertEqual(result["status"], "saved")
        content = self.store.rows("SELECT content FROM research_sources WHERE id='msg:11'")[0]["content"]
        self.assertIn("生成战利品表", content)
        self.assertIn("abc.png", content)
        self.assertNotIn("rkey", content)
        self.assertIn("error", self.save("msg:11", task=self.other))
        self.assertIn("error", self.save("msg:999"))

    def test_export_only_technical_markdown_and_keep_human_files(self):
        source = self.read()["source_id"]
        saved = self.save(source)
        self.save(source, "一般生活资料", ["general"])
        target = self.root / "wiki"
        target.mkdir()
        human = target / "human.md"
        human.write_text("人工验证内容", encoding="utf-8")
        result = self.library.export_wiki(root=target)
        self.assertEqual(result["count"], 1)
        path = Path(result["paths"][0])
        text = path.read_text(encoding="utf-8")
        self.assertIn("AI 整理、未验证", text)
        self.assertIn(saved["knowledge_id"], text)
        self.assertIn("https://example.com/doc", text)
        self.assertEqual(human.read_text(encoding="utf-8"), "人工验证内容")
        self.assertEqual(self.library.export_wiki(root=target)["paths"], result["paths"])
        path.write_text("人工改写", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "人工文件"):
            self.library.export_wiki(root=target)

    def test_knowledge_search_integration_and_no_host_tool_permission(self):
        self.save(self.read()["source_id"])
        with patch("qqbot.docs.library") as docs:
            docs.return_value.search.return_value = []
            result = self.registry.execute(self.task, "search_knowledge", {"queries": ["位置"]})
        self.assertEqual(result["results"][0]["label"], "研究知识（AI 整理、未验证）")
        self.assertIn("error", self.registry.execute(self.task, "run_command", {"command": "echo x"}))
        self.assertIn("error", self.registry.execute(self.task, "save_research", {"group_id": "456"}))

    def test_plugin_http_can_save_evidence_but_not_run_commands_or_cross_groups(self):
        from fastapi.testclient import TestClient
        from qqbot import web

        def install(registry):
            return install_research_tools(registry, self.reader, self.workspaces)

        with patch.object(web, "event_store", self.store), patch.object(web, "install_research_tools", install), \
                patch.dict(os.environ, {"QQBOT_PLUGIN_TOKEN": "test-token", "QQBOT_GROUPS": "123,456"}):
            client = TestClient(web.app, client=("127.0.0.1", 50000))
            headers = {"Authorization": "Bearer test-token"}
            body = {"group_id": "123", "tool": "research_read", "args": {"url": "https://example.com/doc"}}
            self.assertEqual(client.post("/api/plugin/tool", json=body).status_code, 401)
            source = client.post("/api/plugin/tool", json=body, headers=headers).json()["source_id"]
            save = {"group_id": "123", "tool": "save_research", "args": {
                "title": "资料", "content": "有来源的研究", "source_ids": [source], "tags": ["minecraft"]}}
            self.assertEqual(client.post("/api/plugin/tool", json=save, headers=headers).json()["status"], "saved")
            save["group_id"] = "456"
            self.assertIn("error", client.post("/api/plugin/tool", json=save, headers=headers).json())
            body["tool"] = "run_command"
            self.assertEqual(client.post("/api/plugin/tool", json=body, headers=headers).status_code, 403)


class PublicWebTests(unittest.TestCase):
    def test_private_hosts_and_redirects_refused(self):
        with patch("qqbot.web_research.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 80))]):
            with self.assertRaises(PermissionError):
                public_url("http://localhost/")
            with self.assertRaises(PermissionError):
                PublicRedirect().redirect_request(None, None, 302, "", {}, "http://localhost/")
        with self.assertRaises(ValueError):
            public_url("file:///secret")
        with self.assertRaises(ValueError):
            public_url("https://user:password@example.com/")

    def test_html_keeps_code_but_excludes_script(self):
        parser = PageText()
        parser.feed("<title>文档</title><script>evil</script><pre>execute\n  positioned ~ ~ ~</pre>")
        self.assertEqual("".join(parser.title_parts), "文档")
        self.assertNotIn("evil", "".join(parser.parts))
        self.assertIn("execute\n  positioned", "".join(parser.parts))


if __name__ == "__main__":
    unittest.main()
