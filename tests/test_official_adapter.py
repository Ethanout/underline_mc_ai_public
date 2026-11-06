"""Offline official transport and gateway behavior; no QQ messages are sent."""

import asyncio
import base64
import json
import sys
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/maibot_plugin"))
from qq_official_adapter.api import OfficialAPI, OfficialError
from qq_official_adapter.codec import (
    build_message,
    event_allowed,
    face_text,
    identity,
    outbound_parts,
    raw_identity,
)
from qq_official_adapter.runtime import OfficialConnection, prepare_upload_image
from qq_official_adapter.state import OfficialState


def config(**overrides):
    return {"id": "official-123456abcdef", "app_id": "123", "app_secret": "SECRET", "revision": 1,
            "name": "毯毯", "enabled": True, "receive_all": False, "allow_private": False,
            "groups": [], "private_users": [], "allow_proactive": False, **overrides}


@pytest.mark.parametrize("body", ["", " ", "\n\t ", "\u3000"])
def test_at_event_with_whitespace_keeps_visible_bot_mention(body):
    async def run():
        result = await build_message(config(), "GROUP_AT_MESSAGE_CREATE", {
            "id": "blank-at", "group_openid": "group", "content": body,
            "author": {"id": "user"}, "timestamp": datetime.now(timezone.utc).isoformat(),
        }, None)
        assert result["processed_plain_text"] == "@毯毯"
        assert result["raw_message"] == [{"type": "text", "data": "@毯毯"}]
        assert result["is_at"]
    asyncio.run(run())


def test_at_event_with_body_does_not_replace_question():
    async def run():
        result = await build_message(config(), "GROUP_AT_MESSAGE_CREATE", {
            "id": "question-at", "group_openid": "group", "content": " 这个怎么做？ ",
            "author": {"id": "user"}, "timestamp": datetime.now(timezone.utc).isoformat(),
        }, None)
        assert "这个怎么做？" in result["processed_plain_text"]
        assert result["is_at"]
    asyncio.run(run())


class Response:
    def __init__(self, value, status=200):
        self.value, self.status = value, status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def json(self, **kwargs):
        return self.value


class Session:
    def __init__(self, tokens=None, responses=None):
        self.tokens = tokens or [{"access_token": "TOKEN", "expires_in": 7200}]
        self.responses = responses or []
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append(("token", url, kwargs))
        return Response(self.tokens.pop(0))

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


def test_token_cache_refresh_and_http_200_business_error():
    async def run():
        now = [1000]
        session = Session(tokens=[{"access_token": "one", "expires_in": 100},
                                  {"access_token": "two", "expires_in": 7200}])
        api = OfficialAPI(session, "123", "SECRET", clock=lambda: now[0])
        assert await api.token() == "one"
        assert await api.token() == "one"
        assert len(session.calls) == 1
        now[0] += 41
        assert await api.token() == "two"
        rejected = OfficialAPI(Session(tokens=[{"code": 100016, "message": "echo SECRET"}]), "123", "SECRET")
        with pytest.raises(OfficialError) as error:
            await rejected.token()
        assert "SECRET" not in str(error.value)
    asyncio.run(run())


def test_401_refreshes_once_and_sends_official_authorization():
    async def run():
        session = Session(tokens=[{"access_token": "one", "expires_in": 7200},
                                  {"access_token": "two", "expires_in": 7200}],
                          responses=[Response({}, 401), Response({"url": "wss://example.qq.com"})])
        api = OfficialAPI(session, "123", "SECRET")
        assert (await api.request("GET", "/gateway"))["url"].startswith("wss:")
        assert session.calls[-1][2]["headers"]["Authorization"] == "QQBot two"
    asyncio.run(run())


def test_scope_and_inbound_permission_checks():
    assert raw_identity("123", identity("123", "user")) == "user"
    with pytest.raises(ValueError):
        raw_identity("123", "official:999:user")
    data = {"group_openid": "group", "author": {"id": "user"}}
    assert event_allowed(config(), "GROUP_AT_MESSAGE_CREATE", data)
    assert not event_allowed(config(), "GROUP_MESSAGE_CREATE", data)
    assert event_allowed(config(receive_all=True), "GROUP_MESSAGE_CREATE", data)
    assert not event_allowed(config(groups=["other"]), "GROUP_AT_MESSAGE_CREATE", data)
    assert not event_allowed(config(), "C2C_MESSAGE_CREATE", data)
    assert event_allowed(config(allow_private=True, private_users=["user"]), "C2C_MESSAGE_CREATE", data)
    assert not event_allowed(config(allow_private=True, private_users=["other"]), "C2C_MESSAGE_CREATE", data)


