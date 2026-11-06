"""The MaiBot plugin, tested offline with a stand-in for ``maibot_sdk``."""

from __future__ import annotations

import asyncio
import io
import json
import re
import sys
import types
import unittest
import urllib.error
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "maibot_plugin"))
from underline_tools import client  # noqa: E402


def fake_sdk():
    """Just enough of maibot_sdk for plugin.py to import and run."""
    sdk = types.ModuleType("maibot_sdk")
    sdk_types = types.ModuleType("maibot_sdk.types")

    def decorator(kind):
        def make(name, **options):
            def wrap(function):
                function.component = (kind, name, options)
                return function

            return wrap

        return make

    class ConfigBase:
        def __init__(self, **values):
            for key, value in type(self).__dict__.items():
                if isinstance(value, dict) and "default" in value:
                    setattr(self, key, value["default"])
                elif isinstance(value, dict) and "default_factory" in value:
                    setattr(self, key, value["default_factory"]())
            for key, value in values.items():
                setattr(self, key, value)

    sdk.Tool, sdk.Command = decorator("tool"), decorator("command")
    sdk.Field = lambda **options: options
    sdk.PluginConfigBase = ConfigBase
    sdk.MaiBotPlugin = type("MaiBotPlugin", (), {})
    sdk_types.ToolParameterInfo = lambda **options: options
    sdk_types.ToolParamType = types.SimpleNamespace(STRING="string", INTEGER="integer")
    return {"maibot_sdk": sdk, "maibot_sdk.types": sdk_types}


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class ClientTests(unittest.TestCase):
    def test_request_carries_bearer_group_and_tool(self):
        seen = []

        def opener(request, timeout):
            seen.append(request)
            return Response(json.dumps({"messages": []}).encode())

        client.call_tool("search_chat", "100000001", {"keyword": "x"}, "tok", opener=opener)
        request = seen[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:18787/api/plugin/tool")
        self.assertEqual(request.get_header("Authorization"), "Bearer tok")
        self.assertEqual(
            json.loads(request.data),
            {"tool": "search_chat", "group_id": "100000001", "args": {"keyword": "x"}},
        )
        with self.assertRaisesRegex(client.ServiceError, "群聊"):
            client.call_tool("search_chat", "", {}, "tok", opener=opener)

    def test_errors_become_plain_messages_without_the_token(self):
        def refused(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 401, "no", {}, None)

        def down(request, timeout):
            raise urllib.error.URLError("refused")

        with self.assertRaisesRegex(client.ServiceError, "token 不对") as caught:
            client.call_tool("search_chat", "1", {}, "secret-token", opener=refused)
        self.assertNotIn("secret-token", str(caught.exception))
        with self.assertRaisesRegex(client.ServiceError, "连不上"):
            client.call_tool("search_chat", "1", {}, "tok", opener=down)

    def test_token_file_is_required(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "plugin.txt"
            with self.assertRaisesRegex(client.ServiceError, "读不到"):
                client.read_token(path)
            path.write_text("\n", encoding="utf-8")
            with self.assertRaisesRegex(client.ServiceError, "空的"):
                client.read_token(path)
            path.write_text("tok\n", encoding="utf-8")
            self.assertEqual(client.read_token(path), "tok")
        self.assertEqual(client.DEFAULT_TOKEN_FILE, ROOT / "config" / "api" / "qqbot_plugin.txt")

    def test_http_400_preserves_actionable_detail_without_credentials(self):
        def refused(request, timeout):
            body = json.dumps({"detail": "官方端不支持实时精华，请用 underline_search_knowledge secret-token"}).encode()
            raise urllib.error.HTTPError(request.full_url, 400, "bad", {}, io.BytesIO(body))

        with self.assertRaisesRegex(client.ServiceError, "underline_search_knowledge") as caught:
            client.call_tool("read_essence", "official:123:one", {}, "secret-token", opener=refused)
        self.assertNotIn("secret-token", str(caught.exception))

    def test_results_keep_sources_and_stay_short(self):
        text = client.format_result(
            {
                "results": [
                    {"label": "技巧（AI 整理、未验证）", "content": "# 转视角\nexecute rotated", "sources": ["g:3"]},
                    {"label": "聊天", "message_id": "7", "nickname": "群友", "text": "试试 rotated"},
                ]
            }
        )
        self.assertIn("[技巧（AI 整理、未验证），来源 g:3] # 转视角 execute rotated", text)
        self.assertIn("[聊天 #7] 群友：试试 rotated", text)
        essence = {"message_id": "9", "sender_nick": "伊桑", "message": [{"type": "text", "data": {"text": "精华"}}, {"type": "image", "data": {}}]}
        self.assertEqual(client.format_result({"messages": [essence]}), "[#9] 伊桑：精华[image]")
        self.assertEqual(client.format_result({"messages": []}), "没查到相关内容。")
        many = {"messages": [{"message_id": str(i), "text": "x" * 200} for i in range(50)]}
        clipped = client.format_result(many, limit=1000)
        self.assertLess(len(clipped), 1100)
        self.assertIn("没列出", clipped)

    def test_research_results_keep_receipts_and_evidence(self):
        read = client.format_result({"source_id": "web:abc", "title": "文档", "url": "https://example.com",
                                     "content": "x" * 8000, "truncated": False})
        self.assertIn("source_id=web:abc", read)
        self.assertLessEqual(len(read), client.MAX_RESULT_CHARS)
        saved = client.format_result({"knowledge_id": "research:abc", "verification": "未验证",
                                      "tags": ["minecraft"], "source_ids": ["web:abc"]})
        self.assertIn("knowledge_id=research:abc", saved)
        self.assertIn("未验证", saved)
        search = client.format_result({"results": [{"title": "官网", "url": "https://example.com", "summary": "真实摘要"}]})
        self.assertIn("https://example.com", search)
        self.assertIn("真实摘要", search)


class PluginTests(unittest.TestCase):
    def setUp(self):
        self.modules = patch.dict(sys.modules, fake_sdk())
        self.modules.start()
        sys.modules.pop("underline_tools.plugin", None)
        from underline_tools import plugin

        self.plugin_module = plugin
        self.plugin = plugin.create_plugin()
        self.plugin.config = plugin.UnderlineToolsConfig()

    def tearDown(self):
        sys.modules.pop("underline_tools.plugin", None)
        self.modules.stop()

    def test_task_command_is_intercepted_but_chat_is_not(self):
        pattern = re.compile(self.plugin_module.TASK_PATTERN)
        for text in ("/毯 查技巧", "  /毯", "/毯\n多行"):
            self.assertTrue(pattern.search(text), text)
        for text in ("/毯毯", "/毯子 你好", "毯毯在吗", "说 /毯"):
            self.assertFalse(pattern.search(text), text)
        self.assertEqual(asyncio.run(self.plugin.handle_task(text="/毯 x")), (True, None, True))

    def test_tool_uses_the_chat_group_and_only_read_only_service_tools(self):
        calls = []

        def call_tool(tool, group_id, args, token, url, timeout):
            calls.append((tool, group_id, args, token))
            return {"messages": [{"message_id": "1", "nickname": "群友", "text": "execute"}]}

        with patch.object(self.plugin_module, "call_tool", call_tool), \
                patch.object(self.plugin_module, "read_token", lambda path: "tok"):
            result = asyncio.run(self.plugin.handle_search_chat(keyword="execute", group_id="100000001", platform="qq"))
            asyncio.run(self.plugin.handle_search_knowledge(query="转视角", group_id="100000001"))
            asyncio.run(self.plugin.handle_read_essence(group_id="100000001"))
            private = asyncio.run(self.plugin.handle_read_essence(group_id="1", platform="wechat"))
        self.assertEqual(result["content"], "[#1] 群友：execute")
        self.assertEqual(
            [(tool, group, args) for tool, group, args, _ in calls],
            [
                ("search_chat", "100000001", {"keyword": "execute"}),
                ("search_knowledge", "100000001", {"queries": ["转视角"]}),
                ("read_essence", "100000001", {}),
            ],
        )
        self.assertIn("只支持 QQ", private["content"])

    def test_private_chat_can_look_into_a_named_group(self):
        with patch.object(self.plugin_module, "call_tool", return_value={"messages": []}) as call, \
                patch.object(self.plugin_module, "read_token", return_value="tok"):
            asyncio.run(self.plugin.handle_search_chat(keyword="接水管", target_group="1060595795", user_id="42"))
            asyncio.run(self.plugin.handle_read_essence(target_group="123", group_id="100000001"))
        self.assertEqual([entry.args[1] for entry in call.call_args_list], ["1060595795", "123"])

    def test_failed_queries_are_reported_as_failures(self):
        with patch.object(self.plugin_module, "call_tool", side_effect=client.ServiceError("请用知识检索")), \
                patch.object(self.plugin_module, "read_token", return_value="tok"):
            result = asyncio.run(self.plugin.handle_read_essence(group_id="official:123:one", platform="qq_official"))
        self.assertFalse(result["success"])
        self.assertIn("请用知识检索", result["content"])

    def test_save_requires_complete_receipt_and_reports_failed_promises(self):
        for response in ({"error": "工作区写入失败"}, {"status": "saved"}):
            with patch.object(self.plugin_module, "call_tool", return_value=response), \
                    patch.object(self.plugin_module, "read_token", return_value="tok"):
                result = asyncio.run(self.plugin.handle_save_research(group_id="123"))
            self.assertFalse(result["success"])
            self.assertIn("及时纠正", result["content"])

    def test_chat_in_group_triggers_proactive_turn_with_cooldown(self):
        calls = []

        class Chat:
            async def get_group_streams(self, platform="qq"):
                return {"success": True, "streams": [
                    {"stream_id": "s-1060595795", "group_id": "1060595795", "group_name": "接水管", "platform": "qq"},
                    {"stream_id": "s-100000001", "group_id": "100000001", "group_name": "Underline", "platform": "qq"},
                ]}

        class Maisaka:
            async def trigger_proactive(self, stream_id, intent, **kw):
                calls.append((stream_id, intent))
                return {"success": True}

        self.plugin.ctx = types.SimpleNamespace(chat=Chat(), maisaka=Maisaka())
        self.plugin._cross_sends = {}
        run = lambda **kw: asyncio.run(self.plugin.handle_chat_in_group(**kw))["content"]  # noqa: E731
        self.assertIn("尚未确认实际发送", run(target_group="1060595795", intent="跟大家打个招呼", user_id="42"))
        self.assertIn("刚去过", run(target_group="1060595795", intent="再说一句"))
        self.assertIn("去不了", run(target_group="999", intent="x"))
        self.assertIn("直接说", run(target_group="100000001", intent="x", group_id="100000001"))
        self.assertEqual(calls, [("s-1060595795", "跟大家打个招呼")])

    def test_official_group_can_be_listed_and_targeted_by_explicit_legacy_binding(self):
        group = "official:1905809752:0D3256A1E59EF023E38DEC9B7CEA4012"
        chat = types.SimpleNamespace(get_group_streams=AsyncMock(return_value={"success": True, "streams": [
            {"stream_id": "old", "group_id": "100000001", "platform": "qq", "group_name": "Underline"},
            {"stream_id": "official", "group_id": group, "platform": "qq_official", "group_name": "官方Underline"},
        ]}))
        trigger = AsyncMock(return_value={"success": True})
        self.plugin.ctx = types.SimpleNamespace(chat=chat, maisaka=types.SimpleNamespace(trigger_proactive=trigger))
        self.plugin._cross_sends = {}
        with patch.object(self.plugin_module, "read_group_bindings", return_value={group: "100000001"}):
            listing = asyncio.run(self.plugin.handle_list_groups(platform="qq_official"))
            result = asyncio.run(self.plugin.handle_chat_in_group(target_group="100000001", intent="测试打招呼",
                                                                platform="qq_official", user_id="person"))
        self.assertIn(group, listing["content"])
        self.assertIn("已绑定旧群号=100000001", listing["content"])
        self.assertEqual(chat.get_group_streams.call_args.kwargs, {"platform": "all_platforms"})
        self.assertTrue(result["success"])
        self.assertIn("尚未确认实际发送", result["content"])
        self.assertEqual(trigger.call_args.args[:2], ("official", "测试打招呼"))

    def test_official_full_id_works_when_binding_service_is_unavailable(self):
        group = "official:123:OPENID"
        self.plugin.ctx = types.SimpleNamespace(
            chat=types.SimpleNamespace(get_group_streams=AsyncMock(return_value={"success": True, "streams": [
                {"stream_id": "official", "group_id": group, "platform": "qq_official", "group_name": "group"}]})),
            maisaka=types.SimpleNamespace(trigger_proactive=AsyncMock(return_value={"success": True})))
        self.plugin._cross_sends = {}
        with patch.object(self.plugin_module, "read_group_bindings", side_effect=client.ServiceError("绑定不可读")):
            result = asyncio.run(self.plugin.handle_chat_in_group(target_group=group, intent="hello", platform="qq_official"))
        self.assertTrue(result["success"])

    def test_sdk_unwrapped_stream_list_is_accepted(self):
        # 真实 SDK 成功时把 {"success": True, "streams": [...]} 解包成列表
        group = "official:123:OPENID"
        trigger = AsyncMock(return_value={"success": True})
        self.plugin.ctx = types.SimpleNamespace(
            chat=types.SimpleNamespace(get_group_streams=AsyncMock(return_value=[
                {"stream_id": "official", "group_id": group, "platform": "qq_official", "group_name": "group"}])),
            maisaka=types.SimpleNamespace(trigger_proactive=trigger))
        self.plugin._cross_sends = {}
        with patch.object(self.plugin_module, "read_group_bindings", return_value={}):
            listing = asyncio.run(self.plugin.handle_list_groups())
            result = asyncio.run(self.plugin.handle_chat_in_group(target_group=group, intent="hello", platform="qq_official"))
        self.assertTrue(listing["success"])
        self.assertIn(group, listing["content"])
        self.assertTrue(result["success"])
        self.assertEqual(trigger.call_args.args[:2], ("official", "hello"))

    def test_ambiguous_group_and_failed_listing_never_submit_task(self):
        chat = types.SimpleNamespace(get_group_streams=AsyncMock(return_value={"success": True, "streams": [
            {"stream_id": str(index), "group_id": str(index), "platform": "qq", "group_name": "同名"}
            for index in range(2)]}))
        trigger = AsyncMock()
        self.plugin.ctx = types.SimpleNamespace(chat=chat, maisaka=types.SimpleNamespace(trigger_proactive=trigger))
        result = asyncio.run(self.plugin.handle_chat_in_group(target_group="同名", intent="hello"))
        self.assertFalse(result["success"])
        self.assertIn("歧义", result["content"])
        chat.get_group_streams.return_value = {"success": False, "error": "unavailable"}
        listing = asyncio.run(self.plugin.handle_list_groups())
        self.assertFalse(listing["success"])
        self.assertIn("读取本地群会话失败", listing["content"])
        trigger.assert_not_called()

    def test_service_failure_is_reported_as_tool_content(self):
        with patch.object(self.plugin_module, "read_token", side_effect=client.ServiceError("读不到插件 token 文件")):
            result = asyncio.run(self.plugin.handle_read_essence(group_id="100000001"))
        self.assertEqual(result["content"], "查询失败：读不到插件 token 文件")

    def test_research_tool_arguments_and_group_scope(self):
        with patch.object(self.plugin_module, "call_tool", return_value={"results": []}) as call, \
                patch.object(self.plugin_module, "read_token", return_value="tok"):
            asyncio.run(self.plugin.handle_web_search(query="Minecraft 1.21 execute", group_id="123"))
            asyncio.run(self.plugin.handle_web_read(url="https://example.com", group_id="123"))
            asyncio.run(self.plugin.handle_save_research(title="经验", content="结论", source_ids="web:a, work:1",
                                                       tags="minecraft, vanilla-dev", group_id="123"))
            asyncio.run(self.plugin.handle_recall_work(date="2026-10-07", group_id="123"))
        self.assertEqual([entry.args[0] for entry in call.call_args_list],
                         ["research_search", "research_read", "save_research", "recall_work"])
        self.assertTrue(all(entry.args[1] == "123" for entry in call.call_args_list))
        self.assertEqual(call.call_args_list[2].args[2]["source_ids"], ["web:a", "work:1"])
        self.assertEqual(call.call_args_list[2].args[2]["tags"], ["minecraft", "vanilla-dev"])


if __name__ == "__main__":
    unittest.main()
