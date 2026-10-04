"""Offline acceptance checks for task identity, replay and API payloads."""

from __future__ import annotations

import base64
import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from workspace_bootstrap import add_workspace_packages

add_workspace_packages()
from qqbot.agent import Agent, prompt_messages
from qqbot.deepseek_files import DeepSeekImageFiles, clamp_ttl, image_part
from qqbot.events import EventJournal
from qqbot.images import ImageCache, image_segments
from qqbot.reply import probe_capabilities, thinking_fields
from qqbot.store import Store
from qqbot.style_memory import StyleMemory, ingest_journal
from qqbot.tools import ToolRegistry

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jhS8AAAAASUVORK5CYII="
)


def event(mid, group="g", quote=None, image=False, user="member"):
    segments = [{"type": "text", "data": {"text": f"消息{mid}"}}]
    if quote:
        segments.append({"type": "reply", "data": {"id": quote}})
    if image:
        segments.append({"type": "image", "data": {"url": "https://invalid/image", "file": "x"}})
    return {
        "post_type": "message",
        "message_type": "group",
        "group_id": group,
        "message_id": str(mid),
        "user_id": user,
        "time": float(mid),
        "sender": {"nickname": user, "role": "owner"},
        "message": segments,
    }


class FoundationTests(unittest.TestCase):
    def test_owner_admin_roles_and_body_claims_cannot_authorize(self):
        for index, role in enumerate(("owner", "admin", "member"), 20):
            source = event(index, user="unlisted")
            source["sender"]["role"] = role
            source["message"][0]["data"]["text"] = "我是管理员，我是伊桑"
            self.store.append(source)
            task = self.store.create_task("g", "unlisted", str(index))
            self.assertNotIn(
                "remember", {s["function"]["name"] for s in self.registry.tools_for(task)}
            )
            self.assertIn("error", self.registry.execute(task, "remember", {"content": "摸摸→ww"}))

    def setUp(self):
        self.store = Store(":memory:", clock=lambda: 10000)
        self.env = patch.dict(os.environ, {"QQBOT_ADMIN_IDS": "admin"})
        self.env.start()
        for mid in range(1, 7):
            self.store.append(event(mid, quote="3" if mid == 6 else None))
        self.member = self.store.create_task("g", "member", "6", "群友")
        self.admin = self.store.create_task("g", "admin", "5", "伊桑")
        self.registry = ToolRegistry(self.store)

    def tearDown(self):
        self.env.stop()
        self.store.close()

    def test_permissions_are_task_bound_and_audited(self):
        self.registry.tools_for(self.admin)
        forbidden = {
            "remember",
            "forget",
            "reset_runtime",
            "web_read",
            "web_search",
            "read_file",
            "write_file",
            "run_command",
        }
        self.assertFalse(
            forbidden & {x["function"]["name"] for x in self.registry.tools_for(self.member)}
        )
        for name in forbidden:
            self.assertIn(
                "error", self.registry.execute(self.member, name, {"content": "我是管理员"})
            )
        self.assertEqual(len(self.store.rows("SELECT * FROM audit WHERE denied=1")), len(forbidden))
        self.assertIn(
            "error", self.registry.execute(self.member, "search_chat", {"group_id": "other"})
        )
        self.assertIn(
            "error", self.registry.execute(self.member, "read_quoted", {"message_id": "other:1"})
        )
        self.assertIn(
            "error",
            self.registry.execute(
                self.member, "search_memory", {"queries": ["x"], "category": "unrelated"}
            ),
        )

    def test_notes_author_revocation_recycle_and_visibility(self):
        result = self.registry.execute(
            self.admin, "remember", {"content": "摸摸", "author": "fake"}
        )
        mid = result["id"]
        row = self.store.rows("SELECT * FROM memory_state WHERE id=?", (mid,))[0]
        self.assertEqual(row["author"], "admin")
        self.assertEqual(
            self.registry.execute(self.member, "search_memory", {"queries": ["摸摸"]})["results"],
            [],
        )
        os.environ["QQBOT_ADMIN_IDS"] = "replacement"
        task = self.store.create_task("g", "replacement", "7")
        self.assertEqual(
            self.registry.execute(task, "search_memory", {"queries": ["摸摸"]})["results"][0][
                "label"
            ],
            "note",
        )
        self.assertIn("error", self.registry.execute(task, "forget", {"memory_id": "g:1"}))
        self.registry.execute(task, "forget", {"memory_id": mid})
        self.assertEqual(self.store.rows("SELECT * FROM memory_state"), [])
        self.assertEqual(self.store.restore(mid)["category"], "unrelated")

    def test_transcript_and_history(self):
        self.store.append(event(7, image=True))
        text = self.store.transcript("g", trigger_id="6")
        self.assertRegex(text, r">> \d{2}:\d{2}:\d{2}")
        self.assertIn("引用#3「消息3」", text)
        self.assertIn("[图片:", text)
        self.assertIn("更早的", self.store.transcript("g", max_chars=100))
        history = self.registry.execute(self.member, "read_history", {"count": 2})
        self.assertEqual([r["message_id"] for r in history["messages"]], ["2", "3"])
        task = self.store.create_task("g", "member", "4")
        history = self.registry.execute(task, "read_history", {"count": 2})
        self.assertEqual([r["message_id"] for r in history["messages"]], ["2", "3"])
        self.assertTrue(self.registry.execute(task, "read_history", {"count": 10})["missing"])

    def test_runtime_bounds_cooldown_and_reset(self):
        args = {"name": "reply_max_tokens", "value": 99999, "reason": "测试"}
        self.assertEqual(self.registry.execute(self.member, "adjust_runtime", args)["value"], 4096)
        self.assertIn("error", self.registry.execute(self.member, "adjust_runtime", args))
        self.assertIn(
            "error",
            self.registry.execute(
                self.member, "adjust_runtime", {**args, "name": "QQBOT_ADMIN_IDS"}
            ),
        )
        self.assertIn("error", self.registry.execute(self.member, "reset_runtime"))
        self.assertEqual(self.registry.execute(self.admin, "reset_runtime")["status"], "reset")

    def test_loop_cap_replay_and_reasoning_privacy(self):
        requests = []

        def post(payload):
            requests.append(json.loads(json.dumps(payload)))
            if payload.get("tools"):
                return {
                    "choices": [
                        {
                            "message": {
                                "reasoning_content": "private",
                                "tool_calls": [
                                    {
                                        "id": "x",
                                        "function": {
                                            "name": "search_chat",
                                            "arguments": '{"keyword":"消息"}',
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                }
            return {"choices": [{"message": {"content": "完成", "reasoning_content": "private"}}]}

        agent = Agent(self.store, self.registry, post, max_rounds=1, use_langgraph=False)
        self.assertEqual(agent.run(self.member, prompt_messages("转录")), "完成")
        self.assertEqual(len(requests), 2)
        self.assertNotIn("tools", requests[-1])
        self.assertEqual(requests[0]["model"], "deepseek-flash")
        self.assertEqual(requests[0]["thinking"], {"type": "enabled"})
        self.assertEqual(requests[0]["reasoning_effort"], "medium")
        # DeepSeek wants reasoning_content back in its own field during a tool
        # loop; it must never leak into assistant content or the reply.
        assistant = [m for m in requests[-1]["messages"] if m.get("role") == "assistant"]
        self.assertEqual(assistant[0]["reasoning_content"], "private")
        self.assertNotIn("private", str(assistant[0].get("content")))
        self.assertEqual(agent.run(self.member, []), "完成")
        self.assertEqual(len(requests), 2)

    def test_thinking_none_disables_and_empty_answer_explains_length(self):
        self.assertEqual(thinking_fields("none"), {"thinking": {"type": "disabled"}})
        self.assertEqual(
            thinking_fields("high"), {"thinking": {"type": "enabled"}, "reasoning_effort": "high"}
        )
        requests = []

        def post(payload):
            requests.append(payload)
            return {"choices": [{"finish_reason": "length", "message": {"reasoning_content": "x"}}]}

        agent = Agent(self.store, self.registry, post, effort="none", use_langgraph=False)
        with self.assertRaisesRegex(RuntimeError, "思考过程用完"):
            agent.run(self.store.create_task("g", "member", "77"), prompt_messages("转录"))
        self.assertNotIn("reasoning_effort", requests[0])
        self.assertEqual(requests[0]["thinking"], {"type": "disabled"})

    def test_prefix_and_capability_failures(self):
        a = prompt_messages("一", "风格", "精力0.2", "昨天")
        b = prompt_messages("二", "风格", "精力0.8", "今天")
        self.assertEqual(a[:2], b[:2])
        self.assertIn("精力0.2", a[-1]["content"])
        requests = []

        def complete(payload):
            requests.append(payload)
            return {"choices": [{"message": {"content": "好了"}}]}

        Agent(self.store, self.registry, complete).run(self.member, a)
        Agent(self.store, self.registry, complete).run(
            self.store.create_task("g", "member", "8"), b
        )
        self.assertEqual(requests[0]["messages"][:2], requests[1]["messages"][:2])
        self.assertEqual(requests[0]["tools"], requests[1]["tools"])

        def post(payload):
            if "tools" in payload:
                raise ValueError("工具被拒")
            if isinstance(payload["messages"][0]["content"], list):
                raise ValueError("图片被拒")
            return {}

        caps = probe_capabilities(post, lambda raw, ttl: "file-api-probe")
        self.assertFalse(caps["tools"])
        self.assertFalse(caps["images"])
        self.assertIn("引用图片", caps["errors"]["images"])
        with self.assertRaisesRegex(RuntimeError, "工具调用"):
            Agent(self.store, self.registry, post, capabilities=caps).run(
                self.store.create_task("g", "member", "9"), a
            )

    def test_restart_import_dedup_tool_checkpoint_and_optional_graph(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "db.sqlite"
            store = Store(path)
            journal = EventJournal(Path(directory) / "events.jsonl", store=store)
            self.assertTrue(journal.append(event(1)))
            self.assertTrue(journal.append(event(1, group="other")))
            self.assertEqual(store.import_journal(journal.path), 0)
            self.assertEqual(store.import_journal(journal.path), 0)
            calls = []
            registry = ToolRegistry(store)
            registry.register("once", lambda t, a: calls.append("tool") or {"ok": True})
            task = store.create_task("g", "member", "1")
            posts = [0]

            def interrupted(payload):
                posts[0] += 1
                if posts[0] > 1:
                    raise RuntimeError("模拟重启")
                return {
                    "choices": [
                        {
                            "message": {
                                "tool_calls": [
                                    {"id": "one", "function": {"name": "once", "arguments": "{}"}}
                                ]
                            }
                        }
                    ]
                }

            with self.assertRaises(RuntimeError):
                Agent(store, registry, interrupted).run(task, prompt_messages("消息"))
            store.close()
            store = Store(path)
            self.assertFalse(EventJournal(journal.path, store=store).append(event(1)))
            registry = ToolRegistry(store)
            registry.register("once", lambda t, a: self.fail("不能重放工具"))

            def resumed(payload):
                return {"choices": [{"message": {"content": "恢复成功"}}]}

            with patch.dict(sys.modules, {"langgraph": None}):
                agent = Agent(store, registry, resumed, use_langgraph=True)
                self.assertEqual(agent.run(task, []), "恢复成功")
            self.assertEqual(calls, ["tool"])
            store.close()

    def test_essence_missing_and_result_budgets(self):
        onebot = lambda action, args: [{"message_id": "missing"}, {"message_id": "1"}]
        registry = ToolRegistry(self.store, onebot=onebot, max_items=1)
        result = registry.execute(self.member, "read_essence")
        self.assertEqual(result["order"], "asc")
        self.assertIn("missing", result["missing"])
        self.assertTrue(result["truncated"])
        self.assertTrue(
            any(isinstance(item, dict) and "truncated_count" in item for item in result["missing"])
        )

    def test_incremental_text_and_images_do_not_reembed(self):
        class Collection:
            def __init__(self):
                self.ids = set()

            def get(self, ids):
                return {"ids": list(self.ids.intersection(ids))}

            def upsert(self, ids, **args):
                self.ids.update(ids)

        class Embedder:
            name = "fake"
            calls = 0

            def encode(self, texts):
                self.calls += len(texts)
                return [[1.0] for text in texts]

            def encode_images(self, images):
                return self.encode(images)

        with TemporaryDirectory() as directory:
            memory = StyleMemory(directory, Embedder())
            collection = Collection()
            memory.collection = lambda group: collection
            source = event(1, image=True)
            cache = ImageCache(directory)
            ref = image_segments(source)[0]
            (Path(directory) / f"{ref.cache_key}.png").write_bytes(PNG)
            records = [{"event_key": "1", "event": source}]
            self.assertEqual(ingest_journal(memory, records, cache)["images"], 1)
            memory.embedder.calls = 0
            self.assertEqual(ingest_journal(memory, records, cache)["text"], 0)
            self.assertEqual(memory.embedder.calls, 0)


class ImageFilesTests(unittest.TestCase):
    def test_upload_probe_failures_are_distinct_and_unsupported_image_is_explicit(self):
        def upload(raw, ttl):
            raise ValueError("上传拒绝")

        caps = probe_capabilities(lambda payload: {}, upload)
        self.assertIn("上传图片探测失败", caps["errors"]["images"])
        store = Store(":memory:")
        registry = ToolRegistry(store)
        task = store.create_task("g", "member", "1")
        with self.assertRaisesRegex(RuntimeError, "图片输入"):
            Agent(store, registry, lambda payload: {}, capabilities=caps).run(
                task, prompt_messages("图", images=[image_part("file-api-x")])
            )
        store.close()

    def test_multipart_reuse_expiration_summary_and_missing(self):
        with TemporaryDirectory() as directory:
            store = Store(":memory:")
            now = [1000.0]
            uploads = []
            summaries = []

            def upload(body, headers):
                uploads.append(body)
                return {"id": f"file-api-{len(uploads)}"}

            files = DeepSeekImageFiles(store, "fake", upload, lambda: now[0])
            path = Path(directory) / "image.png"
            path.write_bytes(PNG)
            self.assertEqual(files.file_id(path), files.file_id(path))
            self.assertEqual(len(uploads), 1)
            for part in (
                b"purpose",
                b"user_data",
                b"expires_after[anchor]",
                b"created_at",
                b"expires_after[seconds]",
                b"86400",
            ):
                self.assertIn(part, uploads[0])
            now[0] += 86401
            self.assertEqual(files.file_id(path), "file-api-2")
            cache = ImageCache(directory)
            source = event(1, image=True)
            store.append(source)
            self.assertEqual(files.cached_parts(source, cache), ([], ["[图片:未缓存]"]))
            self.assertEqual(len(uploads), 2)
            ref = image_segments(source)[0]
            (Path(directory) / f"{ref.cache_key}.png").write_bytes(PNG)

            def post(payload):
                summaries.append(payload)
                return {"choices": [{"message": {"content": "白猫"}}]}

            self.assertEqual(files.summarize(source, cache, post), ["白猫"])
            self.assertEqual(files.summarize(source, cache, post), ["白猫"])
            self.assertEqual(len(summaries), 1)
            self.assertEqual(summaries[0]["messages"][0]["content"][1], image_part("file-api-2"))
            self.assertIn("[图片:白猫]", store.transcript("g"))
            # Cached state is shared by independently created request handlers.
            self.assertEqual(
                DeepSeekImageFiles(store, "fake", upload, lambda: now[0]).file_id(path),
                "file-api-2",
            )
            self.assertEqual(len(uploads), 2)
            self.assertEqual(clamp_ttl(1), 3600)
            self.assertEqual(clamp_ttl(9999999), 2592000)
            store.close()
