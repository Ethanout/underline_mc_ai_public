import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from workspace_bootstrap import add_workspace_packages

add_workspace_packages()
from qqbot.style_memory import (  # noqa: E402
    StyleMemory,
    collect_images,
    collect_utterances,
    collection_name,
    parse_since,
    message_text,
    read_journal,
    reply_target_id,
)


class FakeEmbedder:
    """Deterministic stand-in so tests never download bge-m3."""

    name = "fake"

    def encode(self, texts):
        vectors = []
        for text in texts:
            vector = [0.0] * 16
            for index, char in enumerate(text):
                vector[(ord(char) + index) % 16] += 1.0
            norm = sum(value * value for value in vector) ** 0.5 or 1.0
            vectors.append([value / norm for value in vector])
        return vectors


def record(message_id, text, user_id="1", name="伊桑", group="100000001", timestamp=100, self_id="bot", role="member", extra=None):
    event = {
        "post_type": "message",
        "message_type": "group",
        "message_id": message_id,
        "time": timestamp,
        "user_id": user_id,
        "self_id": self_id,
        "group_id": group,
        "sender": {"nickname": name, "role": role},
        "message": [{"type": "text", "data": {"text": text}}],
    }
    if extra:
        event["message"] = extra
    return {"received_at": timestamp, "event_key": str(message_id), "event": event}


class TemporaryStyleDirectory(TemporaryDirectory):
    """Windows keeps ChromaDB's sqlite file open; ignore cleanup errors."""

    def __init__(self):
        super().__init__(ignore_cleanup_errors=True)


class SegmentTests(unittest.TestCase):
    def test_message_text_keeps_only_text_segments(self):
        event = {"message": [
            {"type": "image", "data": {"file": "a.png"}},
            {"type": "at", "data": {"qq": "1"}},
            {"type": "text", "data": {"text": "在吗"}},
        ]}
        self.assertEqual(message_text(event), "在吗")
        self.assertEqual(message_text({"message": "not-a-list"}), "")

    def test_reply_target_id_reads_quoted_message(self):
        event = {"message": [
            {"type": "reply", "data": {"id": 42}},
            {"type": "text", "data": {"text": "附议"}},
        ]}
        self.assertEqual(reply_target_id(event), "42")
        self.assertEqual(reply_target_id({"message": []}), "")


class CollectTests(unittest.TestCase):
    def test_collect_marks_bot_lines_and_resolves_quotes(self):
        records = [
            record(1, "毯毯在吗"),
            record(2, "在的", user_id="bot", self_id="bot", extra=[
                {"type": "reply", "data": {"id": 1}},
                {"type": "text", "data": {"text": "在的"}},
            ]),
            record(3, "", user_id="2", name="卡儿"),
        ]
        utterances = collect_utterances(records)
        self.assertEqual([item.text for item in utterances], ["毯毯在吗", "在的"])
        question, answer = utterances
        self.assertFalse(question.is_bot)
        self.assertEqual(question.speaker, "伊桑")
        self.assertTrue(answer.is_bot)
        self.assertEqual(answer.speaker, "毯毯")
        self.assertEqual(answer.reply_to_text, "毯毯在吗")

    def test_collect_skips_non_group_and_unkeyed_records(self):
        private = record(1, "私聊")
        private["event"]["message_type"] = "private"
        unkeyed = record(2, "没 key")
        del unkeyed["event_key"]
        del unkeyed["event"]["message_id"]
        self.assertEqual(collect_utterances([private, unkeyed]), [])

    def test_collect_truncates_long_lines(self):
        utterances = collect_utterances([record(1, "喵" * 900)], max_chars=100)
        self.assertEqual(len(utterances[0].text), 100)

    def test_collect_drops_old_records_with_since(self):
        records = [record(1, "旧的", timestamp=100), record(2, "新的", timestamp=900)]
        self.assertEqual([item.text for item in collect_utterances(records, since=500)], ["新的"])
        self.assertEqual(len(collect_utterances(records)), 2)

    def test_bot_since_only_filters_the_bot(self):
        records = [
            record(1, "群友旧话", user_id="1", timestamp=100),
            record(2, "毯毯旧话", user_id="self", name="毯毯", role="bot", timestamp=100),
            record(3, "毯毯新话", user_id="self", name="毯毯", role="bot", timestamp=900),
        ]
        items = collect_utterances(records, bot_since=500)
        self.assertEqual(
            [(item.text, item.is_bot) for item in items],
            [("群友旧话", False), ("毯毯新话", True)],
        )

    def test_parse_since_accepts_date_and_minute(self):
        self.assertEqual(parse_since("2026-10-04 00:00"), parse_since("2026-10-04"))
        self.assertLess(parse_since("2026-10-04"), parse_since("2026-10-04 12:30"))
        with self.assertRaises(ValueError):
            parse_since("昨天")


