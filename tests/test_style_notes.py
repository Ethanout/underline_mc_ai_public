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

    def _store(self, lines):
        store = Store(":memory:")
        for mid, (uid, name, text) in enumerate(lines, 1):
            store.append(
                {
                    "post_type": "message",
                    "message_type": "group",
                    "group_id": "g",
                    "message_id": str(mid),
                    "time": mid,
                    "user_id": uid,
                    "sender": {"nickname": name},
                    "message": [{"type": "text", "data": {"text": text}}],
                }
            )
        return store

    def _post(self, answer, seen):
        def post(payload):
            seen.append(payload)
            return {"choices": [{"message": {"content": answer}}]}

        return post

    def test_model_note_is_used_and_never_sees_names_or_bot_lines(self):
        store = self._store([("1", "小橘子", "笑死我了这个函数怎么又炸了"), ("self", "毯毯", "毯毯的话")])
        seen = []
        note = refresh_notes(store, "g", self._post("大家爱说笑死，句子短，常用 ww 结尾。", seen))
        self.assertIn("笑死", note)
        self.assertIn("人设优先", note)
        sent = seen[0]["messages"][1]["content"]
        self.assertNotIn("小橘子", sent)
        self.assertNotIn("毯毯的话", sent)
        self.assertEqual(seen[0]["thinking"], {"type": "enabled"})
        store.close()

    def test_quoting_a_source_line_or_naming_someone_is_rejected(self):
        line = "我昨天把整个存档的计分板都删光了真的崩溃"
        for answer in (f"有人说过「{line}」", "小橘子说话很短"):
            store = self._store([("1", "小橘子", line)])
            note = refresh_notes(store, "g", self._post(answer, []))
            self.assertIn("新增 1 条", note)
            self.assertNotIn("计分板", note)
            self.assertNotIn("小橘子", note)
            self.assertIn("已丢弃", store.get_state("style_notes_error:g"))
            store.close()

    def test_model_failure_keeps_cadence_fallback(self):
        store = self._store([("1", "a", "一句话")])

        def broken(payload):
            raise TimeoutError

        self.assertIn("新增 1 条", refresh_notes(store, "g", broken))
        self.assertEqual(store.get_state("style_notes_error:g"), "TimeoutError")
        store.close()
