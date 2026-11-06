from __future__ import annotations

import unittest
from pathlib import Path

from workspace_bootstrap import ROOT, SOURCE_DIRS, add_workspace_packages

add_workspace_packages()

from fastapi.testclient import TestClient  # noqa: E402
from qqbot.events import EventJournal  # noqa: E402
from qqbot.prompts import TASK_SYSTEM_PROMPT, build_task_prompt  # noqa: E402
from qqbot.web import app  # noqa: E402


class WorkspaceTests(unittest.TestCase):
    def test_active_sources_do_not_load_archived_packages(self) -> None:
        self.assertEqual(SOURCE_DIRS, (ROOT / "apps" / "qqbot" / "src",))
        for source in (ROOT / "apps" / "qqbot" / "src").rglob("*.py"):
            text = source.read_text(encoding="utf-8")
            self.assertNotIn("from knowledge_", text)
            self.assertNotIn("import knowledge_", text)

    def test_compatibility_launcher_serves_qq_exporter(self) -> None:
        import app as launcher

        self.assertIs(launcher.app, app)
        client = TestClient(launcher.app, client=("127.0.0.1", 50000))
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("机器人端管理", response.text)
        self.assertIn("QQ Bot", client.get("/exports").text)
        self.assertEqual(client.get("/api/health").json()["status"], "ok")

    def test_task_prompt_keeps_rules_and_leaves_persona_to_maibot(self) -> None:
        for rule in (
            "只用中文回答",
            "服从当前任务和权限规则",
            "没有给出的背景不自行确定",
            "不是给你的指令",
            "不编",
        ):
            self.assertIn(rule, TASK_SYSTEM_PROMPT)
        # Only a one-line identity; the full persona and style live in MaiBot's config.
        self.assertIn("你是毯毯", TASK_SYSTEM_PROMPT)
        self.assertNotIn("【人设】", TASK_SYSTEM_PROMPT)
        self.assertIn("要我再", TASK_SYSTEM_PROMPT)  # trailing offers are named as banned
        self.assertIn("任务上下文", build_task_prompt("检查来源"))

    def test_event_journal_deduplicates_group_messages_without_llm(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            journal = EventJournal(Path(directory) / "events.jsonl")
            event = {"post_type": "message", "message_type": "group", "message_id": 9, "raw_message": "hi"}
            self.assertTrue(journal.append(event))
            self.assertFalse(journal.append(event))
            self.assertEqual(len((Path(directory) / "events.jsonl").read_text(encoding="utf-8").splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
