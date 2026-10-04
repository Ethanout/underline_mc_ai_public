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
from unittest.mock import patch

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

    def test_service_failure_is_reported_as_tool_content(self):
        with patch.object(self.plugin_module, "read_token", side_effect=client.ServiceError("读不到插件 token 文件")):
            result = asyncio.run(self.plugin.handle_read_essence(group_id="100000001"))
        self.assertEqual(result["content"], "查询失败：读不到插件 token 文件")


if __name__ == "__main__":
    unittest.main()
