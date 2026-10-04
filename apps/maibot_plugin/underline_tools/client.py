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
        raise ServiceError(reasons.get(exc.code, f"服务返回 {exc.code}")) from exc
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
    for row in result.get("results", []):
        if row.get("label") == "聊天":
            lines.append(f"[聊天 #{row.get('message_id')}] {_speaker(row)}：{_clip(_text(row))}")
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
