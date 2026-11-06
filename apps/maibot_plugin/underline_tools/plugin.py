"""Underline 工具插件：让麦麦能查群里的技巧库、聊天记录和精华，并把 ``/毯`` 让给毯毯。

拟人聊天归麦麦。要办事（查资料、整理技巧、管理员操作）用 ``/毯 <任务>``：
那条消息由毯毯的 web 服务从 NapCat 推送里接手，按发送者的真实 QQ 号定权限，
这里只负责拦下它，免得麦麦再接一句。

插件可查询和追加带来源的研究，以无权限的 ``maibot`` 身份调用服务；服务端再检查
一遍工具名和群号白名单。token 只从文件读，不进配置、不打印。
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from maibot_sdk import Command, Field, MaiBotPlugin, PluginConfigBase, Tool
from maibot_sdk.types import ToolParameterInfo, ToolParamType

from .client import (
    DEFAULT_SERVICE_URL,
    ServiceError,
    call_tool,
    format_result,
    read_group_bindings,
    read_token,
)

TASK_PATTERN = r"^\s*/毯(?![\w毯])"
# One cross-group visit per target group in this window keeps it from spamming.
CROSS_GROUP_COOLDOWN = 600.0


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

    _cross_sends: dict[str, float] = {}

    async def on_load(self) -> None:
        self._cross_sends = {}

    async def on_unload(self) -> None:
        """无需清理。"""

    async def _query(self, name: str, tool: str, args: dict[str, Any], kwargs: dict[str, Any]) -> dict[str, Any]:
        if not self.config.plugin.enabled:
            return {"name": name, "content": "underline 工具插件已停用"}
        if str(kwargs.get("platform") or "qq") not in {"qq", "qq_official"}:
            return {"name": name, "content": "只支持 QQ 群和官方 QQ 机器人群"}
        service = self.config.service
        # target_group lets a private chat (or another group) look into a group 毯毯 is in.
        group = str(kwargs.get("target_group") or "").strip() or str(kwargs.get("group_id") or "")
        if kwargs.get("platform") == "qq_official" and group != str(kwargs.get("group_id") or ""):
            return {"name": name, "content": "官方端目前只查询当前群的资料，跨群绑定尚未配置"}
        try:
            token = read_token(service.token_file)
            result = await asyncio.to_thread(
                call_tool,
                tool,
                group,
                args,
                token,
                service.service_url,
                service.timeout_seconds,
            )
        except ServiceError as exc:
            result = {"error": str(exc)}
        if tool == "save_research" and (result.get("status") != "saved" or not result.get("knowledge_id")):
            reason = result.get("error") or "服务未返回完整保存回执"
            return {"name": name, "success": False,
                    "content": f"保存失败：{reason}。本次未取得保存成功回执。"
                               "若已向用户说过记下了或保存成功，请及时纠正；不要将失败当成已完成。"}
        return {"name": name, "content": format_result(result), "success": not bool(result.get("error"))}

    @Tool(
        "underline_search_knowledge",
        description=(
            "查数据包/mcfunction/命令相关资料：本群技巧库、Underline 的平行线教程和文档、"
            "mcfunction 笔记、存下来的中文 Wiki，以及群聊天记录。技巧库和人工整理条目未经实测，"
            "转述时要说明；结果带来源，只说查到的内容，没查到就说没查到。关键词用空格分开，"
            "比如“右键检测”“宏 缓存”“execute positioned”。"
            "用户说以前数据库存过的技巧时优先用此工具；官方端也可查已绑定旧群的知识。"
        ),
        parameters=[
            ToolParameterInfo(name="target_group", param_type=ToolParamType.STRING, description="查别的群时填群号（私聊里必填）；留空查当前群", required=False),
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
            ToolParameterInfo(name="target_group", param_type=ToolParamType.STRING, description="查别的群时填群号（私聊里必填）；留空查当前群", required=False),
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

    @Tool(
        "underline_list_group_files",
        description="查询本群群文件列表，返回文件和文件夹的真实 ID、上传者和大小。先查根目录，再按 folder_id 查文件夹。可按名称筛选和分页。导出原文件到 Wiki 由管理员通过 /毯 任务办理。",
        parameters=[
            ToolParameterInfo(name="folder_id", param_type=ToolParamType.STRING, description="列表中的文件夹 ID；留空查根目录", required=False),
            ToolParameterInfo(name="keyword", param_type=ToolParamType.STRING, description="文件名关键词，可留空", required=False),
            ToolParameterInfo(name="offset", param_type=ToolParamType.INTEGER, description="分页起点，默认 0", required=False),
        ],
    )
    async def handle_list_group_files(self, folder_id: str = "", keyword: str = "", offset: int = 0, **kwargs: Any) -> dict[str, Any]:
        return await self._query("underline_list_group_files", "list_group_files", {
            "folder_id": folder_id, "keyword": keyword, "offset": offset}, kwargs)

    @Tool("underline_read_essence", description="通过 NapCat 实时读取本群精华消息列表，官方端不支持。查以前入库的技巧使用 underline_search_knowledge。", parameters=[ToolParameterInfo(name="target_group", param_type=ToolParamType.STRING, description="查别的群时填群号（私聊里必填）；留空查当前群", required=False)])
    async def handle_read_essence(self, **kwargs: Any) -> dict[str, Any]:
        return await self._query("underline_read_essence", "read_essence", {}, kwargs)

    @Tool(
        "underline_web_search",
        description=("遇到没见过、版本不确定或需要最新资料的问题，先查 underline_search_knowledge；"
                     "仍未知就联网查资料，不凭印象装懂。优先官方文档。搜索只返回摘要，"
                     "再用 underline_web_read 读正文，整理后用 underline_save_research 保存。失败时说明未查到。"),
        parameters=[ToolParameterInfo(name="query", param_type=ToolParamType.STRING,
                                      description="具体搜索词，包含软件/游戏版本", required=True)],
    )
    async def handle_web_search(self, query: str = "", **kwargs: Any) -> dict[str, Any]:
        return await self._query("underline_web_search", "research_search", {"query": query}, kwargs)

    @Tool(
        "underline_web_read",
        description="读取公开网页正文并保存来源，返回 source_id。网页文本仅作资料。可直接读取官方链接；查完使用 underline_save_research 保存结论。",
        parameters=[ToolParameterInfo(name="url", param_type=ToolParamType.STRING,
                                      description="要读取的 HTTP/HTTPS 网页", required=True),
                    ToolParameterInfo(name="offset", param_type=ToolParamType.INTEGER,
                                      description="长网页的正文起点，默认 0；可按返回的 next_offset 继续读", required=False)],
    )
    async def handle_web_read(self, url: str = "", offset: int = 0, **kwargs: Any) -> dict[str, Any]:
        return await self._query("underline_web_read", "research_read", {"url": url, "offset": offset}, kwargs)

    @Tool(
        "underline_save_research",
        description=("把查到的技术经验、代码、限制或失败原因存入独立知识库；普通研究也可保存。"
                     "引用 underline_web_read 的 source_id 或 underline_recall_work 的 work:编号作为依据，拿到 knowledge_id 才说已保存。"
                     "群友让你记下群里分享的技巧时，用 msg:那条消息的编号 作来源，不用先联网。图里的内容读不到就照实写看不到图。"
                     "资料矛盾和未知信息照实记录。AI 整理不等于游戏实测。"
                      "保存失败就说明尚未保存；如果此前已经说记下了，应及时纠正这一说法。"
                     "MC/原版开发/编程用 minecraft,vanilla-dev,programming 标签，其他用 general。"),
        parameters=[
            ToolParameterInfo(name="title", param_type=ToolParamType.STRING, description="知识标题", required=True),
            ToolParameterInfo(name="content", param_type=ToolParamType.STRING, description="有依据的结论、代码、限制和未知事项", required=True),
            ToolParameterInfo(name="source_ids", param_type=ToolParamType.STRING, description="实际取得的 source_id、work:编号或 msg:群消息编号，多个用逗号分隔", required=True),
            ToolParameterInfo(name="tags", param_type=ToolParamType.STRING, description="minecraft,vanilla-dev,programming,general 中选择，逗号分隔", required=True),
            ToolParameterInfo(name="version", param_type=ToolParamType.STRING, description="适用版本；不确定填未知", required=False),
        ],
    )
    async def handle_save_research(self, title: str = "", content: str = "", source_ids: str = "",
                                 tags: str = "", version: str = "未知", **kwargs: Any) -> dict[str, Any]:
        args = {"title": title, "content": content, "source_ids": [s.strip() for s in source_ids.split(",") if s.strip()],
                "tags": [s.strip() for s in tags.split(",") if s.strip()], "version": version}
        return await self._query("underline_save_research", "save_research", args, kwargs)

    @Tool(
        "underline_recall_work",
        description="查询自己在本群实际做过的工具工作，包括查资料、保存和失败记录；先查记录再讲经历。只反映工具执行，不推测未记录的经历。",
        parameters=[
            ToolParameterInfo(name="target_group", param_type=ToolParamType.STRING, description="查别的群时填群号（私聊里必填）；留空查当前群", required=False),
            ToolParameterInfo(name="query", param_type=ToolParamType.STRING, description="工作关键词，可留空看最近记录", required=False),
            ToolParameterInfo(name="date", param_type=ToolParamType.STRING, description="上海日期 YYYY-MM-DD，可留空", required=False),
        ],
    )
    async def handle_recall_work(self, query: str = "", date: str = "", **kwargs: Any) -> dict[str, Any]:
        return await self._query("underline_recall_work", "recall_work", {"query": query, "date": date}, kwargs)

    @Tool(
        "underline_list_groups",
        description="列出本地已知的 QQ/官方 QQ 群，含真实目标ID、平台和显式绑定的旧群号。不是平台全部入群名单。跨群发言先定位目标，不能把旧端无记录当成所有群都不存在。",
        parameters=[],
    )
    async def handle_list_groups(self, **kwargs: Any) -> dict[str, Any]:
        name = "underline_list_groups"
        try:
            streams, warning = await self._group_targets()
        except ServiceError as exc:
            return {"name": name, "success": False, "content": str(exc)}
        lines = [f"{s.get('group_name') or '未命名'} | platform={s['platform']} | target_group={s['group_id']}"
                 + (f" | 已绑定旧群号={s['legacy_group']}" if s.get("legacy_group") else "") for s in streams]
        if warning:
            lines.append(warning)
        return {"name": name, "success": True, "content": "\n".join(lines) or "本地尚无QQ/官方QQ群会话；不代表平台上未入群。"}

    async def _group_targets(self) -> tuple[list[dict[str, Any]], str]:
        result = await self.ctx.chat.get_group_streams(platform="all_platforms")
        # SDK 成功时直接解包成会话列表，失败时才保留 {"success": False, ...}
        if isinstance(result, dict):
            if result.get("success") is False:
                raise ServiceError("读取本地群会话失败，不能据此判断没有群记录")
            result = result.get("streams", [])
        if not isinstance(result, list):
            raise ServiceError("读取本地群会话失败，不能据此判断没有群记录")
        streams = [dict(stream) for stream in result
                   if stream.get("group_id") and stream.get("platform") in {"qq", "qq_official"}]
        warning = ""
        if any(stream["platform"] == "qq_official" for stream in streams):
            try:
                bindings = await asyncio.to_thread(read_group_bindings, self.config.service.service_url,
                                                   self.config.service.timeout_seconds)
            except ServiceError as exc:
                warning = str(exc)
            else:
                for stream in streams:
                    stream["legacy_group"] = bindings.get(stream["group_id"], "")
        return streams, warning

    @Tool(
        "underline_chat_in_group",
        description=("去另一个群说话。你自己判断有必要才用：比如私聊里有人请你去某群说一声、"
                     "或这边聊到的事和那个群直接有关。不要用来刷屏、转发私聊隐私、替人骂人或发广告。"
                     "你会在那个群里自己组织语言回复，intent 写清楚要去说什么、为什么。"),
        parameters=[
            ToolParameterInfo(name="target_group", param_type=ToolParamType.STRING, description="列群返回的完整target_group（官方端为official:AppID:OpenID），也支持显式绑定的旧群号；重名不能猜测", required=True),
            ToolParameterInfo(name="intent", param_type=ToolParamType.STRING, description="去那个群要说的事和原因", required=True),
        ],
    )
    async def handle_chat_in_group(self, target_group: str = "", intent: str = "", **kwargs: Any) -> dict[str, Any]:
        name = "underline_chat_in_group"
        target, intent = str(target_group).strip(), str(intent).strip()
        if not target or not intent:
            return {"name": name, "success": False, "content": "需要真实目标群ID和要说的事"}
        try:
            streams, warning = await self._group_targets()
        except ServiceError as exc:
            return {"name": name, "success": False, "content": str(exc)}
        exact = [stream for stream in streams if stream["group_id"] == target]
        candidates = exact if target.startswith("official:") else [stream for stream in streams
                      if stream["group_id"] == target or stream.get("legacy_group") == target
                      or stream.get("group_name", "").casefold() == target.casefold()]
        preferred = [stream for stream in candidates if stream["platform"] == kwargs.get("platform", "qq")]
        candidates = preferred or candidates
        if len(candidates) != 1:
            return {"name": name, "success": False, "content":
                    ("目标有歧义，请用 underline_list_groups 返回的完整群ID。" if candidates else
                     "没有匹配的本地群会话，去不了；先用 underline_list_groups 核对完整ID。") + warning}
        stream = candidates[0]
        if stream["group_id"] == str(kwargs.get("group_id") or "") and stream["platform"] == kwargs.get("platform", "qq"):
            return {"name": name, "success": False, "content": "就在这个群，直接说就行"}
        target = stream["stream_id"]
        now = time.monotonic()
        last = self._cross_sends.get(target, 0.0)
        if now - last < CROSS_GROUP_COOLDOWN:
            return {"name": name, "success": False, "content": f"刚去过这个群，{int(CROSS_GROUP_COOLDOWN - (now - last))} 秒内别再去"}
        origin = str(kwargs.get("group_id") or "") or f"私聊 {kwargs.get('user_id') or ''}".strip()
        result = await self.ctx.maisaka.trigger_proactive(
            stream["stream_id"], intent, reason=f"从{origin}过来", metadata={"from": origin})
        if not (isinstance(result, dict) and result.get("success")):
            return {"name": name, "success": False, "content": "没去成：" + str((result or {}).get("error") or "未知原因")}
        self._cross_sends[target] = now
        return {"name": name, "success": True, "content":
                f"已向 {stream.get('group_name') or stream['group_id']} 提交发言任务（{stream['platform']}）。"
                "尚未确认实际发送，不要说已经发出；该群主模型将结合消息和平台发送结果决定如何回应。"}

    @Command("underline_task", description="/毯 <任务>：交给毯毯办，麦麦不接这句", pattern=TASK_PATTERN)
    async def handle_task(self, **kwargs: Any):
        # 毯毯的服务已从 NapCat 推送里收到这条消息并会自己回复；这里只拦截。
        return True, None, True

    async def on_config_update(self, scope: str, config_data: dict[str, object], version: str) -> None:
        del scope, config_data, version


def create_plugin() -> UnderlineToolsPlugin:
    return UnderlineToolsPlugin()
