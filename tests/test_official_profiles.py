"""Official identity data stays scoped to an app and real event fields."""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/maibot_plugin"))
from qq_official_adapter.codec import build_message
from qq_official_adapter.profiles import avatar_url, enrich_event_profiles
from qq_official_adapter.state import OfficialState
from qq_official_adapter.plugin import QQOfficialPlugin


def test_profiles_survive_restart_and_missing_event_fields(tmp_path):
    path = tmp_path / "profiles.sqlite"
    state = OfficialState(path)
    event = {"author": {"member_openid": "user", "username": "昵称", "member_name": "群名片",
                        "avatar": "https://q.qlogo.cn/avatar.png"},
             "group_openid": "group", "group_name": "Underline",
             "group_avatar": "https://p.qpic.cn/group.png"}
    enrich_event_profiles(state, "GROUP_MESSAGE_CREATE", event)
    state.close()
    state = OfficialState(path)
    data = enrich_event_profiles(state, "GROUP_MESSAGE_CREATE", {
        "author": {"member_openid": "user"}, "group_openid": "group",
        "id": "message", "timestamp": "2026-10-21T12:00:00+08:00",
    })
    message = asyncio.run(build_message({"app_id": "123", "id": "endpoint", "name": "毯毯"},
                                        "GROUP_MESSAGE_CREATE", data, None))
    info = message["message_info"]
    assert info["user_info"]["user_nickname"] == "昵称"
    assert info["user_info"]["user_cardname"] == "群名片"
    assert info["group_info"]["group_name"] == "Underline"
    assert info["additional_config"]["user_avatar_url"].startswith("https://q.qlogo.cn/")
    assert info["additional_config"]["group_avatar_url"].endswith("group.png")
    other = enrich_event_profiles(state, "GROUP_MESSAGE_CREATE", {
        "author": {"member_openid": "user"}, "group_openid": "other",
    })
    assert "member_name" not in other["author"]
    assert "group_name" not in other
    state.close()


def test_private_profile_and_missing_fields_do_not_invent_data(tmp_path):
    state = OfficialState(tmp_path / "state.sqlite")
    enrich_event_profiles(state, "C2C_MESSAGE_CREATE", {"author": {"user_openid": "private", "username": "朋友"}})
    data = enrich_event_profiles(state, "C2C_MESSAGE_CREATE", {"author": {"user_openid": "private"}})
    assert data["author"]["username"] == "朋友"
    assert "avatar" not in data["author"]
    state.close()


def test_mentioned_members_reuse_group_scoped_names_only(tmp_path):
    state = OfficialState(tmp_path / "mention-profiles.sqlite")
    enrich_event_profiles(state, "GROUP_MESSAGE_CREATE", {
        "group_openid": "group-a",
        "author": {"member_openid": "target", "username": "昵称", "member_name": "群名片"},
    })
    enriched = enrich_event_profiles(state, "GROUP_AT_MESSAGE_CREATE", {
        "group_openid": "group-a", "mentions": [{"id": "target"}],
    })
    assert enriched["mentions"][0]["username"] == "昵称"
    assert enriched["mentions"][0]["member_name"] == "群名片"
    other_group = enrich_event_profiles(state, "GROUP_AT_MESSAGE_CREATE", {
        "group_openid": "group-b", "mentions": [{"id": "target"}],
    })
    assert "member_name" not in other_group["mentions"][0]
    state.close()


def test_avatar_urls_are_validated():
    for value in (None, "http://q.qlogo.cn/x", "https://example.com/x", "https://qq.com:bad/x",
                  "https://qq.com.evil.example/x", "https://user:secret@qq.com/x"):
        assert avatar_url(value) == ""


def test_avatar_api_returns_cached_url_and_enforces_app_scope(tmp_path):
    async def run():
        state = OfficialState(tmp_path / "api.sqlite")
        enrich_event_profiles(state, "C2C_MESSAGE_CREATE", {"author": {
            "user_openid": "user", "username": "朋友", "avatar": "https://q.qlogo.cn/u.png",
        }})
        async def read(method, *args):
            return getattr(state, method)(*args)
        plugin = object.__new__(QQOfficialPlugin)
        plugin._connections = {"endpoint": (SimpleNamespace(config={"app_id": "123"}, state=state, _state=read), None)}
        result = await plugin.get_avatar("qq_official", "official:123:user", account_id="123", scope="endpoint")
        assert result["status"] == "available" and result["url"].endswith("u.png")
        assert (await plugin.get_avatar("qq_official", "official:other:user"))["status"] == "missing"
        assert (await plugin.get_avatar("qq_official", "official:123:user", scope="other"))["status"] == "missing"
        profile = await plugin.get_profile("qq_official", "official:123:user")
        assert profile["name"] == "朋友"
        assert profile["source"] == "official_event"
        state.close()
    asyncio.run(run())
