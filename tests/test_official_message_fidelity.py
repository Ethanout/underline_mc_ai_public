"""Reproduce the serialized nested quote shape supplied by the live QQ gateway."""

import asyncio
from unittest.mock import AsyncMock, patch

from qq_official_adapter.codec import build_message
from test_official_adapter import config


def event(**overrides):
    return {"id": "root", "group_openid": "group", "author": {"id": "user"},
            "content": "现在能看到吗", "timestamp": "2026-10-25T20:37:20+08:00", **overrides}


def test_serialized_nested_quote_downloads_original_and_retains_parallel_text():
    async def run():
        url = "https://multimedia.nt.qq.com.cn/download?fileid=test&spec=0"
        text = ("=== 消息 1 ===\n[消息内容] 这张图\n[消息类型] 引用消息\n[关联消息]\n"
                "--- 第1条 ---\n    [消息类型] 引用消息\n"
                f"    [附件1] 类型:图片 文件名:source.jpg 尺寸:3168x1440 大小:763.3KB URL:{url}\n")
        data = event(message_type=103, msg_elements=[{"content": text}],
                     parallel_message={"msg_nodes": [{"content": "@神王 这张图", "message_type": 0}]})
        image = {"type": "image", "data": "", "hash": "original", "binary_data_base64": "DATA"}
        with patch("qq_official_adapter.codec.image_component", AsyncMock(return_value=image)) as download:
            result = await build_message(config(), "GROUP_AT_MESSAGE_CREATE", data, None)
        download.assert_awaited_once_with(None, url)
        trees = [part for part in result["raw_message"] if part["type"] == "forward"]
        assert image in trees[0]["data"][0]["content"]
        assert result["is_picture"]
        assert trees[1]["data"][0]["content"][0]["data"] == "@神王 这张图"
        source = next(part["data"]["payload"] for part in result["raw_message"]
                      if part["type"] == "dict" and part["data"]["type"] == "official_message_source")
        assert source["msg_elements"][0]["content"] == text
        assert "message_scene" not in source
        assert not any(part["type"] == "reply" for part in result["raw_message"])
    asyncio.run(run())


def test_long_text_card_and_branches_beyond_eager_limit_are_preserved():
    async def run():
        card = {"prompt": "网页分享", "fields": {"title": "卡片标题", "url": "https://example.org/page"}}
        elements = [{"content": "长" * 10000 + "正文末尾", "ark_data": card}]
        elements.extend({"content": f"节点{i}"} for i in range(65))
        result = await build_message(config(), "GROUP_AT_MESSAGE_CREATE", event(msg_elements=elements), None)
        tree = next(part for part in result["raw_message"] if part["type"] == "forward")
        assert tree["data"][0]["content"][0]["data"].endswith("正文末尾")
        assert any(part["type"] == "dict" and part["data"]["type"] == "official_card"
                   for part in tree["data"][0]["content"])
        source = next(part["data"]["payload"] for part in result["raw_message"]
                      if part["type"] == "dict" and part["data"]["type"] == "official_message_source")
        assert source["msg_elements"] == elements
        assert "预览截断" in result["processed_plain_text"]
    asyncio.run(run())


def test_failed_eager_download_keeps_a_readable_original_attachment_link():
    async def run():
        attachment = {"filename": "large.png", "content_type": "image/png", "url": "https://example.qq.com/full.png"}
        with patch("qq_official_adapter.codec.image_component", AsyncMock(return_value={
            "type": "text", "data": "[图片：超过8 MiB下载上限]",
        })):
            result = await build_message(config(), "GROUP_AT_MESSAGE_CREATE", event(attachments=[attachment]), None)
        file = next(part for part in result["raw_message"] if part["type"] == "file")
        assert file["data"]["url"] == attachment["url"]
        assert file["data"]["mime_type"] == "image/png"
    asyncio.run(run())