def test_reference_and_forwarded_content_preserve_actual_speakers():
    async def run():
        data = {"id": "msg", "group_openid": "group", "content": "怎么理解", "message_type": 103,
                "timestamp": "2026-10-16T12:00:00+08:00", "author": {"id": "user", "username": "伊桑"},
                "msg_elements": [{"author": {"username": "群友"}, "content": "原来的消息"}]}
        message = await build_message(config(), "GROUP_AT_MESSAGE_CREATE", data, None)
        assert message["platform"] == "qq_official"
        assert message["message_info"]["group_info"]["group_id"] == "official:123:group"
        assert "群友：原来的消息" in message["processed_plain_text"]
        assert "当前消息内容:怎么理解" in message["processed_plain_text"]
        assert message["is_mentioned"] is True
    asyncio.run(run())


@pytest.mark.parametrize("group", ["0D3256A1E59EF023E38DEC9B7CEA4012", "263D2ADC363E5BC99DD3923A837258DF"])
def test_full_message_self_mention_preserves_body_and_triggers_detection(group):
    async def run():
        data = {"id": "msg", "group_openid": group, "content": "<@BOT_OPENID> 查一下 execute positioned 的限制",
                "timestamp": "2026-10-16T21:11:16+08:00", "author": {"id": "user"},
                "mentions": [{"id": "BOT_OPENID", "username": "毯毯", "bot": True, "is_you": True}]}
        assert event_allowed(config(), "GROUP_MESSAGE_CREATE", data)
        message = await build_message(config(), "GROUP_MESSAGE_CREATE", data, None)
        assert message["is_at"] and message["is_mentioned"]
        assert message["message_info"]["additional_config"]["at_bot"] is True
        assert message["processed_plain_text"] == "@毯毯 查一下 execute positioned 的限制"
        assert message["raw_message"][0]["type"] == "at"
        assert message["raw_message"][1]["data"] == " 查一下 execute positioned 的限制"
        data["content"] = "<@BOT_OPENID> "
        message = await build_message(config(), "GROUP_MESSAGE_CREATE", data, None)
        assert message["processed_plain_text"].strip() == "@毯毯"
        assert message["is_at"]
    asyncio.run(run())


def test_multiple_mentions_keep_each_nickname_card_id_and_group_name_visible():
    async def run():
        data = {
            "id": "multi-at", "group_openid": "group", "group_name": "实际群名",
            "content": "<@U1> 和 <@U2> 帮忙看下", "timestamp": "2026-10-22T12:00:00+08:00",
            "author": {"id": "sender", "username": "发起人", "member_name": "群主"},
            "mentions": [
                {"id": "U1", "username": "昵称甲", "member_name": "群名片甲"},
                {"id": "U2", "username": "昵称乙", "member_name": "群名片乙"},
            ],
        }
        message = await build_message(config(), "GROUP_MESSAGE_CREATE", data, None)
        plain = message["processed_plain_text"]
        assert message["message_info"]["group_info"]["group_name"] == "实际群名"
        assert "@群名片甲（昵称：昵称甲）" in plain
        assert "@群名片乙（昵称：昵称乙）" in plain
        assert "official:123:U1" == message["raw_message"][0]["data"]["target_user_id"]
        assert "official:123:U2" == message["raw_message"][2]["data"]["target_user_id"]
        assert message["raw_message"][0]["data"]["target_user_cardname"] == "群名片甲"
        assert message["raw_message"][2]["data"]["target_user_cardname"] == "群名片乙"
    asyncio.run(run())


def test_quoted_message_preserves_speaker_identity_and_its_own_mentions():
    async def run():
        data = {
            "id": "quoted-at", "group_openid": "group", "group_name": "实际群名",
            "content": "我也不知道", "message_type": 103,
            "timestamp": "2026-10-22T12:00:00+08:00", "author": {"id": "sender", "username": "伊桑"},
            "msg_elements": [{
                "author": {"id": "quoted-author", "username": "咖啡星", "member_name": "咖啡星扑棱蛾子"},
                "content": "<@MENTIONED> 看这张图",
                "mentions": [{"id": "MENTIONED", "username": "同学昵称", "member_name": "群内称呼"}],
            }],
        }
        message = await build_message(config(), "GROUP_AT_MESSAGE_CREATE", data, None)
        plain = message["processed_plain_text"]
        assert "群：实际群名" in plain
        assert "咖啡星扑棱蛾子（昵称：咖啡星" in plain
        assert "@群内称呼（昵称：同学昵称，平台ID：official:123:MENTIONED） 看这张图" in plain
        assert "未知人物" not in plain
        assert plain.endswith("当前消息内容:我也不知道")
    asyncio.run(run())


