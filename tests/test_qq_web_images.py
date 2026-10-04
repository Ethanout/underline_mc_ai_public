import hashlib
import hmac
import json
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


def napcat_post(client, event, token):
    """Sign the way NapCat's HTTP client does: HMAC-SHA1 over the raw body."""
    body = json.dumps(event, ensure_ascii=False).encode("utf-8")
    signature = "sha1=" + hmac.new(token.encode(), body, hashlib.sha1).hexdigest()
    return client.post(
        "/api/onebot/event",
        content=body,
        headers={"Content-Type": "application/json", "x-self-id": "20002", "x-signature": signature},
    )


EVENT = {
    "post_type": "message",
    "message_type": "group",
    "message_id": 1,
    "group_id": "100000001",
    "user_id": "2",
    "message": [{"type": "text", "data": {"text": "奇怪"}}],
}


@unittest.skipIf(web is None, "fastapi/httpx 未安装")
class EventAuthTests(unittest.TestCase):
    def _client(self, directory):
        journal = web.EventJournal(Path(directory) / "events.jsonl")
        patches = [
            mock.patch.object(web, "event_journal", journal),
            mock.patch.dict("os.environ", {"QQBOT_EVENT_TOKEN": "secret-token"}),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        return TestClient(web.app, client=("127.0.0.1", 50000))

    def test_napcat_signature_is_accepted(self):
        with TemporaryDirectory() as directory:
            client = self._client(directory)
            response = napcat_post(client, EVENT, "secret-token")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["accepted"])

    def test_wrong_signature_and_missing_auth_are_rejected(self):
        with TemporaryDirectory() as directory:
            client = self._client(directory)
            self.assertEqual(napcat_post(client, EVENT, "other-token").status_code, 401)
            self.assertEqual(client.post("/api/onebot/event", json=EVENT).status_code, 401)

    def test_bearer_still_works_for_manual_calls(self):
        with TemporaryDirectory() as directory:
            client = self._client(directory)
            ok = client.post("/api/onebot/event", json=EVENT, headers={"Authorization": "Bearer secret-token"})
            bad = client.post("/api/onebot/event", json=EVENT, headers={"Authorization": "Bearer nope"})
            self.assertEqual((ok.status_code, bad.status_code), (200, 401))


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
                client = TestClient(web.app, client=("127.0.0.1", 50000))
                headers = {"Authorization": "Bearer t"}
                self.assertEqual(client.post("/api/onebot/event", json=event, headers=headers).status_code, 200)
                client.post("/api/onebot/event", json=event, headers=headers)
                text_only = dict(event, message_id=2, message=[{"type": "text", "data": {"text": "在吗"}}])
                client.post("/api/onebot/event", json=text_only, headers=headers)
        self.assertEqual([ev["message_id"] for ev in submitted], [1])


if __name__ == "__main__":
    unittest.main()
