"""Connection settings never expose credentials or mutate the existing NapCat data."""

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from qqbot.endpoint_routes import make_endpoint_router
from qqbot.endpoints import Endpoints
from qqbot.store import Store
from qqbot.tools import ToolRegistry
from unittest.mock import patch


def test_official_config_is_opt_in_and_secret_is_write_only(tmp_path):
    store = Store(tmp_path / "ends.sqlite")
    registry = Endpoints(store)
    public = registry.save({"app_id": "123", "app_secret": "secret-value"})
    assert public["enabled"] is False
    assert public["runtime"]["status"] == "disabled"
    assert "secret-value" not in json.dumps(registry.configs())
    assert public["secret_configured"] is True
    registry.save({"name": "changed", "app_secret": ""}, public["id"])
    assert registry.get(public["id"])["app_secret"] == "secret-value"
    assert registry.get(public["id"])["name"] == "changed"
    store.close()


def test_status_needs_matching_revision_and_recent_heartbeat(tmp_path):
    now = [1000.0]
    store = Store(tmp_path / "ends.sqlite", clock=lambda: now[0])
    registry = Endpoints(store)
    public = registry.save({"app_id": "123", "app_secret": "secret", "enabled": True})
    assert public["runtime"]["status"] == "pending"
    assert not registry.report(public["id"], {"revision": 0, "status": "online"})
    assert registry.report(public["id"], {"revision": 1, "status": "online", "app_secret": "drop"})
    assert registry.configs()[0]["runtime"]["status"] == "online"
    assert "app_secret" not in registry.configs()[0]["runtime"]
    now[0] += 50
    assert registry.configs()[0]["runtime"]["status"] == "offline"
    assert registry.save({"enabled": False}, public["id"])["runtime"]["status"] == "disabled"
    store.close()


def test_bridge_is_authenticated_and_management_checks_origin(tmp_path):
    store = Store(tmp_path / "ends.sqlite")
    app = FastAPI()
    app.include_router(make_endpoint_router(store, lambda token: token == "Bearer test-token"))
    client = TestClient(app)
    assert client.get("/api/bridge/endpoints").status_code == 401
    assert client.post("/api/endpoints", json={"name": "test"}, headers={"origin": "https://elsewhere.invalid"}).status_code == 403
    public = client.post("/api/endpoints", json={"name": "test", "app_id": "123", "app_secret": "hidden"}).json()
    assert public["secret_configured"] is True
    assert "hidden" not in client.get("/api/endpoints").text
    response = client.get("/api/bridge/endpoints", headers={"Authorization": "Bearer test-token"})
    assert response.json()["endpoints"][0]["app_secret"] == "hidden"
    assert client.post("/api/endpoints", json={"app_id": "123"}).status_code == 400
    assert client.post("/api/endpoints", json={"enabled": True}).status_code == 400
    assert client.post("/api/endpoints", json={"endpoint": "http://remote.invalid"}).status_code == 422
    store.close()


def test_napcat_enable_only_patches_adapter_switch(tmp_path, monkeypatch):
    calls = []
    from qqbot import endpoint_routes
    monkeypatch.setattr(endpoint_routes, "webui_request", lambda *args: calls.append(args) or {"success": True})
    store = Store(tmp_path / "ends.sqlite")
    app = FastAPI()
    app.include_router(make_endpoint_router(store, lambda _: False))
    response = TestClient(app).put("/api/endpoints/napcat/settings", json={"enabled": False})
    assert response.status_code == 200
    assert calls == [("/plugins/config/maibot-team.napcat-adapter", {"config": {"plugin": {"enabled": False}}}, "PUT")]
    store.close()