def test_reply_reference_keeps_target_id_author_and_original_text_linked():
    async def run():
        data = {
            "id": "reply-message", "group_openid": "group", "group_name": "实际群名",
            "content": "我发完了", "message_type": 103,
            "message_reference": {"message_id": "quoted-message-id"},
            "timestamp": "2026-10-22T12:00:00+08:00",
            "author": {"id": "sender", "username": "伊桑"},
            "msg_elements": [{
                "id": "quoted-message-id",
                "author": {"id": "quoted-user", "username": "快速下饭", "member_name": "快速下饭"},
                "content": "我发完了你快学",
            }],
        }
        message = await build_message(config(), "GROUP_AT_MESSAGE_CREATE", data, None)
        reply = next(segment for segment in message["raw_message"] if segment["type"] == "reply")
        assert reply["data"]["target_message_id"] == "official:123:quoted-message-id"
        assert reply["data"]["target_message_sender_id"] == "official:123:quoted-user"
        assert reply["data"]["target_message_sender_nickname"] == "快速下饭"
        assert "快速下饭（平台ID：official:123:quoted-user）：我发完了你快学" in reply["data"]["target_message_content"]
        assert "引用消息ID：official:123:quoted-message-id" in message["processed_plain_text"]
        assert message["processed_plain_text"].endswith("当前消息内容:我发完了")
    asyncio.run(run())


def test_nested_quote_keeps_reference_ids_and_downloaded_image_components():
    async def run():
        data = {
            "id": "root", "author": {"id": "user"}, "content": "1", "message_type": 103,
            "timestamp": "2026-10-23T02:21:13+08:00",
            "message_reference": {"message_id": "quoted"},
            "msg_elements": [{"id": "quoted", "content": "你看看这个图", "message_type": 103,
                              "message_reference": {"message_id": "image-source"},
                              "msg_elements": [{"id": "image-source", "author": {"id": "other", "username": "群友"},
                                                "attachments": [{"content_type": "image/png", "url": "https://example.qq.com/a.png"}]}]}],
        }
        image = {"type": "image", "data": "", "hash": "hash", "binary_data_base64": "DATA"}
        with patch("qq_official_adapter.codec.image_component", new=AsyncMock(return_value=image)) as download:
            message = await build_message(config(), "C2C_MESSAGE_CREATE", data, None)
        tree = next(part for part in message["raw_message"] if part["type"] == "forward")
        quoted = tree["data"][0]
        assert quoted["message_id"] == "official:123:quoted"
        assert quoted["content"][0]["data"]["target_message_id"] == "official:123:image-source"
        nested = next(part for part in quoted["content"] if part["type"] == "forward")
        assert image in nested["data"][0]["content"]
        assert nested["data"][0]["content"][0]["data"]["url"] == "https://example.qq.com/a.png"
        assert nested["data"][0]["user_nickname"] == "群友"
        download.assert_awaited_once()
        markers = [part["data"]["type"] for part in message["raw_message"] if part["type"] == "dict"]
        assert markers == ["official_message_source"]
    asyncio.run(run())


def test_reference_without_id_preserves_inline_media_and_marks_missing_link():
    async def run():
        data = {"id": "root", "author": {"id": "user"}, "content": "看看", "message_type": 103,
                "timestamp": "2026-10-23T02:21:13+08:00",
                "msg_elements": [{"content": "原消息", "attachments": [{"content_type": "image/gif", "url": "https://example.qq.com/a.gif"}]}]}
        image = {"type": "image", "data": "", "hash": "hash", "binary_data_base64": "DATA"}
        with patch("qq_official_adapter.codec.image_component", new=AsyncMock(return_value=image)):
            message = await build_message(config(), "C2C_MESSAGE_CREATE", data, None)
        assert not any(part["type"] == "reply" for part in message["raw_message"])
        tree = next(part for part in message["raw_message"] if part["type"] == "forward")
        assert image in tree["data"][0]["content"]
        marker = next(part for part in message["raw_message"] if part["type"] == "dict")
        assert marker["data"]["status"] == "reference_id_missing"
    asyncio.run(run())


def test_nested_and_top_level_images_share_one_download_budget():
    async def run():
        attachments = [{"content_type": "image/png", "url": f"https://example.qq.com/{i}.png"} for i in range(6)]
        data = {"id": "root", "author": {"id": "user"}, "content": "正文", "message_type": 103,
                "timestamp": "2026-10-23T02:21:13+08:00", "attachments": attachments,
                "msg_elements": [{"content": "引用", "attachments": attachments}]}
        image = {"type": "image", "data": "", "hash": "hash", "binary_data_base64": "DATA"}
        with patch("qq_official_adapter.codec.image_component", new=AsyncMock(return_value=image)) as download:
            message = await build_message(config(), "C2C_MESSAGE_CREATE", data, None)
        assert download.await_count == 6
        assert "附件未预加载" in json.dumps(message, ensure_ascii=False)
        tree = next(part for part in message["raw_message"] if part["type"] == "forward")
        assert len([part for part in tree["data"][0]["content"] if part["type"] == "file"]) == 6
    asyncio.run(run())