class JournalTests(unittest.TestCase):
    def test_read_journal_skips_broken_lines(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text(
                json.dumps(record(1, "在吗"), ensure_ascii=False) + "\n\n{not json}\n",
                encoding="utf-8",
            )
            records = read_journal(path)
            self.assertEqual(len(records), 1)
            self.assertEqual(collect_utterances(records)[0].text, "在吗")

    def test_read_journal_tolerates_missing_file(self):
        self.assertEqual(read_journal("does/not/exist.jsonl"), [])


class CollectionNameTests(unittest.TestCase):
    def test_names_are_chroma_safe(self):
        self.assertEqual(collection_name("style", "100000001"), "style_100000001")
        self.assertEqual(collection_name("style", "a b/c"), "style_a_b_c")
        self.assertGreaterEqual(len(collection_name("style", "")), 3)


class StyleMemoryTests(unittest.TestCase):
    def test_ingest_then_search_roundtrip(self):
        with TemporaryStyleDirectory() as directory:
            memory = StyleMemory(Path(directory) / "db", FakeEmbedder())
            records = [
                record(1, "毯毯在吗"),
                record(2, "在的", user_id="bot", self_id="bot"),
                record(3, "load.json 会每 tick 跑吗"),
            ]
            self.assertEqual(memory.add(collect_utterances(records)), 3)
            self.assertEqual(memory.stats(), {"100000001": 3})

            # A self-query should retrieve the line itself; anything finer is
            # a property of the real embedding model, not of this pipeline.
            hits = memory.search("load.json 会每 tick 跑吗", "100000001", k=1)
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["text"], "load.json 会每 tick 跑吗")
            self.assertGreater(hits[0]["score"], 0.99)

            bot_hits = memory.search("在的", "100000001", k=2, is_bot=True)
            self.assertEqual([hit["text"] for hit in bot_hits], ["在的"])
            self.assertTrue(bot_hits[0]["is_bot"])

    def test_reingesting_the_same_journal_does_not_duplicate(self):
        with TemporaryStyleDirectory() as directory:
            memory = StyleMemory(Path(directory) / "db", FakeEmbedder())
            records = [record(1, "在吗"), record(2, "在的")]
            memory.add(collect_utterances(records))
            memory.add(collect_utterances(records))
            self.assertEqual(memory.stats(), {"100000001": 2})

    def test_groups_are_isolated(self):
        with TemporaryStyleDirectory() as directory:
            memory = StyleMemory(Path(directory) / "db", FakeEmbedder())
            memory.add(collect_utterances([record(1, "群一的话")]))
            memory.add(collect_utterances([record(2, "群二的话", group="100")]))
            self.assertEqual(sorted(memory.groups()), ["100", "100000001"])
            hits = memory.search("群二", "100", k=3)
            self.assertEqual([hit["text"] for hit in hits], ["群二的话"])

    def test_search_on_empty_collection_returns_nothing(self):
        with TemporaryStyleDirectory() as directory:
            memory = StyleMemory(Path(directory) / "db", FakeEmbedder())
            self.assertEqual(memory.search("在吗", "100000001"), [])


def image_segment(url, file=""):
    return {"type": "image", "data": {"url": url, "file": file, "summary": ""}}


