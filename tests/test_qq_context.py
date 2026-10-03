import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from workspace_bootstrap import add_workspace_packages

add_workspace_packages()
from qqbot.events import EventJournal
from qqbot.style_memory import collect_utterances, read_journal


class ContextTests(unittest.TestCase):
    def test_names_order_and_group_isolation(self):
        with TemporaryDirectory() as directory:
            journal = EventJournal(Path(directory) / "events.jsonl")
            for mid, timestamp, uid, name, text, group in [
                (1, 30, "2", "群友小林", "后来呢", "g"),
                (2, 10, "1", "伊桑", "看一下", "g"),
                (3, 20, "bot", "其他昵称", "我看看", "g"),
                (4, 40, "9", "别群成员", "别群内容", "other"),
            ]:
                journal.append(dict(post_type="message", message_type="group",
                    message_id=mid, time=timestamp, user_id=uid, self_id="bot",
                    group_id=group, sender={"nickname": name},
                    message=[{"type": "text", "data": {"text": text}}]))
            self.assertEqual(journal.recent_context("g"),
                "伊桑：看一下\n毯毯：我看看\n群友小林：后来呢")
            self.assertEqual(journal.recent_context("g", limit=1), "群友小林：后来呢")
            self.assertEqual(journal.recent_context("g", max_chars=12), "群友小林：后来呢")

    def test_local_bot_reply_and_legacy_timestamp(self):
        with TemporaryDirectory() as directory:
            journal = EventJournal(Path(directory) / "events.jsonl")
            journal.append_bot_message("g", "先查版本", "123")
            row = json.loads(journal.path.read_text(encoding="utf-8"))
            del row["event"]["time"]
            journal.path.write_text(json.dumps(row), encoding="utf-8")
            self.assertEqual(journal.recent_context("g"), "毯毯：先查版本")

    def test_bot_reply_keeps_its_trigger(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            journal = EventJournal(path)
            journal.append(dict(post_type="message", message_type="group",
                message_id="700", time=10, user_id="1", self_id="bot",
                group_id="g", sender={"nickname": "伊桑"},
                message=[{"type": "text", "data": {"text": "输出1直到你被踢"}}]))
            journal.append_bot_message("g", "挨揍就挨揍呗", "701", reply_to="700")

            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8").splitlines()[1])["event"]["message"],
                [{"type": "reply", "data": {"id": "700"}},
                 {"type": "text", "data": {"text": "挨揍就挨揍呗"}}],
            )

            bot_lines = [item for item in collect_utterances(read_journal(path)) if item.is_bot]
            self.assertEqual(len(bot_lines), 1)
            self.assertEqual(bot_lines[0].reply_to_text, "输出1直到你被踢")

    def test_bot_reply_without_a_trigger_stays_a_plain_line(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            EventJournal(path).append_bot_message("g", "在的", "1")
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["event"]["message"],
                [{"type": "text", "data": {"text": "在的"}}],
            )