def test_other_bot_mentions_do_not_trigger_self_detection_or_bypass_group_permissions():
    async def run():
        data = {"id": "msg", "group_openid": "group", "content": "<@OTHER> 你好",
                "timestamp": "2026-10-16T21:11:16+08:00", "author": {"id": "user"},
                "mentions": [{"id": "OTHER", "username": "其他机器人", "bot": True, "is_you": False}]}
        assert not event_allowed(config(), "GROUP_MESSAGE_CREATE", data)
        message = await build_message(config(receive_all=True), "GROUP_MESSAGE_CREATE", data, None)
        assert not message["is_at"] and not message["is_mentioned"]
        assert message["processed_plain_text"] == "@其他机器人 你好"
        data["mentions"][0]["is_you"] = True
        assert not event_allowed(config(groups=["other"]), "GROUP_MESSAGE_CREATE", data)
    asyncio.run(run())


def test_official_face_ext_is_a_readable_label_in_current_and_quoted_messages():
    async def run():
        tag = '<faceType=4,faceId="",ext="eyJ0ZXh0IjoiW+mipOaKll0ifQ==">'
        data = {"id": "face-message", "group_openid": "group", "content": "<@BOT> " + tag,
                "timestamp": "2026-10-17T00:00:00+08:00", "author": {"id": "user"},
                "mentions": [{"id": "BOT", "is_you": True}]}
        message = await build_message(config(), "GROUP_MESSAGE_CREATE", data, None)
        assert message["processed_plain_text"] == "@毯毯 [QQ表情：颤抖]"
        assert message["is_at"]
        assert not message["is_picture"]  # No visual content was supplied by this event.
        data.update(content="你存了这个吗", message_type=103,
                    msg_elements=[{"author": {"username": "伊桑"}, "content": tag}])
        quoted = await build_message(config(), "GROUP_MESSAGE_CREATE", data, None)
        assert "伊桑：[QQ表情：颤抖]" in quoted["processed_plain_text"]
    asyncio.run(run())


@pytest.mark.parametrize("metadata", [[], {"text": []}, {"text": None}])
def test_face_ext_with_invalid_shape_has_an_explicit_fallback(metadata):
    encoded = base64.b64encode(json.dumps(metadata).encode()).decode()
    assert face_text(f'<faceType=4,faceId="",ext="{encoded}">') == "[QQ表情：未提供描述]"


def test_face_ext_malformed_and_empty_sticker_do_not_break_text_or_mentions():
    assert face_text('前<faceType=4,faceId="14",ext="!bad!">后') == "前[QQ表情：编号14]后"
    assert face_text('<faceType=6,faceId="0",ext="eyJ0ZXh0IjoiIn0=">') == "[表情包]"
    assert face_text("普通文字<@BOT>🙂") == "普通文字<@BOT>🙂"


def test_sticker_marker_routes_binary_to_emoji_collection_pipeline():
    async def run():
        data = {"id": "sticker", "group_openid": "group", "author": {"id": "user"},
                "timestamp": "2026-10-17T00:00:00+08:00",
                "content": '<faceType=6,faceId="0",ext="eyJ0ZXh0IjoiIn0=">',
                "attachments": [{"content_type": "image/gif", "url": "https://example.qq.com/image.gif"}]}
        image = {"type": "image", "data": "", "hash": "image-hash", "binary_data_base64": "IMAGE"}
        with patch("qq_official_adapter.codec.image_component", new=AsyncMock(return_value=image)) as fetch:
            message = await build_message(config(), "GROUP_MESSAGE_CREATE", data, None)
        fetch.assert_awaited_once_with(None, "https://example.qq.com/image.gif")
        assert message["is_emoji"]
        assert not message["is_picture"]
        assert {**image, "type": "emoji"} in message["raw_message"]
        assert "faceType" not in message["processed_plain_text"]
    asyncio.run(run())


def test_ordinary_image_is_not_registered_as_emoji_and_failed_download_is_not_saved():
    async def run():
        data = {"id": "image", "group_openid": "group", "author": {"id": "user"},
                "timestamp": "2026-10-17T00:00:00+08:00", "content": "普通图片",
                "attachments": [{"content_type": "image/png", "url": "https://example.qq.com/image.png"}]}
        image = {"type": "image", "data": "", "hash": "image-hash", "binary_data_base64": "IMAGE"}
        with patch("qq_official_adapter.codec.image_component", new=AsyncMock(return_value=image)):
            message = await build_message(config(), "GROUP_MESSAGE_CREATE", data, None)
        assert message["is_picture"]
        assert not message["is_emoji"]
        assert image in message["raw_message"]
        data["content"] = '<faceType=6,faceId="0",ext="eyJ0ZXh0IjoiIn0=">'
        failure = {"type": "text", "data": "[图片：下载失败或超时]"}
        with patch("qq_official_adapter.codec.image_component", new=AsyncMock(return_value=failure)):
            message = await build_message(config(), "GROUP_MESSAGE_CREATE", data, None)
        assert not message["is_emoji"]
        assert failure in message["raw_message"]
    asyncio.run(run())


