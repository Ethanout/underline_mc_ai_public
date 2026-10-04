"""Style placeholders use aggregate cadence, excluding bot and private text."""

from __future__ import annotations
import unittest
from workspace_bootstrap import add_workspace_packages

add_workspace_packages()
from qqbot.store import Store
from qqbot.style_notes import refresh_notes


class StyleNotesTests(unittest.TestCase):
    def test_incremental_bot_exclusion_and_no_quotes(self):
        store = Store(":memory:")
        for mid, uid, text in ((1, "member", "一段私人内容"), (2, "self", "毯毯自己的长句")):
            store.append(
                {
                    "post_type": "message",
                    "message_type": "group",
                    "group_id": "g",
                    "message_id": str(mid),
                    "time": mid,
                    "user_id": uid,
                    "message": [{"type": "text", "data": {"text": text}}],
                }
            )
        note = refresh_notes(store, "g")
        self.assertIn("新增 1 条", note)
        self.assertNotIn("私人", note)
        self.assertNotIn("自己的长句", note)
        self.assertEqual(refresh_notes(store, "g"), note)
        store.close()
