#!/usr/bin/env python3
"""Export QQ group essence messages through a OneBot-compatible HTTP API.

The QQ-side action is intentionally configurable because NapCat/Lagrange
adapters expose different names for the essence-message list endpoint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def api_call(endpoint: str, token: str | None, action: str, params: dict[str, Any], root_envelope: bool) -> Any:
    if root_envelope:
        url = endpoint
        request_payload = {"action": action, "params": params, "echo": "qq-essence-export"}
    else:
        # NapCat's OneBot HTTP server exposes each action as its own URL path.
        url = f"{endpoint.rstrip('/')}/{urllib.parse.quote(action, safe='_')}"
        request_payload = params
    body = json.dumps(request_payload).encode()
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"无法连接 OneBot 接口 {url}: {exc}") from exc
    if not isinstance(payload, (dict, list)):
        raise RuntimeError(f"QQ 接口返回了非 JSON 对象或列表: {type(payload).__name__}")
    if isinstance(payload, dict):
        if payload.get("status") == "failed" or payload.get("retcode", 0) not in (0, None):
            # Do not include a potentially content-bearing OneBot payload in logs.
            raise RuntimeError("QQ 接口调用失败，请在 NapCat 日志中检查 retcode 和权限。")
        return payload.get("data", payload)
    return payload


def find_list(value: Any) -> list[dict[str, Any]]:
    """Accept common response wrappers used by different adapters."""
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("messages", "essence_messages", "items", "list", "records"):
            result = find_list(value.get(key))
            if result:
                return result
        for nested in value.values():
            result = find_list(nested)
            if result:
                return result
    return []


def response_summary(value: Any) -> str:
    if value is None:
        return "接口 data=null"
    if isinstance(value, list):
        keys = sorted(value[0].keys()) if value and isinstance(value[0], dict) else []
        return f"接口返回 list，数量={len(value)}，首项字段={keys}"
    if isinstance(value, dict):
        parts = []
        for key, nested in value.items():
            if isinstance(nested, list):
                parts.append(f"{key}=list({len(nested)})")
            elif isinstance(nested, dict):
                parts.append(f"{key}=object({sorted(nested.keys())})")
            else:
                parts.append(f"{key}={type(nested).__name__}")
        return f"接口返回 object：{'; '.join(parts)}"
    return f"接口返回 {type(value).__name__}"


def message_id(message: dict[str, Any]) -> str:
    for key in ("message_id", "msg_id", "id"):
        if message.get(key) is not None:
            return str(message[key])
    digest = hashlib.sha1(json.dumps(message, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return f"unknown-{digest[:16]}"


def safe_name(value: str, fallback: str = "file") -> str:
    value = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", value).strip(" .")
    return value or fallback


def extension_for(url: str, content_type: str | None = None) -> str:
    suffix = Path(urllib.parse.urlparse(url).path).suffix
    if suffix and len(suffix) <= 10:
        return suffix
    return mimetypes.guess_extension((content_type or "").split(";")[0].strip()) or ".bin"


def download(url: str, target: Path, token: str | None) -> Path:
    parsed = urllib.parse.urlparse(url)
    local_candidate = Path(url) if Path(url).exists() else Path(urllib.request.url2pathname(parsed.path))
    if parsed.scheme in ("", "file") and local_candidate.exists():
        shutil.copy2(local_candidate, target)
        return target
    request = urllib.request.Request(url)
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
        if target.suffix == ".bin":
            target = target.with_suffix(extension_for(url, response.headers.get("Content-Type")))
        target.write_bytes(data)
    return target


def extract_media(message: dict[str, Any]) -> list[tuple[str, str, str]]:
    segments = message.get("message") or message.get("message_chain") or message.get("content") or []
    if isinstance(segments, str):
        return []
    media: list[tuple[str, str, str]] = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        kind = segment.get("type", "")
        data = segment.get("data") if isinstance(segment.get("data"), dict) else segment
        if kind not in ("image", "file", "video", "record"):
            continue
        url = data.get("url") or data.get("file_url") or data.get("path") or data.get("file")
        if url:
            media.append((kind, str(url), safe_name(str(data.get("name") or data.get("file_name") or kind))))
    return media


def has_message_content(message: dict[str, Any]) -> bool:
    for key in ("message", "message_chain", "raw_message"):
        if message.get(key):
            return True
    return bool(message.get("content"))


def fetch_message_detail(
    endpoint: str,
    token: str | None,
    message: dict[str, Any],
    action: str,
    root_envelope: bool,
) -> dict[str, Any]:
    """Fetch text and segments when an essence-list item only has metadata."""
    if has_message_content(message):
        return message
    detail = api_call(endpoint, token, action, {"message_id": message_id(message)}, root_envelope)
    if isinstance(detail, dict):
        merged = dict(message)
        merged.update(detail)
        return merged
    return message


def read_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict) or not isinstance(loaded.get("messages", []), list):
        raise RuntimeError("已有 messages.json 格式无效；请修复文件或使用 --overwrite。")
    return loaded


def export(args: argparse.Namespace) -> int:
    token = os.environ.get(args.token_env)
    output = Path(args.output).resolve()
    manifest_path = output / "messages.json"
    existing: dict[str, Any] = {} if args.overwrite else read_manifest(manifest_path)
    messages: dict[str, Any] = {
        str(item["message_id"]): item
        for item in existing.get("messages", [])
        if isinstance(item, dict) and item.get("message_id") is not None
    }
    if not args.diagnose:
        output.mkdir(parents=True, exist_ok=True)
        (output / "media").mkdir(exist_ok=True)
    page = 0
    processed = 0
    downloaded = 0
    failures = 0
    detail_failures = 0
    while page < args.max_pages:
        params = {
            "group_id": args.group_id,
            "page": page,
            "offset": page * args.page_size,
            "page_size": args.page_size,
            "limit": args.page_size,
        }
        response_data = api_call(args.endpoint, token, args.action, params, args.root_envelope)
        if args.diagnose:
            print(response_summary(response_data))
            return 0
        batch = find_list(response_data)
        if not batch:
            if args.diagnose:
                print("未找到可导出的消息对象；请检查 action 返回结构或账号是否能在 QQ 客户端查看群精华。")
            break
        new_count = 0
        for raw in batch:
            if args.max_messages and processed >= args.max_messages:
                break
            mid = message_id(raw)
            if mid in messages and not args.refresh:
                continue
            new_count += 1
            processed += 1
            try:
                source = fetch_message_detail(
                    args.endpoint,
                    token,
                    raw,
                    args.message_action,
                    args.root_envelope,
                )
            except RuntimeError:
                # QQ can retain an essence marker after the original message expires.
                source = raw
                detail_failures += 1
            record = dict(source)
            record["message_id"] = mid
            record["media"] = []
            for index, (kind, url, name) in enumerate(extract_media(source)):
                parsed = urllib.parse.urlparse(url)
                suffix = Path(parsed.path).suffix or ".bin"
                filename = safe_name(f"{mid}_{index}_{name}") + suffix
                target = output / "media" / filename
                try:
                    saved_path = download(url, target, token)
                    record["media"].append({"type": kind, "source": url, "file": str(saved_path.relative_to(output))})
                    downloaded += 1
                except Exception as exc:  # keep the message even if one attachment fails
                    record["media"].append({"type": kind, "source": url, "error": str(exc)})
                    failures += 1
            messages[mid] = record
        if args.max_messages and processed >= args.max_messages:
            break
        if new_count == 0 and page > 0:
            break
        page += 1
        if len(batch) < args.page_size:
            break
        time.sleep(args.delay)
    result = {
        "schema_version": 1,
        "group_id": str(args.group_id),
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "messages": list(messages.values()),
    }
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"导出完成：消息 {len(messages)} 条，媒体 {downloaded} 个，媒体失败 {failures} 个，"
        f"正文缺失 {detail_failures} 条，输出目录：{output}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="批量导出 QQ 群精华消息及媒体附件")
    parser.add_argument("--endpoint", required=True, help="OneBot HTTP API 地址，例如 http://127.0.0.1:3000")
    parser.add_argument("--token-env", default="ONEBOT_ACCESS_TOKEN", help="读取 token 的环境变量名")
    parser.add_argument("--group-id", required=True, help="QQ群号")
    parser.add_argument("--action", default="get_essence_msg_list", help="适配器的精华列表 action 名称")
    parser.add_argument("--message-action", default="get_msg", help="读取精华正文的 action")
    parser.add_argument("--root-envelope", action="store_true", help="向根路径发送 action envelope；仅用于少数非标准适配器")
    parser.add_argument("--output", default="./export", help="导出目录")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=10000)
    parser.add_argument("--max-messages", type=int, default=0, help="最多处理多少条新消息；0 表示不限制")
    parser.add_argument("--diagnose", action="store_true", help="仅请求一次并输出结构/数量，不写入消息或媒体")
    parser.add_argument("--delay", type=float, default=0.3, help="分页请求间隔秒数")
    parser.add_argument("--refresh", action="store_true", help="重新读取已有 message_id")
    parser.add_argument("--overwrite", action="store_true", help="忽略旧清单")
    args = parser.parse_args()
    try:
        return export(args)
    except Exception as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