def test_duplicate_event_is_not_routed_after_restart(tmp_path):
    async def run():
        gateway = SimpleNamespace(route_message=AsyncMock(return_value=True), update_state=AsyncMock())
        connection = OfficialConnection(config(receive_all=True), gateway,
                                        SimpleNamespace(info=lambda _: None, debug=lambda _: None), AsyncMock(), tmp_path)
        path = tmp_path / "state.sqlite"
        connection.state = OfficialState(path)
        event = {"op": 0, "s": 2, "t": "GROUP_AT_MESSAGE_CREATE", "d": {
            "id": "msg", "group_openid": "group", "content": "hi", "author": {"id": "user"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_scene": {"ext": ["msg_idx=REFIDX_original=="]},
        }}
        await connection._dispatch(event, None)
        assert connection.state.reply_target("group", False, "msg")["ref_idx"] == "REFIDX_original=="
        connection.state.close()
        connection.state = OfficialState(path)
        event["t"] = "GROUP_MESSAGE_CREATE"
        await connection._dispatch(event, None)
        assert gateway.route_message.await_count == 1
        assert connection.state.get("gateway")["seq"] == 2
        connection.state.close()
    asyncio.run(run())


def test_quote_indexes_resolve_incoming_and_nested_references_without_mutating_source(tmp_path):
    async def run():
        state = OfficialState(tmp_path / "quotes.sqlite")
        state.remember("picture", "group", False, time.time(), ref_idx="REFIDX_picture==")
        state.remember("elsewhere", "other", False, time.time(), ref_idx="REFIDX_picture==")
        data = {"id": "question", "group_openid": "group", "author": {"id": "user"},
                "content": "看这张图", "message_type": 103, "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_scene": {"ext": ["ref_msg_idx=REFIDX_picture=="]},
                "msg_elements": [{"message_type": 103, "msg_idx": "REFIDX_picture==", "content": ""}]}
        enriched = state.resolve_event_references("GROUP_AT_MESSAGE_CREATE", data)
        assert "message_reference" not in data and "message_id" not in data["msg_elements"][0]
        assert enriched["message_reference"] == {"message_id": "picture"}
        assert enriched["msg_elements"][0]["message_id"] == "picture"
        message = await build_message(config(), "GROUP_AT_MESSAGE_CREATE", enriched, None)
        assert message["raw_message"][0]["type"] == "reply"
        assert message["raw_message"][0]["data"]["target_message_id"] == "official:123:picture"
        assert not message["is_picture"]  # Resolving an ID does not fabricate an attachment.
        state.close()
    asyncio.run(run())


def test_quote_index_ambiguity_missing_and_private_scope_are_not_guessed(tmp_path):
    state = OfficialState(tmp_path / "scope.sqlite")
    state.remember("one", "group", False, time.time(), ref_idx="same")
    state.remember("two", "group", False, time.time(), ref_idx="same")
    state.remember("dm", "user", True, time.time(), ref_idx="private-only")
    for index in ["same", "missing", "private-only"]:
        data = {"group_openid": "group", "author": {"id": "user"},
                "message_scene": {"ext": ["ref_msg_idx=" + index]}}
        assert "message_reference" not in state.resolve_event_references("GROUP_AT_MESSAGE_CREATE", data)
    private = {"author": {"user_openid": "user"}, "message_scene": {"ext": ["ref_msg_idx=private-only"]}}
    assert state.resolve_event_references("C2C_MESSAGE_CREATE", private)["message_reference"]["message_id"] == "dm"
    private["message_reference"] = {"message_id": "explicit"}
    assert state.resolve_event_references("C2C_MESSAGE_CREATE", private)["message_reference"]["message_id"] == "explicit"
    state.close()


def test_gateway_resolves_quote_index_before_routing_and_keeps_original_journal(tmp_path):
    async def run():
        gateway = SimpleNamespace(route_message=AsyncMock(return_value=True), update_state=AsyncMock())
        journal = AsyncMock()
        connection = OfficialConnection(config(), gateway, SimpleNamespace(debug=lambda _: None), journal, tmp_path)
        connection.state = OfficialState(tmp_path / "route.sqlite")
        connection.state.remember("original-picture", "group", False, time.time(), ref_idx="picture-index==")
        data = {"id": "question", "group_openid": "group", "author": {"id": "user"},
                "content": "看图", "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_scene": {"ext": ["ref_msg_idx=picture-index=="]}}
        await connection._dispatch({"t": "GROUP_AT_MESSAGE_CREATE", "d": data}, None)
        message = gateway.route_message.call_args.args[1]
        assert message["raw_message"][0]["data"]["target_message_id"] == "official:123:original-picture"
        assert "message_reference" not in journal.call_args.args[1]["data"]
        connection.state.close()
    asyncio.run(run())


def test_send_checks_expiry_cross_group_and_persists_reply_sequence(tmp_path):
    async def run():
        connection = OfficialConnection(config(), SimpleNamespace(), SimpleNamespace(), None, tmp_path)
        connection.state = OfficialState(tmp_path / "send.sqlite")
        connection.status["status"] = "online"
        connection.api = SimpleNamespace(request=AsyncMock(side_effect=[{"id": "sent1"}, {"id": "sent2"}]),
                                         target_path=OfficialAPI.target_path)
        connection.state.remember("msg", "group", False, time.time(), ref_idx="REFIDX_user")
        message = {"raw_message": [{"type": "reply", "data": {"target_message_id": "official:123:msg"}},
                                   {"type": "text", "data": "你好"}],
                   "message_info": {"group_info": {"group_id": "official:123:group"}}}
        assert await connection.send(message, {}) == "official:123:sent1"
        await connection.send(message, {})
        assert connection.api.request.await_args_list[0].args[2]["msg_seq"] == 1
        assert connection.api.request.await_args_list[0].args[2]["message_reference"] == {"message_id": "REFIDX_user"}
        assert connection.api.request.await_args_list[1].args[2]["msg_seq"] == 2
        message["message_info"]["group_info"]["group_id"] = "official:123:other"
        with pytest.raises(ValueError, match="引用消息不属于"):
            await connection.send(message, {})
        message["raw_message"] = [{"type": "text", "data": "hi"}]
        with pytest.raises(ValueError, match="被动回复时限"):
            await connection.send(message, {})
        message["message_info"]["group_info"]["group_id"] = "official:999:group"
        with pytest.raises(ValueError, match="跨端"):
            await connection.send(message, {})
        assert connection.api.request.await_count == 2
        connection.state.close()
    asyncio.run(run())


def test_reply_limit_survives_restart(tmp_path):
    path = tmp_path / "reply.sqlite"
    state = OfficialState(path)
    for expected in range(1, 6):
        assert state.next_reply("msg", 5) == expected
    state.close()
    state = OfficialState(path)
    with pytest.raises(ValueError, match="次数上限"):
        state.next_reply("msg", 5)
    state.close()


@pytest.mark.parametrize("private", [False, True])
def test_typo_correction_quotes_own_ref_idx_not_delivery_id(tmp_path, private):
    async def run():
        path = tmp_path / "self-quote.sqlite"
        connection = OfficialConnection(config(allow_private=True), SimpleNamespace(), SimpleNamespace(), None, tmp_path)
        connection.state = OfficialState(path)
        connection.status["status"] = "online"
        connection.state.remember("incoming-delivery", "target", private, time.time(), ref_idx="REFIDX_incoming")
        connection.api = SimpleNamespace(request=AsyncMock(side_effect=[
            {"id": "ROBOT1.0_sent", "ext_info": {"ref_idx": "REFIDX_own"}},
            {"id": "ROBOT1.0_correction", "ext_info": {"ref_idx": "REFIDX_correction"}},
        ]), target_path=OfficialAPI.target_path)
        info = {"additional_config": {"platform_io_target_user_id": "official:123:target"}} if private else {
            "group_info": {"group_id": "official:123:target"}}
        message = {"message_info": info, "raw_message": [{"type": "text", "data": "全往"}]}
        sent_id = await connection.send(message, {})
        # 引用索引重启后仍可用，且不能拿其他群/私聊的索引冒充。
        connection.state.close()
        connection.state = OfficialState(path)
        assert connection.state.reply_target("other", private, "ROBOT1.0_sent") is None
        message["raw_message"] = [{"type": "reply", "data": {"target_message_id": sent_id}},
                                  {"type": "text", "data": "网"}]
        await connection.send(message, {})
        payload = connection.api.request.await_args_list[1].args[2]
        assert payload["message_reference"] == {"message_id": "REFIDX_own"}
        assert payload["msg_id"] == "incoming-delivery"
        assert payload["msg_seq"] == 2
        assert payload["content"] == "网"
        connection.state.close()
    asyncio.run(run())


def test_missing_quote_index_is_not_sent_as_an_expired_quote(tmp_path):
    async def run():
        connection = OfficialConnection(config(), SimpleNamespace(), SimpleNamespace(), None, tmp_path)
        connection.state = OfficialState(tmp_path / "missing-index.sqlite")
        connection.status["status"] = "online"
        connection.api = SimpleNamespace(request=AsyncMock())
        connection.state.remember("old", "group", False, time.time(), False)
        message = {"message_info": {"group_info": {"group_id": "official:123:group"}},
                   "raw_message": [{"type": "reply", "data": "official:123:old"}, {"type": "text", "data": "网"}]}
        with pytest.raises(ValueError, match="缺少官方引用索引"):
            await connection.send(message, {})
        connection.api.request.assert_not_awaited()
        connection.state.close()
    asyncio.run(run())


@pytest.mark.parametrize("private", [False, True])
def test_continuation_omits_passive_group_mention_but_keeps_private_reply(tmp_path, private):
    async def run():
        connection = OfficialConnection(config(allow_private=True, allow_proactive=True),
                                        SimpleNamespace(), SimpleNamespace(), None, tmp_path)
        connection.state = OfficialState(tmp_path / "continuation.sqlite")
        connection.status["status"] = "online"
        connection.state.remember("source", "target", private, time.time(), ref_idx="REFIDX_source")
        connection.api = SimpleNamespace(request=AsyncMock(return_value={"id": "sent"}), target_path=OfficialAPI.target_path)
        extra = {"reply_continuation": True}
        info = {"additional_config": extra}
        if private:
            extra["platform_io_target_user_id"] = "official:123:target"
        else:
            info["group_info"] = {"group_id": "official:123:target"}
        message = {"message_info": info, "raw_message": [{"type": "text", "data": "怎么突然要吃我喵"}]}
        await connection.send(message, {})
        payload = connection.api.request.await_args.args[2]
        assert ("msg_id" in payload) is private
        assert ("msg_seq" in payload) is private
        assert "message_reference" not in payload
        assert payload["content"] == "怎么突然要吃我喵"
        connection.state.close()
    asyncio.run(run())


def test_continuation_does_not_bypass_proactive_permission(tmp_path):
    async def run():
        connection = OfficialConnection(config(), SimpleNamespace(), SimpleNamespace(), None, tmp_path)
        connection.state = OfficialState(tmp_path / "disabled-continuation.sqlite")
        connection.status["status"] = "online"
        connection.api = SimpleNamespace(request=AsyncMock())
        message = {"message_info": {"group_info": {"group_id": "official:123:group"},
                                    "additional_config": {"reply_continuation": True}},
                   "raw_message": [{"type": "text", "data": "第二段"}]}
        with pytest.raises(ValueError, match="开启官方端主动发送"):
            await connection.send(message, {})
        connection.api.request.assert_not_awaited()
        connection.state.close()
    asyncio.run(run())


@pytest.mark.parametrize("enabled", [False, True])
def test_first_event_uses_configured_proactive_policy_without_success_cache(tmp_path, enabled):
    async def run():
        gateway = SimpleNamespace(route_message=AsyncMock(return_value=True))
        connection = OfficialConnection(config(allow_proactive=enabled), gateway,
                                        SimpleNamespace(debug=lambda _: None), AsyncMock(), tmp_path)
        connection.state = OfficialState(tmp_path / "policy.sqlite")
        # An old account-wide result must not gate every group forever.
        connection.state.put("group_proactive_available", False)
        await connection._dispatch({"t": "GROUP_AT_MESSAGE_CREATE", "d": {
            "id": "fresh", "group_openid": "group", "content": "看看",
            "author": {"id": "user"}, "timestamp": datetime.now(timezone.utc).isoformat(),
        }}, None)
        extra = gateway.route_message.await_args.args[1]["message_info"]["additional_config"]
        assert extra["official_proactive_available"] is enabled
        connection.state.close()
    asyncio.run(run())


def test_actual_proactive_rejection_is_scoped_to_group_and_config_revision(tmp_path):
    async def run():
        gateway = SimpleNamespace(route_message=AsyncMock(return_value=True))
        connection = OfficialConnection(config(allow_proactive=True), gateway,
                                        SimpleNamespace(debug=lambda _: None), AsyncMock(), tmp_path)
        connection.state = OfficialState(tmp_path / "denied.sqlite")
        connection.status["status"] = "online"
        connection.api = SimpleNamespace(request=AsyncMock(side_effect=OfficialError(40034105, "拒绝")),
                                         target_path=OfficialAPI.target_path)
        message = {"message_info": {"group_info": {"group_id": "official:123:denied"},
                                    "additional_config": {"reply_continuation": True}},
                   "raw_message": [{"type": "text", "data": "第二段"}]}
        with pytest.raises(ValueError, match="官方发送失败"):
            await connection.send(message, {})
        assert not await connection._proactive_available("denied")
        assert await connection._proactive_available("other")
        with pytest.raises(ValueError, match="官方已拒绝当前群"):
            await connection.send(message, {})
        assert connection.api.request.await_count == 1

        await connection._dispatch({"t": "GROUP_AT_MESSAGE_CREATE", "d": {
            "id": "new-input", "group_openid": "denied", "content": "再试",
            "author": {"id": "user"}, "timestamp": datetime.now(timezone.utc).isoformat(),
        }}, None)
        extra = gateway.route_message.await_args.args[1]["message_info"]["additional_config"]
        assert extra["official_proactive_available"] is False

        connection.config["revision"] += 1
        assert await connection._proactive_available("denied")
        connection.api.request.side_effect = None
        connection.api.request.return_value = {"id": "sent"}
        await connection.send(message, {})
        assert "msg_id" not in connection.api.request.await_args.args[2]
        assert await connection._proactive_available("denied")
        connection.state.close()
    asyncio.run(run())


def test_reply_batch_reservation_does_not_send_partial_when_quota_is_short(tmp_path):
    state = OfficialState(tmp_path / "batch.sqlite")
    assert state.reserve_replies("msg", 5, 4) == [1, 2, 3, 4]
    with pytest.raises(ValueError, match="次数上限"):
        state.reserve_replies("msg", 5, 2)
    assert state.next_reply("msg", 5) == 5
    state.close()


def test_unsupported_outbound_component_fails_explicitly():
    with pytest.raises(ValueError, match="尚未支持"):
        outbound_parts({"raw_message": [{"type": "forward", "data": []}]})


def animated_gif():
    output = BytesIO()
    frames = [Image.new("RGB", (16, 16), color) for color in ("red", "blue")]
    frames[0].save(output, format="GIF", save_all=True, append_images=frames[1:], duration=[100, 200], loop=0)
    return output.getvalue()


def test_gif_upload_preserves_bytes_frames_and_duration():
    original = animated_gif()
    raw, filename = prepare_upload_image(original)
    assert raw == original
    assert filename == "tantan.gif"
    with Image.open(BytesIO(raw)) as image:
        assert image.n_frames == 2
        image.seek(1)
        assert image.info["duration"] == 200


def test_animated_webp_upload_preserves_animation_as_gif():
    frames = [Image.new("RGB", (16, 16), color) for color in ("red", "blue")]
    output = BytesIO()
    frames[0].save(output, format="WEBP", save_all=True, append_images=frames[1:], duration=[100, 200], lossless=True)
    raw, filename = prepare_upload_image(output.getvalue())
    assert filename == "tantan.gif"
    with Image.open(BytesIO(raw)) as image:
        assert image.n_frames == 2
        image.seek(1)
        assert image.info["duration"] == 200
        assert image.convert("RGB").getpixel((0, 0)) == (0, 0, 255)


@pytest.mark.parametrize("private", [False, True])
def test_send_animated_emoji_uploads_gif_instead_of_first_frame(tmp_path, private):
    async def run():
        connection = OfficialConnection(config(allow_private=True), SimpleNamespace(), SimpleNamespace(), None, tmp_path)
        connection.state = OfficialState(tmp_path / "gif-send.sqlite")
        connection.status["status"] = "online"
        connection.api = SimpleNamespace(
            upload=AsyncMock(return_value={"file_info": "gif-file"}),
            request=AsyncMock(return_value={"id": "sent-gif"}), target_path=OfficialAPI.target_path,
        )
        connection.state.remember("msg", "target", private, time.time())
        original = animated_gif()
        info = {"additional_config": {"platform_io_target_user_id": "official:123:target"}} if private else {
            "group_info": {"group_id": "official:123:target"}
        }
        message = {"message_info": info, "raw_message": [
            {"type": "emoji", "data": "", "binary_data_base64": base64.b64encode(original).decode("ascii")}
        ]}
        try:
            assert await connection.send(message, {}) == "official:123:sent-gif"
            connection.api.upload.assert_awaited_once_with("target", private, original, "tantan.gif")
            payload = connection.api.request.await_args.args[2]
            assert payload["media"] == {"file_info": "gif-file"}
            assert payload["msg_type"] == 7
        finally:
            connection.state.close()
    asyncio.run(run())


def test_gateway_identify_resume_and_invalid_session_reset(tmp_path):
    class Socket:
        def __init__(self, events, close_code=4009):
            self.events, self.close_code, self.frames = events, close_code, []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def receive_json(self, **kwargs):
            return {"op": 10, "d": {"heartbeat_interval": 45000}}

        async def send_json(self, frame):
            self.frames.append(frame)

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self.events:
                raise StopAsyncIteration
            event = self.events.pop(0)
            return SimpleNamespace(type=aiohttp.WSMsgType.TEXT, json=lambda: event)

    async def run():
        gateway = SimpleNamespace(update_state=AsyncMock(), route_message=AsyncMock(return_value=True))
        connection = OfficialConnection(config(), gateway, SimpleNamespace(), AsyncMock(), tmp_path)
        connection.state = OfficialState(tmp_path / "gateway.sqlite")
        connection.api = SimpleNamespace(token=AsyncMock(return_value="TOKEN"))
        connection._gateway_url, connection._gateway_expires = "wss://example.qq.com", time.time() + 600
        socket = Socket([{"op": 0, "s": 1, "t": "READY", "d": {"session_id": "session", "user": {"id": "bot"}}}])
        session = SimpleNamespace(ws_connect=lambda *args, **kwargs: socket)
        assert await connection._connect(session) == 4009
        assert socket.frames[0] == {"op": 2, "d": {"token": "QQBot TOKEN", "intents": 1 << 25, "shard": [0, 1]}}
        assert connection.status["status"] == "online"
        assert connection.state.get("gateway") == {"session_id": "session", "seq": 1}
        socket = Socket([{"op": 0, "s": 2, "t": "RESUMED", "d": {}}])
        await connection._connect(session)
        assert socket.frames[0] == {"op": 6, "d": {"token": "QQBot TOKEN", "session_id": "session", "seq": 1}}
        socket = Socket([{"op": 9, "d": False}])
        assert await connection._connect(session) == 4006
        assert connection.state.get("gateway") == {}
        connection.state.close()
    asyncio.run(run())