def test_official_source_is_scoped_and_deduplicated(tmp_path):
    store = Store(tmp_path / "ends.sqlite")
    end = Endpoints(store).save({"app_id": "123", "app_secret": "s", "enabled": True, "groups": ["group"]})
    app = FastAPI()
    app.include_router(make_endpoint_router(store, lambda _: True))
    client = TestClient(app)
    event = {"event_type": "GROUP_AT_MESSAGE_CREATE", "data": {
        "id": "msg", "group_openid": "group", "content": "test",
        "author": {"id": "user", "username": "群友"}, "timestamp": "2026-10-16T12:00:00+08:00",
    }}
    url = f"/api/bridge/endpoints/{end['id']}/event"
    assert client.post(url, json=event).json()["accepted"] is True
    assert client.post(url, json=event).json()["accepted"] is False
    rows = store.rows("SELECT * FROM messages")
    assert len(rows) == 1
    assert rows[0]["group_id"] == "official:123:group"
    assert rows[0]["user_id"] == "official:123:user"
    event["data"]["group_openid"] = "other"
    assert client.post(url, json=event).status_code == 400
    store.close()


def test_remove_endpoint_requires_disabled_and_preserves_source_messages(tmp_path):
    store = Store(tmp_path / "ends.sqlite")
    registry = Endpoints(store)
    end = registry.save({"app_id": "123", "app_secret": "s", "enabled": True})
    store.append({"post_type": "message", "message_type": "group", "group_id": "official:123:group",
                  "message_id": "msg", "user_id": "user", "message": "正文"})
    app = FastAPI()
    app.include_router(make_endpoint_router(store, lambda _: True))
    client = TestClient(app)
    assert client.delete("/api/endpoints/" + end["id"]).status_code == 400
    registry.save({"enabled": False}, end["id"])
    assert client.delete("/api/endpoints/" + end["id"]).json()["history_preserved"] is True
    assert registry.configs() == []
    assert len(store.rows("SELECT * FROM messages")) == 1
    store.close()


def test_bound_group_reads_old_chat_and_only_shared_knowledge(tmp_path):
    store = Store(tmp_path / "bound.sqlite")
    endpoints = Endpoints(store)
    end = endpoints.save({"app_id": "123", "app_secret": "secret", "enabled": True,
                          "groups": ["one", "two"], "group_bindings": {"one": "924"},
                          "knowledge_groups": {"one": ["106"]}})
    for group in ("924", "106", "999"):
        store.append({"post_type": "message", "message_type": "group", "group_id": group,
                      "message_id": "1", "user_id": "user", "message": "block_transformer chat"})
        store.write("INSERT INTO memory_state VALUES (?,?,?,?,?,?,?,?,?)",
                    (group + ":trick", group, "related", "trick", "user",
                     "block_transformer knowledge", "[]", "{}", 1))
    task = store.create_task("official:123:one", "maibot", "request", "query")
    registry = ToolRegistry(store)
    assert endpoints.read_groups(task["group_id"], knowledge=True) == ["official:123:one", "924", "106"]
    chat = registry.execute(task, "search_chat", {"keyword": "block_transformer"})["messages"]
    assert {row["group_id"] for row in chat} == {"924"}
    with patch("qqbot.docs.library") as docs:
        docs.return_value.search.return_value = []
        hits = registry.execute(task, "search_knowledge", {"queries": ["block_transformer"]})["results"]
    assert {row["group_id"] for row in hits} == {"924", "106"}
    assert not any(row["label"] == "聊天" and row["group_id"] == "106" for row in hits)
    assert store.task(task["id"])["group_id"] == "official:123:one"
    assert "error" in registry.execute(task, "run_command", {"command": "whoami"})
    assert endpoints.read_groups("official:123:two", knowledge=True) == ["official:123:two"]
    assert endpoints.read_groups("official:456:one", knowledge=True) == ["official:456:one"]
    assert endpoints.read_groups("official:123:unknown", knowledge=True) == ["official:123:unknown"]
    endpoints.save({"enabled": False}, end["id"])
    assert endpoints.read_groups(task["group_id"], knowledge=True) == ["official:123:one"]
    store.close()


def test_group_bindings_reject_invalid_sources(tmp_path):
    import pytest

    store = Store(tmp_path / "invalid.sqlite")
    for binding in ({"one": "official:123:two"}, {"one": ["123"]}):
        with pytest.raises(ValueError, match="数字群号"):
            Endpoints(store).save({"group_bindings": binding})
    with pytest.raises(ValueError, match="数字群号"):
        Endpoints(store).save({"knowledge_groups": {"one": "123"}})
    store.close()
