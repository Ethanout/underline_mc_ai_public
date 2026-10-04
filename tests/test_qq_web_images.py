import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from workspace_bootstrap import add_workspace_packages

add_workspace_packages()
try:
    from fastapi.testclient import TestClient
    from qqbot import web
except ImportError:  # pragma: no cover - web extras not installed
    web = None


@unittest.skipIf(web is None, "fastapi/httpx 未安装")
class EventImageHookTests(unittest.TestCase):
    def test_new_image_message_is_queued_for_caching_once(self):
        event = {
            "post_type": "message",
            "message_type": "group",
            "message_id": 1,
            "group_id": "100000001",
            "user_id": "2",
            "message": [{"type": "image", "data": {"file": "A.jpg", "url": "https://x/a"}}],
        }
        with TemporaryDirectory() as directory:
            journal = web.EventJournal(Path(directory) / "events.jsonl")
            submitted = []
            fake_executor = mock.Mock()
            fake_executor.submit.side_effect = lambda fn, ev: submitted.append(ev)
            with mock.patch.object(web, "event_journal", journal), \
                    mock.patch.object(web, "image_executor", fake_executor), \
                    mock.patch.dict("os.environ", {"QQBOT_EVENT_TOKEN": "t"}):
                client = TestClient(web.app)
                headers = {"Authorization": "Bearer t"}
                self.assertEqual(client.post("/api/onebot/event", json=event, headers=headers).status_code, 200)
                client.post("/api/onebot/event", json=event, headers=headers)
                text_only = dict(event, message_id=2, message=[{"type": "text", "data": {"text": "在吗"}}])
                client.post("/api/onebot/event", json=text_only, headers=headers)
        self.assertEqual([ev["message_id"] for ev in submitted], [1])


if __name__ == "__main__":
    unittest.main()