class FakeImageEmbedder(FakeEmbedder):
    """Embeds an image as the text of its file contents, so tests can aim at it."""

    name = "fake-vl"

    def __init__(self, refuse=()):
        self.refuse = set(refuse)
        self.image_calls = []

    def encode_images(self, paths):
        self.image_calls.append(len(paths))
        contents = [Path(path).read_bytes()[8:].decode("utf-8") for path in paths]
        for content in contents:
            if content in self.refuse:
                raise RuntimeError(f"HTTP 400: {content}")
        return self.encode(contents)


def png_with(text):
    return b"\x89PNG\r\n\x1a\n" + text.encode("utf-8")


class CollectImageTests(unittest.TestCase):
    def test_image_only_message_becomes_an_image_entry(self):
        records = [
            record(1, "", extra=[image_segment("https://x/a", "A.jpg")]),
            record(2, "这个好", extra=[
                {"type": "text", "data": {"text": "这个好"}},
                image_segment("https://x/b"),
                image_segment("https://x/c"),
            ]),
        ]
        self.assertEqual([item.text for item in collect_utterances(records)], ["这个好"])
        images = collect_images(records)
        self.assertEqual([image.event_key for image in images], ["1#img0", "2#img0", "2#img1"])
        self.assertEqual(images[0].document, "[图片]")
        self.assertEqual(images[1].caption, "这个好")
        self.assertEqual(images[1].source_key, "2")
        self.assertEqual(images[0].metadata("p.png")["kind"], "image")

    def test_images_obey_the_same_time_filters(self):
        records = [
            record(1, "", timestamp=100, extra=[image_segment("https://x/a")]),
            record(2, "", timestamp=900, extra=[image_segment("https://x/b")]),
        ]
        self.assertEqual([image.source_key for image in collect_images(records, since=500)], ["2"])


class ImageMemoryTests(unittest.TestCase):
    def _image(self, directory, key, content, caption=""):
        path = Path(directory) / f"{key}.png"
        path.write_bytes(png_with(content))
        records = [record(key, caption, extra=[
            {"type": "text", "data": {"text": caption}},
            image_segment(f"https://x/{key}"),
        ])]
        return collect_images(records)[0], path

    def test_images_and_text_share_a_collection_and_filter_by_kind(self):
        with TemporaryStyleDirectory() as directory:
            memory = StyleMemory(Path(directory) / "db", FakeImageEmbedder())
            memory.add(collect_utterances([record(1, "猫猫打滚")]))
            stored, rejected = memory.add_images([self._image(directory, 2, "猫猫打滚", caption="看图")])
            self.assertEqual((stored, rejected), (1, []))
            self.assertEqual(memory.stats(), {"100000001": 2})

            image_hits = memory.search("猫猫打滚", "100000001", k=5, kind="image")
            self.assertEqual(len(image_hits), 1)
            self.assertEqual(image_hits[0]["kind"], "image")
            self.assertEqual(image_hits[0]["text"], "看图")
            self.assertTrue(image_hits[0]["image_path"].endswith("2.png"))

            text_hits = memory.search("猫猫打滚", "100000001", k=5, kind="text", is_bot=False)
            self.assertEqual([hit["text"] for hit in text_hits], ["猫猫打滚"])

            by_image = memory.search_image(Path(directory) / "2.png", "100000001", k=1, kind="image")
            self.assertGreater(by_image[0]["score"], 0.99)

    def test_a_refused_image_does_not_sink_its_batch(self):
        with TemporaryStyleDirectory() as directory:
            embedder = FakeImageEmbedder(refuse={"坏图"})
            memory = StyleMemory(Path(directory) / "db", embedder)
            items = [self._image(directory, 1, "好图一"), self._image(directory, 2, "坏图"), self._image(directory, 3, "好图二")]
            stored, rejected = memory.add_images(items)
            self.assertEqual(stored, 2)
            self.assertEqual([image.source_key for image, _ in rejected], ["2"])
            self.assertEqual(embedder.image_calls, [3, 1, 1, 1])

    def test_text_only_backend_refuses_images_clearly(self):
        with TemporaryStyleDirectory() as directory:
            memory = StyleMemory(Path(directory) / "db", FakeEmbedder())
            with self.assertRaises(ValueError):
                memory.add_images([self._image(directory, 1, "图")])


if __name__ == "__main__":
    unittest.main()
