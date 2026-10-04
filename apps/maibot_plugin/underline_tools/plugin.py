"""Underline 工具插件：让麦麦能查群里的技巧库、聊天记录和精华，并把 ``/毯`` 让给毯毯。

拟人聊天归麦麦。要办事（查资料、整理技巧、管理员操作）用 ``/毯 <任务>``：
那条消息由毯毯的 web 服务从 NapCat 推送里接手，按发送者的真实 QQ 号定权限，
这里只负责拦下它，免得麦麦再接一句。

插件里的工具都是只读的，以无权限的 ``maibot`` 身份调用服务；服务端再检查
一遍工具名和群号白名单。token 只从文件读，不进配置、不打印。
"""

from __future__ import annotations

import asyncio
from typing import Any

from maibot_sdk import Command, Field, MaiBotPlugin, PluginConfigBase, Tool
from maibot_sdk.types import ToolParameterInfo, ToolParamType

from .client import DEFAULT_SERVICE_URL, ServiceError, call_tool, format_result, read_token

TASK_PATTERN = r"^\s*/毯(?![\w毯])"


class PluginSectionConfig(PluginConfigBase):
    __ui_label__ = "插件"
    __ui_icon__ = "package"
    __ui_order__ = 0

    enabled: bool = Field(default=True, description="是否启用插件")
    config_version: str = Field(default="1.0.0", description="配置版本")


class ServiceConfig(PluginConfigBase):
    __ui_label__ = "毯毯服务"
    __ui_icon__ = "server"
    __ui_order__ = 1

    service_url: str = Field(default=DEFAULT_SERVICE_URL, description="毯毯 web 服务地址，只用本机回环")
    token_file: str = Field(
        default="",
        description="插件 token 文件路径；留空时用 underline 仓库的 config/api/qqbot_plugin.txt（插件以目录联接安装时有效）",
    )
    timeout_seconds: float = Field(default=20.0, description="单次查询超时（秒）")


class UnderlineToolsConfig(PluginConfigBase):
    plugin: PluginSectionConfig = Field(default_factory=PluginSectionConfig)
    service: ServiceConfig = Field(default_factory=ServiceConfig)


class UnderlineToolsPlugin(MaiBotPlugin):
    config_model = UnderlineToolsConfig

    async def on_load(self) -> None:
        """无需初始化。"""

    async def on_unload(self) -> None:
        """无需清理。"""

    async def _query(self, name: str, tool: str, args: dict[str, Any], kwargs: dict[str, Any]) -> dict[str, Any]:
        if not self.config.plugin.enabled:
            return {"name": name, "content": "underline 工具插件已停用"}
        if str(kwargs.get("platform") or "qq") != "qq":
            return {"name": name, "content": "只支持 QQ 群"}
        service = self.config.service
        try:
            token = read_token(service.token_file)
            result = await asyncio.to_thread(
                call_tool,
                tool,
                str(kwargs.get("group_id") or ""),
                args,
                token,
                service.service_url,
                service.timeout_seconds,
            )
        except ServiceError as exc:
            return {"name": name, "content": f"查询失败：{exc}"}
        return {"name": name, "content": format_result(result)}

    @Tool(
        "underline_search_knowledge",
        description=(
            "查本群的数据包/指令技巧库和聊天记录。技巧库条目是 AI 整理、未验证的，"
            "转述时要说明；结果带消息编号和来源，只说查到的内容，没查到就说没查到。"
        ),
        parameters=[
            ToolParameterInfo(
                name="query", param_type=ToolParamType.STRING, description="要找的关键词，比如 execute 转视角", required=True
            ),
        ],
    )
    async def handle_search_knowledge(self, query: str = "", **kwargs: Any) -> dict[str, Any]:
        return await self._query(
            "underline_search_knowledge", "search_knowledge", {"queries": [str(query)]}, kwargs
        )

    @Tool(
        "underline_search_chat",
        description="按关键词查本群聊天记录，可以限定说话人和最近几天。结果带消息编号。",
        parameters=[
            ToolParameterInfo(name="keyword", param_type=ToolParamType.STRING, description="关键词", required=True),
            ToolParameterInfo(
                name="speaker", param_type=ToolParamType.STRING, description="说话人的 QQ 号或昵称，可不填", required=False
            ),
            ToolParameterInfo(
                name="days", param_type=ToolParamType.INTEGER, description="只看最近几天，可不填", required=False
            ),
        ],
    )
    async def handle_search_chat(
        self, keyword: str = "", speaker: str = "", days: int | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        args: dict[str, Any] = {"keyword": str(keyword)}
        if speaker:
            args["speaker"] = str(speaker)
        if days:
            args["days"] = int(days)
        return await self._query("underline_search_chat", "search_chat", args, kwargs)

    @Tool("underline_read_essence", description="读取本群的精华消息列表。", parameters=[])
    async def handle_read_essence(self, **kwargs: Any) -> dict[str, Any]:
        return await self._query("underline_read_essence", "read_essence", {}, kwargs)

    @Command("underline_task", description="/毯 <任务>：交给毯毯办，麦麦不接这句", pattern=TASK_PATTERN)
    async def handle_task(self, **kwargs: Any):
        # 毯毯的服务已从 NapCat 推送里收到这条消息并会自己回复；这里只拦截。
        return True, None, True

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        del scope, config_data, version


def create_plugin() -> UnderlineToolsPlugin:
    return UnderlineToolsPlugin()
