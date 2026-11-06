"""Translate official OpenIDs and message elements into MaiBot components."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime
from urllib.parse import urlparse

import aiohttp

from .profiles import avatar_url

PLATFORM = "qq_official"
GATEWAY = "qq_official_gateway"
MAX_IMAGE_BYTES = 8 * 1024 * 1024


def identity(app_id, value):
    return f"official:{app_id}:{value}"


def raw_identity(app_id, value):
    prefix = f"official:{app_id}:"
    if not value.startswith(prefix) or not value[len(prefix):]:
        raise ValueError("消息目标不属于当前官方机器人，不能跨端发送")
    return value[len(prefix):]


def event_allowed(config, event_type, data):
    if event_type not in {"GROUP_AT_MESSAGE_CREATE", "GROUP_MESSAGE_CREATE", "C2C_MESSAGE_CREATE"}:
        return False
    if event_type == "GROUP_MESSAGE_CREATE" and not config["receive_all"] and not mentions_self(data):
        return False
    author = data.get("author") or {}
    if author.get("bot"):
        return False
    if event_type == "C2C_MESSAGE_CREATE":
        user = str(author.get("user_openid") or author.get("id") or "")
        return bool(config["allow_private"] and user and (
            not config["private_users"] or user in config["private_users"]
        ))
    group = str(data.get("group_openid") or "")
    return bool(group and (not config["groups"] or group in config["groups"]))


def mentions_self(data):
    """Official full-message events identify the bot through mention metadata."""
    return any(mention.get("is_you") is True for mention in data.get("mentions") or [])


def _format_mention_text(data):
    card = str(data.get("target_user_cardname") or "").strip()
    nickname = str(data.get("target_user_nickname") or "").strip()
    target_id = str(data.get("target_user_id") or "").strip()
    label = card or nickname or target_id or "未知人物"
    details = []
    if card and nickname and nickname != card:
        details.append(f"昵称：{nickname}")
    if target_id and target_id not in {card, nickname}:
        details.append(f"平台ID：{target_id}")
    return f"@{label}" + (f"（{'，'.join(details)}）" if details else "")


def mention_components(app_id, text, mentions):
    """Keep body order and resolve only mentions supplied by the official event."""
    users = {}
    for mention in mentions:
        for key in ("id", "member_openid", "user_openid"):
            if mention.get(key):
                users[str(mention[key])] = mention
    components = []
    start = 0
    for match in re.finditer(r"<@!?([^<>\s]+)>", text):
        if match.start() > start:
            components.append({"type": "text", "data": text[start:match.start()]})
        uid = match.group(1)
        user = users.get(uid)
        if user is None:
            components.append({"type": "text", "data": match.group(0)})
        else:
            name = user.get("username") or ("毯毯" if user.get("is_you") is True else uid)
            components.append({"type": "at", "data": {
                "target_user_id": identity(app_id, uid), "target_user_nickname": name,
                "target_user_cardname": user.get("member_name") or user.get("card"),
            }})
        start = match.end()
    if start < len(text):
        components.append({"type": "text", "data": text[start:]})
    return components


def face_text(text):
    """Render the official face label; ext metadata is not an image attachment."""
    def replace_face(match):
        attributes = {}
        for field in re.finditer(r'(faceType|faceId|ext)\s*=\s*(?:"([^"]*)"|\x27([^\x27]*)\x27|([^,\s>]+))', match[0]):
            attributes[field[1]] = next(value for value in field.groups()[1:] if value is not None)
        encoded = attributes.get("ext", "")
        description = ""
        if encoded and len(encoded) <= 8192:
            try:
                metadata = json.loads(base64.b64decode(encoded + "=" * (-len(encoded) % 4), validate=True))
                if isinstance(metadata, dict) and isinstance(metadata.get("text"), str):
                    description = " ".join(metadata["text"].split())[:200].strip("[]")
            except (ValueError, UnicodeError):
                pass
        if description:
            return f"[QQ表情：{description}]"
        if attributes.get("faceType") == "6":
            return "[表情包]"
        face_id = attributes.get("faceId", "")
        return f"[QQ表情：编号{face_id[:32]}]" if face_id else "[QQ表情：未提供描述]"

    return re.sub(r"<faceType\s*=[^<>]*>", replace_face, text)


def element_text(elements, app_id, depth=0):
    if depth > 4:
        return "[嵌套消息过深，未展开]"
    lines = []
    for element in elements[:30]:
        author = element.get("author") or {}
        user_id = str(author.get("member_openid") or author.get("user_openid") or author.get("id") or "")
        nickname = str(author.get("username") or author.get("nickname") or "").strip()
        card = str(author.get("member_name") or author.get("card") or "").strip()
        speaker = card or nickname or ("未知人物" if not user_id else "未知昵称")
        details = []
        if card and nickname and nickname != card:
            details.append(f"昵称：{nickname}")
        if user_id:
            details.append(f"平台ID：{identity(app_id, user_id)}")
        if details:
            speaker += f"（{'，'.join(details)}）"
        original_content = str(element.get("content") or "")
        content = face_text(original_content[:1500])
        if len(original_content) > 1500:
            content += " [预览截断；完整原文可用read_message读取组件]"
        text = "".join(
            part["data"] if part["type"] == "text" else
            _format_mention_text(part["data"])
            for part in mention_components(app_id, content, element.get("mentions") or [])
        )
        nested = element.get("msg_elements") or []
        if nested:
            text += "\n" + element_text(nested, app_id, depth + 1)
        if element.get("attachments"):
            text += " [含附件]"
        lines.append(f"{speaker}：{text}")
    preview = "\n".join(lines)
    if len(elements) > 30 or len(preview) > 6000:
        return preview[:6000] + "\n[预览截断；完整消息元素已保留，可用read_message继续读取]"
    return preview


def _message_reference_id(data):
    reference = data.get("message_reference") or data.get("reference") or {}
    if isinstance(reference, dict):
        message_id = reference.get("message_id") or reference.get("id")
        if message_id:
            return str(message_id)
    elif isinstance(reference, str) and reference.strip():
        return reference.strip()
    if data.get("message_type") not in (102, 103):
        return ""
    for element in data.get("msg_elements") or []:
        message_id = element.get("message_id") or element.get("id")
        if message_id:
            return str(message_id)
    return ""


def _card_components(data):
    """Keep card text and links visible, with the full structured fields available to tools."""
    card = data.get("ark_data")
    if not card:
        return []
    text = json.dumps(card, ensure_ascii=False)
    preview = text[:3000] + (" [卡片预览截断；read_message可读取完整原文]" if len(text) > 3000 else "")
    return [{"type": "text", "data": "[QQ卡片]\n" + preview},
            {"type": "dict", "data": {"type": "official_card", "payload": deepcopy(card)}}]


async def image_component(session, url):
    try:
        parsed = urlparse(url)
        port = parsed.port
    except (ValueError, TypeError):
        return {"type": "text", "data": "[图片：下载地址格式无效；原附件信息已保留]"}
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or port not in (None, 443) or parsed.username or parsed.password or not any(
        host == domain or host.endswith("." + domain)
        for domain in ("qq.com", "qq.com.cn", "qpic.cn", "gtimg.cn", "gtimg.com")
    ):
        return {"type": "text", "data": "[图片：下载地址不受支持]"}
    try:
        async with session.get(url, allow_redirects=False) as response:
            if response.status != 200:
                return {"type": "text", "data": f"[图片：下载失败 HTTP {response.status}]"}
            raw = bytearray()
            async for chunk in response.content.iter_chunked(65536):
                raw.extend(chunk)
                if len(raw) > MAX_IMAGE_BYTES:
                    return {"type": "text", "data": "[图片：超过8 MiB下载上限]"}
        if not bytes(raw).startswith((b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"RIFF")):
            return {"type": "text", "data": "[图片：文件格式无法识别]"}
        return {"type": "image", "data": "", "hash": hashlib.sha256(raw).hexdigest(),
                "binary_data_base64": base64.b64encode(raw).decode("ascii")}
    except (OSError, TimeoutError, aiohttp.ClientError):
        return {"type": "text", "data": "[图片：下载失败或超时]"}


async def _attachment_components(data, session, budget):
    """Share one download budget between the body and its quoted message tree."""
    components = []
    sticker = bool(re.search(r'<faceType\s*=\s*["\x27]?6(?:["\x27]?(?:,|\s|>))', str(data.get("content") or "")))
    attachments = list(data.get("attachments") or [])
    # QQ may serialize nested quote attachments into text rather than attachments[].
    for line in str(data.get("content") or "").splitlines():
        if not re.search(r"\[附件\d+\]\s*类型\s*[:：]\s*(?:图片|image)", line, re.I):
            continue
        url = re.search(r"\bURL\s*[:：]\s*(https://[^\s<>\"']+)", line, re.I)
        if url and not any(item.get("url") == url[1] for item in attachments):
            filename = re.search(r"文件名\s*[:：]\s*(.*?)\s+(?:尺寸|大小|URL)\s*[:：]", line)
            attachments.append({"url": url[1], "filename": filename[1] if filename else "引用图片",
                                "content_type": "image/unknown"})
    for attachment in attachments:
        content_type = str(attachment.get("content_type") or "")
        # Keep the original address even if eager loading is limited or fails.
        components.append({"type": "file", "data": {
            "name": attachment.get("filename") or "附件", "url": attachment.get("url") or "",
            "size": attachment.get("size") or "", "mime_type": content_type,
            "file_id": attachment.get("id") or "",
        }})
        if budget["attachments"] >= 6:
            components.append({"type": "text", "data": "[附件未预加载，可用read_message/view_image按需读取原图]"})
            continue
        budget["attachments"] += 1
        if not content_type.startswith("image/"):
            description = attachment.get("asr_refer_text") or attachment.get("filename") or content_type
            components.append({"type": "text", "data": f"[附件:{description}]"})
            continue
        if budget["bytes"] >= 10 * 1024 * 1024:
            components.append({"type": "text", "data": "[图片：本条消息图片总量超过传输上限]"})
            continue
        component = await image_component(session, attachment.get("url", ""))
        budget["bytes"] += len(component.get("binary_data_base64", ""))
        if budget["bytes"] > 10 * 1024 * 1024:
            component = {"type": "text", "data": "[图片：本条消息图片总量超过传输上限]"}
        elif sticker and component["type"] == "image":
            # EmojiComponent invokes MaiBot's persistent emoji collection pipeline.
            component = {**component, "type": "emoji"}
        components.append(component)
    return components


async def _element_components(elements, app_id, session, budget, depth=0):
    """Keep quoted/forwarded bodies and media as addressable component trees."""
    if depth >= 8:
        return [{"type": "text", "data": "[嵌套消息超过8层，未展开]"}]
    nodes = []
    for element in elements:
        if budget["nodes"] >= 60:
            break
        if not isinstance(element, dict):
            continue
        budget["nodes"] += 1
        author = element.get("author") or {}
        uid = str(author.get("member_openid") or author.get("user_openid") or author.get("id") or "")
        components = []
        target_id = _message_reference_id(element)
        if target_id:
            components.append({"type": "reply", "data": {"target_message_id": identity(app_id, target_id)}})
        if element.get("content"):
            components.extend(mention_components(app_id, face_text(str(element["content"])), element.get("mentions") or []))
        components.extend(await _attachment_components(element, session, budget))
        components.extend(_card_components(element))
        if element.get("msg_elements"):
            components.extend(await _element_components(element["msg_elements"], app_id, session, budget, depth + 1))
        nodes.append({
            "user_id": identity(app_id, uid) if uid else "", "user_nickname": author.get("username") or author.get("nickname") or "未知人物",
            "user_cardname": author.get("member_name") or author.get("card"),
            "message_id": identity(app_id, str(element.get("message_id") or element.get("id"))) if element.get("message_id") or element.get("id") else "",
            "content": components or [{"type": "text", "data": "[平台未提供嵌套消息正文或附件]"}],
        })
    result = [{"type": "forward", "data": nodes}] if nodes else []
    if budget["nodes"] >= 60:
        result.append({"type": "text", "data": "[嵌套消息超过60个节点，后续未展开]"})
    return result


def _contains_component(components, kind):
    for component in components:
        if component["type"] == kind:
            return True
        if component["type"] == "forward" and any(
            _contains_component(node["content"], kind) for node in component["data"]
        ):
            return True
    return False


async def build_message(config, event_type, data, session):
    app_id = config["app_id"]
    author = data.get("author") or {}
    private = event_type == "C2C_MESSAGE_CREATE"
    user_id = str(author.get("user_openid" if private else "member_openid") or author.get("id") or "")
    if not user_id or not data.get("id"):
        raise ValueError("官方事件缺少用户 OpenID 或消息 ID")
    timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")).timestamp()
    content = str(data.get("content") or "")
    text = face_text(content)
    segments = []
    reference_id = _message_reference_id(data)
    nested_elements = data.get("msg_elements") or []
    nested_text = element_text(nested_elements, app_id) if nested_elements else ""
    if reference_id:
        first_element = nested_elements[0] if nested_elements else {}
        quoted_author = first_element.get("author") or {}
        quoted_user_id = str(
            quoted_author.get("member_openid") or quoted_author.get("user_openid") or quoted_author.get("id") or ""
        )
        quoted_nickname = str(quoted_author.get("username") or quoted_author.get("nickname") or "").strip()
        quoted_card = str(quoted_author.get("member_name") or quoted_author.get("card") or "").strip()
        reference = data.get("message_reference") if isinstance(data.get("message_reference"), dict) else {}
        segments.append({"type": "reply", "data": {
            "target_message_id": identity(app_id, reference_id),
            "target_message_content": nested_text or str(reference.get("content") or ""),
            "target_message_sender_id": identity(app_id, quoted_user_id) if quoted_user_id else "",
            "target_message_sender_nickname": quoted_nickname,
            "target_message_sender_cardname": quoted_card,
        }})
    if nested_elements:
        label = "引用/聊天记录" if data.get("message_type") in (102, 103) else "消息元素"
        group_name = data.get("group_name") or config["name"]
        reference_label = f"，引用消息ID：{identity(app_id, reference_id)}" if reference_id else ""
        segments.append({"type": "text", "data": f"[{label}，群：{group_name}{reference_label}]\n{nested_text}\n当前消息内容:"})
    elif reference_id:
        segments.append({"type": "text", "data": f"[引用消息ID：{identity(app_id, reference_id)}；平台未提供引用原文]\n当前消息内容:"})
    if text:
        segments.extend(mention_components(app_id, text, data.get("mentions") or []))
    budget = {"attachments": 0, "bytes": 0, "nodes": 0}
    segments.extend(await _attachment_components(data, session, budget))
    segments.extend(_card_components(data))
    if nested_elements:
        segments.extend(await _element_components(nested_elements, app_id, session, budget))
        if data.get("message_type") in (102, 103) and not reference_id:
            segments.append({"type": "dict", "data": {
                "type": "official_reference_preview", "status": "reference_id_missing",
                "preview": nested_text, "detail": "官方事件未提供引用ID；用read_message检查内嵌内容及本地历史候选，不能推断QQ故障。",
            }})
    parallel = (data.get("parallel_message") or {}).get("msg_nodes") or []
    if parallel:
        segments.append({"type": "text", "data": "[平台关联消息，非当前发送者正文]"})
        segments.extend(await _element_components(parallel, app_id, session, budget))
    if nested_elements or parallel or data.get("attachments") or data.get("ark_data"):
        # Preserve all visible source fields for on-demand pagination, including branches beyond eager limits.
        segments.append({"type": "dict", "data": {
            "type": "official_message_source",
            "payload": deepcopy({key: data[key] for key in (
                "content", "message_type", "msg_elements", "parallel_message", "attachments", "mentions", "message_reference", "ark_data",
            ) if key in data}),
        }})
    # 官方 @ 事件可能移除机器人提及，只留下空格或换行；不能让空白绕过空消息识别。
    if not segments or all(item["type"] == "text" and not item["data"].strip() for item in segments):
        segments = [{"type": "text", "data": "@毯毯"}]
    at_bot = event_type == "GROUP_AT_MESSAGE_CREATE" or mentions_self(data)
    additional = {"self_id": app_id, "official_endpoint_id": config["id"], "at_bot": at_bot,
                  "is_mentioned": at_bot,
                  "official_member_role": author.get("member_role", "member")}
    additional["user_avatar_url"] = avatar_url(author.get("avatar") or author.get("avatar_url"))
    additional["group_avatar_url"] = avatar_url(data.get("group_avatar"))
    info = {"user_info": {"user_id": identity(app_id, user_id),
                          "user_nickname": author.get("username") or author.get("nickname") or user_id,
                          "user_cardname": author.get("member_name") or author.get("card")},
            "additional_config": additional}
    if not private:
        group = identity(app_id, data["group_openid"])
        info["group_info"] = {"group_id": group, "group_name": data.get("group_name") or config["name"] + " / " + data["group_openid"]}
        additional["platform_io_target_group_id"] = group
    else:
        additional["platform_io_target_user_id"] = identity(app_id, user_id)
    plain = "".join(
        item["data"] if item["type"] == "text" else
        "@" + str(item["data"].get("target_user_cardname") or item["data"]["target_user_nickname"])
        + (f"（昵称：{item['data']['target_user_nickname']}）"
           if item["data"].get("target_user_cardname")
           and item["data"].get("target_user_nickname") != item["data"].get("target_user_cardname") else "")
        if item["type"] == "at" else
        f"引用消息：[{item['data'].get('target_message_sender_cardname') or item['data'].get('target_message_sender_nickname') or '未知人物'}]的id为[{item['data']['target_message_id']}]的消息:[{item['data'].get('target_message_content') or '原消息内容不可用'}]\n当前消息内容:"
        if item["type"] == "reply" else
        "" if item["type"] in {"forward", "dict"} else
        "[附件：" + str(item["data"].get("name") or "未命名") + "]" if item["type"] == "file" else
        "[表情包]" if item["type"] == "emoji" else "[图片]"
        for item in segments
    )
    return {
        "message_id": identity(app_id, data["id"]), "timestamp": str(timestamp), "platform": PLATFORM,
        "message_info": info, "raw_message": segments, "processed_plain_text": plain,
        "display_message": plain, "session_id": "", "is_at": at_bot,
        "is_mentioned": at_bot, "is_emoji": _contains_component(segments, "emoji"),
        "is_picture": _contains_component(segments, "image"), "is_notify": False,
        "is_command": plain.startswith("/"),
    }


def outbound_parts(message):
    text, images, quote_id = [], [], ""
    for part in message.get("raw_message") or []:
        kind = part.get("type")
        data = part.get("data")
        if kind == "text":
            text.append(str(data or ""))
        elif kind == "reply":
            quote_id = str(data.get("target_message_id") or "") if isinstance(data, dict) else str(data or "")
        elif kind in {"image", "emoji"}:
            encoded = part.get("binary_data_base64") or ""
            if not encoded or len(encoded) > 8 * 1024 * 1024:
                raise ValueError("官方端图片缺少正文或超过上传上限")
            images.append(base64.b64decode(encoded, validate=True))
        elif kind == "at" and isinstance(data, dict):
            text.append("@" + str(data.get("target_user_nickname") or data.get("target_user_id") or "用户"))
        else:
            raise ValueError(f"官方端首版尚未支持发送 {kind} 消息组件")
    return "".join(text), images, quote_id
