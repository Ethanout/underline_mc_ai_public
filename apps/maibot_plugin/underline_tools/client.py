"""Talks to the underline qqbot service; stdlib only so it can be tested without MaiBot.

The service decides everything that matters for safety: which tools a plugin
may call (read-only ones), which groups are served, and the caller identity
(always the unprivileged ``maibot``).  This side only forwards the group the
chat is in and formats the answer for MaiBot's planner.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

# apps/maibot_plugin/underline_tools/client.py -> repository root.  resolve()
# follows a junction from MaiBot's plugins folder back into this repository.
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TOKEN_FILE = REPO_ROOT / "config" / "api" / "qqbot_plugin.txt"
DEFAULT_SERVICE_URL = "http://127.0.0.1:18787"
MAX_RESULT_CHARS = 4000


class ServiceError(RuntimeError):
    """The service refused or could not be reached; the message is safe to show."""


def read_token(path: str | Path = "") -> str:
    token_file = Path(path) if str(path).strip() else DEFAULT_TOKEN_FILE
    try:
        token = token_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ServiceError(f"读不到插件 token 文件 {token_file}：{exc.strerror or exc}") from exc
    if not token:
        raise ServiceError(f"插件 token 文件 {token_file} 是空的")
    return token


def read_group_bindings(service_url: str = DEFAULT_SERVICE_URL, timeout: float = 20) -> dict[str, str]:
    """读取管理端公开的显式绑定；不请求或读取官方端密钥。"""
    request = urllib.request.Request(service_url.rstrip("/") + "/api/endpoints")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=timeout) as response:
            payload = json.load(response)
        return {
            f"official:{endpoint['app_id']}:{openid}": legacy
            for endpoint in payload["endpoints"] if endpoint.get("enabled") and endpoint.get("kind") == "qq_official"
            for openid, legacy in endpoint.get("group_bindings", {}).items()
        }
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ServiceError("无法读取官方群绑定；仍可用列群返回的完整群ID定位，不要猜测旧群号") from exc


def call_tool(
    tool: str,
    group_id: str,
    args: dict[str, Any],
    token: str,
    service_url: str = DEFAULT_SERVICE_URL,
    timeout: float = 20,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    if not str(group_id).strip():
        raise ServiceError("只能在群聊里查")
    request = urllib.request.Request(
        service_url.rstrip("/") + "/api/plugin/tool",
        data=json.dumps({"tool": tool, "group_id": str(group_id), "args": args}).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with opener(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        reasons = {401: "插件 token 不对", 403: "这个群或这个工具不对插件开放"}
        reason = reasons.get(exc.code, f"服务返回 {exc.code}")
        if exc.code == 400:
            try:
                detail = json.loads(exc.read(4096)).get("detail")
                if isinstance(detail, str):
                    reason = detail[:1000].replace(token, "[凭证]") if token else detail[:1000]
            except (ValueError, OSError, AttributeError):
                pass
        raise ServiceError(reason) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise ServiceError("连不上毯毯的 web 服务，确认它在运行") from exc


def _clip(text: Any, limit: int = 300) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[:limit] + "…"


def _speaker(row: dict[str, Any]) -> str:
    return str(row.get("card") or row.get("nickname") or row.get("sender_nick") or row.get("user_id") or "")


def _text(row: dict[str, Any]) -> str:
    if row.get("text"):
        return str(row["text"])
    # Essence rows come straight from NapCat: segments, no flattened text.
    parts = []
    for segment in row.get("message") or []:
        data = segment.get("data") or {}
        parts.append(str(data.get("text", "")) if segment.get("type") == "text" else f"[{segment.get('type')}]")
    return "".join(parts)


def format_result(result: dict[str, Any], limit: int = MAX_RESULT_CHARS) -> str:
    """Compact lines the planner can quote, each carrying where it came from."""
    if result.get("error"):
        return f"查询失败：{result['error']}"
    lines: list[str] = []
    if result.get("knowledge_id"):
        return (f"研究已保存，knowledge_id={result['knowledge_id']}；"
                f"{result.get('verification')}；标签={','.join(result.get('tags', []))}；"
                f"来源={','.join(result.get('source_ids', []))}"
                + (f"；{result['workspace_warning']}" if result.get("workspace_warning") else ""))
    if result.get("source_id"):
        excerpt_size = max(100, limit - 650)
        next_offset = (result.get("offset", 0) + excerpt_size if len(result["content"]) > excerpt_size
                       else result.get("next_offset"))
        return (f"source_id={result['source_id']}\n来源：{result['url']}\n"
                f"标题：{result['title']}\n{result.get('status', '')}\n"
                f"offset={result.get('offset', 0)}；next_offset={next_offset}\n"
                f"正文截断：{bool(result.get('truncated')) or len(result['content']) > excerpt_size}\n"
                f"正文：{result['content'][:excerpt_size]}")[:limit]
    if result.get("status"):
        lines.append(str(result["status"]))
    if "next_offset" in result:
        lines.append(f"当前文件夹，共 {result.get('total', 0)} 项；next_offset={result['next_offset']}；{result.get('scope', '')}")
    for row in result.get("results", []):
        if row.get("group_id"):
            lines.append(f"来源群：{row['group_id']}")
        if row.get("kind") == "file":
            lines.append(f"[文件 {row.get('file_name')}，file_id={row.get('file_id')}] 大小={row.get('file_size') or row.get('size')}；上传者={row.get('uploader_name')} ({row.get('uploader')})")
        elif row.get("kind") == "folder":
            lines.append(f"[文件夹 {row.get('folder_name')}，folder_id={row.get('folder_id')}] 文件数={row.get('total_file_count')}")
        elif row.get("label") == "聊天":
            lines.append(f"[聊天 #{row.get('message_id')}] {_speaker(row)}：{_clip(_text(row))}")
        elif row.get("title"):
            lines.append(f"[{row.get('label') or row.get('kind', '网页')}：{row.get('title')}，{(row.get('sources') or [row.get('url', '?')])[0]}] {_clip(row.get('content') or row.get('summary'), 900)}")
        else:
            sources = "、".join(str(s) for s in row.get("sources") or []) or "无"
            lines.append(f"[{row.get('label')}，来源 {sources}] {_clip(row.get('content'), 600)}")
    for row in result.get("messages", []):
        lines.append(f"[#{row.get('message_id')}] {_speaker(row)}：{_clip(_text(row))}")
    if not lines:
        return "没查到相关内容。"
    text, kept = "", 0
    for line in lines:
        if len(text) + len(line) + 1 > limit:
            break
        text, kept = text + line + "\n", kept + 1
    if kept < len(lines):
        text += f"（还有 {len(lines) - kept} 条没列出）"
    return text.rstrip()
