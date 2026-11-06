"""Local UI and authenticated plugin configuration for QQ connections."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from .endpoints import Endpoints
from .maibot import webui_port, webui_request

NAPCAT_PLUGIN = "maibot-team.napcat-adapter"


class OfficialSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(default="官方 QQ 机器人", min_length=1, max_length=80)
    app_id: str = Field(default="", max_length=32)
    app_secret: str = Field(default="", max_length=256)
    enabled: bool = False
    receive_all: bool = False
    allow_private: bool = False
    allow_proactive: bool = False
    groups: list[str] = Field(default_factory=list, max_length=200)
    private_users: list[str] = Field(default_factory=list, max_length=200)
    group_bindings: dict[str, str] = Field(default_factory=dict, max_length=200)
    knowledge_groups: dict[str, list[str]] = Field(default_factory=dict, max_length=200)


class RuntimeStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int
    status: Literal["connecting", "online", "offline", "error", "disabled"]
    error: str = Field(default="", max_length=300)
    bot_id: str = Field(default="", max_length=128)
    received: int = 0
    sent: int = 0
    last_event_at: float = 0
    last_sent_at: float = 0


class NapCatSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool


class OfficialEvent(BaseModel):
    event_type: Literal["GROUP_AT_MESSAGE_CREATE", "GROUP_MESSAGE_CREATE", "C2C_MESSAGE_CREATE"]
    data: dict


def make_endpoint_router(store, plugin_authorized):
    registry = Endpoints(store)
    router = APIRouter()

    def local_write(request: Request):
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
            raise HTTPException(403, "管理操作必须从本机管理页面发起")

    def bridge_auth(request: Request):
        if not plugin_authorized(request.headers.get("authorization", "")):
            raise HTTPException(401, "插件 token 无效")

    @router.get("/api/endpoints")
    def list_endpoints():
        last_poll = store.get_state("endpoint:bridge", {}).get("updated", 0)
        return {"endpoints": registry.configs(), "maibot_url": f"http://127.0.0.1:{webui_port()}",
                "adapter_connected": bool(last_poll and store.clock() - last_poll < 45)}

    @router.post("/api/endpoints")
    def create_endpoint(settings: OfficialSettings, request: Request):
        local_write(request)
        try:
            return registry.save(settings.model_dump())
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @router.put("/api/endpoints/{endpoint_id}")
    def update_endpoint(endpoint_id: str, settings: OfficialSettings, request: Request):
        local_write(request)
        try:
            return registry.save(settings.model_dump(), endpoint_id)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @router.get("/api/endpoints/napcat/status")
    def napcat_status():
        try:
            config = webui_request(f"/plugins/config/{NAPCAT_PLUGIN}").get("config", {})
            chat = config.get("chat", {})
            return {
                "id": "napcat", "kind": "napcat", "name": "现有 NapCat 接入",
                "enabled": config.get("plugin", {}).get("enabled", True),
                "groups": chat.get("group_list", []),
                "private_users": chat.get("private_list", []),
                "group_list_type": chat.get("group_list_type"),
                "status": "configured" if config.get("plugin", {}).get("enabled", True) else "disabled",
                "management_url": f"http://127.0.0.1:{webui_port()}",
                "note": "已读取麦麦适配器配置；QQ 在线状态请在 NapCat 查看",
            }
        except ValueError as exc:
            return {"id": "napcat", "status": "unavailable", "error": str(exc)}

    @router.delete("/api/endpoints/{endpoint_id}")
    def remove_endpoint(endpoint_id: str, request: Request):
        local_write(request)
        try:
            registry.remove(endpoint_id)
            return {"removed": True, "history_preserved": True}
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @router.put("/api/endpoints/napcat/settings")
    def napcat_settings(settings: NapCatSettings, request: Request):
        local_write(request)
        try:
            return webui_request(f"/plugins/config/{NAPCAT_PLUGIN}",
                                 {"config": {"plugin": {"enabled": settings.enabled}}}, "PUT")
        except ValueError as exc:
            raise HTTPException(502, str(exc)) from exc

    @router.get("/api/bridge/endpoints")
    def bridge_configs(request: Request):
        bridge_auth(request)
        store.set_state("endpoint:bridge", {"updated": store.clock()})
        return {"endpoints": registry.configs(private=True)}

    @router.post("/api/bridge/endpoints/{endpoint_id}/status")
    def bridge_status(endpoint_id: str, status: RuntimeStatus, request: Request):
        bridge_auth(request)
        try:
            return {"accepted": registry.report(endpoint_id, status.model_dump())}
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @router.post("/api/bridge/endpoints/{endpoint_id}/event")
    def bridge_event(endpoint_id: str, event: OfficialEvent, request: Request):
        bridge_auth(request)
        try:
            from datetime import datetime
            config = registry.get(endpoint_id)
            data = event.data
            if not config["enabled"]:
                raise ValueError("官方端已停用")
            if event.event_type == "C2C_MESSAGE_CREATE":
                return {"accepted": True, "note": "私聊正文由麦麦独立保存"}
            group = str(data["group_openid"])
            if config["groups"] and group not in config["groups"]:
                raise ValueError("群不在官方端允许名单里")
            author = data["author"]
            uid = str(author.get("member_openid") or author["id"])
            source = {
                "post_type": "message", "message_type": "group",
                "group_id": f"official:{config['app_id']}:{group}",
                "message_id": f"official:{config['app_id']}:{data['id']}",
                "user_id": f"official:{config['app_id']}:{uid}",
                "self_id": config["app_id"],
                "time": datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")).timestamp(),
                "sender": {"nickname": author.get("username") or uid},
                "message": [{"type": "text", "data": {"text": str(data.get("content") or "")}}],
                "official_source": data,
            }
            return {"accepted": store.append(source)}
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(400, "官方来源事件无效或未获授权") from exc

    return router
