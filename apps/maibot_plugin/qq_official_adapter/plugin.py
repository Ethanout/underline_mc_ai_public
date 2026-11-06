"""MaiBot gateway, configured by the existing Underline local management service."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiohttp
from maibot_sdk import API, Field, MaiBotPlugin, MessageGateway, PluginConfigBase

from .codec import GATEWAY, PLATFORM, raw_identity
from .profiles import profile_key
from .runtime import OfficialConnection


class PluginSection(PluginConfigBase):
    enabled: bool = Field(default=True, description="启用官方端管理连接；具体机器人在统一管理页启用")
    config_version: str = Field(default="1.0.0", description="配置版本")


class ServiceSection(PluginConfigBase):
    service_url: str = Field(default="http://127.0.0.1:18787", description="统一端管理服务地址，仅本机回环")
    token_file: str = Field(default="", description="管理服务插件 token 文件的绝对路径")
    state_dir: str = Field(default="data/qq_official_adapter", description="官方端断线游标和去重数据库目录")


class OfficialConfig(PluginConfigBase):
    plugin: PluginSection = Field(default_factory=PluginSection)
    service: ServiceSection = Field(default_factory=ServiceSection)


class QQOfficialPlugin(MaiBotPlugin):
    config_model = OfficialConfig

    def __init__(self):
        super().__init__()
        self._manager = None
        self._connections = {}
        self._session = None

    async def on_load(self):
        self._manager = asyncio.create_task(self._manage(), name="qq-official-manager")

    async def on_unload(self):
        if self._manager:
            self._manager.cancel()
            await asyncio.gather(self._manager, return_exceptions=True)
            self._manager = None
        await self._stop_all()

    async def on_config_update(self, scope, config_data, version):
        if scope == "self":
            await self.on_unload()
            self.set_plugin_config(config_data)
            await self.on_load()

    async def _bridge(self, path, payload=None):
        config = self.config.service
        parsed = urlparse(config.service_url)
        if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("统一端管理地址必须是本机 HTTP 服务")
        token = await asyncio.to_thread(Path(config.token_file).read_text, encoding="utf-8")
        token = token.strip()
        if not token:
            raise ValueError("插件 token 文件为空")
        async with self._session.request(
            "POST" if payload is not None else "GET", config.service_url.rstrip("/") + path,
            json=payload, headers={"Authorization": "Bearer " + token},
        ) as response:
            if response.status != 200:
                raise ValueError(f"统一端管理接口返回 HTTP {response.status}")
            return await response.json()

    async def _journal(self, endpoint_id, event):
        await self._bridge(f"/api/bridge/endpoints/{endpoint_id}/event", event)

    async def _stop(self, endpoint_id):
        connection, task = self._connections.pop(endpoint_id)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    async def _stop_all(self):
        for endpoint_id in list(self._connections):
            await self._stop(endpoint_id)

    async def _manage(self):
        failures = 0
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), trust_env=False) as session:
            self._session = session
            try:
                while True:
                    try:
                        if not self.config.plugin.enabled:
                            await self._stop_all()
                            await asyncio.sleep(10)
                            continue
                        configs = (await self._bridge("/api/bridge/endpoints"))["endpoints"]
                        desired = {item["id"]: item for item in configs if item["enabled"]}
                        for endpoint_id, (connection, _) in list(self._connections.items()):
                            if endpoint_id not in desired or desired[endpoint_id]["revision"] != connection.config["revision"]:
                                await self._stop(endpoint_id)
                        for endpoint_id, config in desired.items():
                            if endpoint_id not in self._connections:
                                connection = OfficialConnection(
                                    config, self.ctx.gateway, self.ctx.logger, self._journal, self.config.service.state_dir,
                                )
                                task = asyncio.create_task(connection.run(), name=endpoint_id)
                                self._connections[endpoint_id] = (connection, task)
                        for endpoint_id, (connection, task) in self._connections.items():
                            if task.done() and not task.cancelled() and task.exception():
                                connection.status.update(status="error", error="官方端工作任务异常，请检查日志并重新保存配置")
                            await self._bridge(f"/api/bridge/endpoints/{endpoint_id}/status", dict(connection.status))
                        failures = 0
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        failures += 1
                        if failures == 1 or failures % 6 == 0:
                            self.ctx.logger.warning(f"官方端管理同步失败（{type(exc).__name__}），正在重试")
                        # Fail closed: revoked/disabled config must not keep sending while management is unavailable.
                        await self._stop_all()
                    await asyncio.sleep(10)
            finally:
                await self._stop_all()
                self._session = None

    @API("adapter.avatar.get", version="1", public=True, description="查询官方事件提供的用户或群头像")
    async def get_avatar(self, platform, target_id, target_type="user", account_id="", scope=""):
        if platform != PLATFORM or target_type not in {"user", "group"}:
            return {"status": "unsupported"}
        for endpoint_id, (connection, _) in self._connections.items():
            if scope and endpoint_id != scope:
                continue
            if account_id and connection.config["app_id"] != account_id:
                continue
            try:
                target = raw_identity(connection.config["app_id"], target_id)
            except ValueError:
                continue
            if connection.state is None:
                continue
            profile = await connection._state("get", profile_key(target_type, target), {})
            if profile.get("avatar_url"):
                return {"status": "available", "url": profile["avatar_url"], "expires_in": 3600}
            return {"status": "missing"}
        return {"status": "missing"}

    @API("adapter.profile.get", version="1", public=True, description="查询官方事件缓存的用户昵称、群名称和头像")
    async def get_profile(self, platform, target_id, target_type="user", account_id="", scope=""):
        if platform != PLATFORM or target_type not in {"user", "group"}:
            return {"status": "unsupported"}
        for endpoint_id, (connection, _) in self._connections.items():
            if (scope and scope != endpoint_id) or (account_id and account_id != connection.config["app_id"]):
                continue
            try:
                target = raw_identity(connection.config["app_id"], target_id)
            except ValueError:
                continue
            if connection.state is None:
                continue
            profile = await connection._state("get", profile_key(target_type, target), {})
            return {"status": "available" if profile else "missing", **profile, "source": "official_event"}
        return {"status": "missing"}

    @MessageGateway(name=GATEWAY, route_type="duplex", platform=PLATFORM, protocol="qq_official",
                    description="QQ 官方机器人群聊和私聊，由毯毯统一端管理配置")
    async def send_official(self, message: dict[str, Any], route=None, metadata=None, **kwargs):
        route = route or {}
        endpoint_id = str(route.get("scope") or "")
        pair = self._connections.get(endpoint_id)
        if pair is None:
            return {"success": False, "error": "没有可用的官方端路由"}
        connection, _ = pair
        try:
            actual_id = await connection.send(message, route)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            safe = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            self.ctx.logger.warning("官方端发送失败：" + safe)
            return {"success": False, "error": safe}
        internal_id = str(message.get("message_id") or "")
        callbacks = ([{"name": "message_id_echo", "payload": {"content": {
            "type": "echo", "echo": internal_id, "actual_id": actual_id,
        }}}] if internal_id and internal_id != actual_id else [])
        return {"success": True, "external_message_id": actual_id,
                "metadata": {"adapter_callbacks": callbacks}}


def create_plugin():
    return QQOfficialPlugin()
