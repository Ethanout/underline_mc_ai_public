"""Management JSON rejects non-loopback clients without trusting headers."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from workspace_bootstrap import add_workspace_packages

add_workspace_packages()
from qqbot import web
from qqbot.store import Store


class AdminApiTests(unittest.TestCase):
    def test_first_event_profile_count_and_duplicate_tasks(self):
        from unittest.mock import Mock
        from qqbot.events import EventJournal

        store = Store(":memory:")
        source = {
            "post_type": "message",
            "message_type": "group",
            "group_id": "new-group",
            "message_id": "1",
            "user_id": "member",
            "self_id": "bot",
            "message": [{"type": "at", "data": {"qq": "bot"}}],
        }
        with TemporaryDirectory() as directory:
            journal = EventJournal(Path(directory) / "events.jsonl", store=store)
            queued = Mock()
            with (
                patch.object(web, "event_store", store),
                patch.object(web, "event_journal", journal),
                patch.object(web, "_brains", {}),
                patch.object(web, "executor", queued),
                patch.object(web, "memory_executor", Mock()),
            ):
                self.assertTrue(web.handle_event(source)["reply_queued"])
                self.assertFalse(web.handle_event(source)["reply_queued"])
                self.assertEqual(sum(web.get_brain("new-group").profile), 3)
                self.assertEqual(queued.submit.call_count, 1)
                self.assertEqual(len(store.rows("SELECT * FROM tasks")), 1)
                self.assertIn("@毯毯", store.transcript("new-group"))
        store.close()

    def test_loopback_endpoints_health_and_remote_denial(self):
        store = Store(":memory:")
        store.create_task("g", "member", "1")
        caps = {"deepseek-flash": {"tools": False, "images": False, "thinking": True}}
        with patch.object(web, "event_store", store), patch.object(web, "_capabilities", caps):
            client = TestClient(web.app, client=("127.0.0.1", 50000))
            for endpoint in (
                "tasks",
                "tasks/g:1",
                "audit",
                "memory",
                "memory/changes",
                "memory/forgetting",
                "recycle-bin",
                "brain",
                "runtime",
                "capabilities",
                "health",
            ):
                self.assertEqual(client.get("/api/" + endpoint).status_code, 200, endpoint)
            self.assertFalse(
                client.get("/api/health").json()["capabilities"]["deepseek-flash"]["tools"]
            )
            remote = TestClient(web.app, client=("192.0.2.1", 50000))
            self.assertEqual(
                remote.get("/api/tasks", headers={"X-Forwarded-For": "127.0.0.1"}).status_code, 403
            )
            self.assertEqual(remote.get("/api/health").status_code, 403)
            self.assertEqual(
                TestClient(web.app, client=("::1", 50000)).get("/api/health").status_code, 200
            )
        store.close()

    def test_bind_address_must_be_loopback(self):
        with patch.dict("os.environ", {"QQBOT_WEB_HOST": "0.0.0.0"}):
            with self.assertRaisesRegex(ValueError, "回环"):
                web.web_host()
