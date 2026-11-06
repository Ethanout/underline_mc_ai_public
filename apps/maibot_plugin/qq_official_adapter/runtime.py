"""A reconnecting official gateway connection for one AppID."""

from __future__ import annotations

import asyncio
import io
import time
from pathlib import Path
from urllib.parse import urlparse

import aiohttp

from .api import OfficialAPI, OfficialError
from .codec import (
    GATEWAY,
    PLATFORM,
    build_message,
    event_allowed,
    identity,
    outbound_parts,
    raw_identity,
)
from .profiles import enrich_event_profiles
from .state import OfficialState

FATAL_CLOSE_CODES = {4013, 4014, 4914, 4915}
MESSAGE_EVENTS = {"GROUP_AT_MESSAGE_CREATE", "GROUP_MESSAGE_CREATE", "C2C_MESSAGE_CREATE"}


def prepare_upload_image(raw):
    """Keep GIF bytes intact and preserve other animations when converting formats."""
    from PIL import Image
    with Image.open(io.BytesIO(raw)) as image:
        if image.width * image.height > 25_000_000:
            raise ValueError("图片尺寸超过官方端本地处理上限")
        if image.format == "GIF":
            image.verify()
            return raw, "tantan.gif"
        if getattr(image, "is_animated", False):
            if image.n_frames > 500 or image.width * image.height * image.n_frames > 50_000_000:
                raise ValueError("动图解码量超过官方端本地处理上限")
            frames, durations = [], []
            loop = image.info.get("loop", 0)
            for index in range(image.n_frames):
                image.seek(index)
                frames.append(image.convert("RGBA"))
                durations.append(image.info.get("duration", 100))
            output = io.BytesIO()
            frames[0].save(output, format="GIF", save_all=True, append_images=frames[1:],
                           duration=durations, loop=loop, disposal=2)
            return output.getvalue(), "tantan.gif"
        image.seek(0)
        output = io.BytesIO()
        image.convert("RGBA").save(output, format="PNG")
        return output.getvalue(), "tantan.png"


class OfficialConnection:
    def __init__(self, config, gateway, logger, journal, state_dir):
        self.config, self.gateway, self.logger, self.journal = config, gateway, logger, journal
        self.state_dir = Path(state_dir)
        self.state = None
        self.status = {"revision": config["revision"], "status": "connecting", "error": "",
                       "received": 0, "sent": 0, "last_event_at": 0, "last_sent_at": 0, "bot_id": ""}
        self.api = None
        self._send_lock = asyncio.Lock()
        self._cursor = {}
        self._gateway_url = ""
        self._gateway_expires = 0
        self._ack_pending = False
        self._connected_at = 0

    async def _state(self, method, *args):
        return await asyncio.to_thread(getattr(self.state, method), *args)

    def _proactive_state_key(self, target):
        # Permissions can differ by group and change after a configuration update.
        return f"group_proactive_available:{self.config['revision']}:{target}"

    async def _proactive_available(self, target):
        if not self.config["allow_proactive"]:
            return False
        return bool(await self._state("get", self._proactive_state_key(target), True))

    async def ready(self, ready):
        await self.gateway.update_state(
            GATEWAY, ready=ready, platform=PLATFORM, account_id=self.config["app_id"],
            scope=self.config["id"], metadata={"protocol": "qq_official"},
        )

    async def run(self):
        self.state = await asyncio.to_thread(
            OfficialState, self.state_dir / (self.config["id"] + ".sqlite3")
        )
        self._cursor = await self._state("get", "gateway", {})
        timeout = aiohttp.ClientTimeout(total=20)
        try:
            async with aiohttp.ClientSession(timeout=timeout, trust_env=False) as session:
                self.api = OfficialAPI(session, self.config["app_id"], self.config["app_secret"])
                delay = 2
                while True:
                    self.status.update(status="connecting", error="")
                    self._connected_at = 0
                    try:
                        close_code = await self._connect(session)
                        if close_code in FATAL_CLOSE_CODES:
                            self.status.update(status="error", error=f"官方网关拒绝接入（{close_code}），请检查应用状态和权限后重新保存配置")
                            return
                        if close_code in (4006, 4007, 4012):
                            self._cursor = {}
                            await self._state("put", "gateway", {})
                        if close_code == 4010:
                            self.status.update(status="error", error="官方网关拒绝分片参数（4010）")
                            return
                        self.status.update(status="offline", error=f"连接断开（{close_code or '网络断开'}），正在重连")
                        stable = self._connected_at and time.monotonic() - self._connected_at >= 60
                        delay = 2 if stable else min(60, delay * 2)
                    except asyncio.CancelledError:
                        raise
                    except OfficialError as exc:
                        self.status.update(status="error", error=str(exc))
                        if exc.code in (100007, 100016):
                            return
                        delay = min(60, delay * 2)
                    except Exception as exc:
                        # Exception strings can contain signed URLs or tokens. Report only the type.
                        self.status.update(status="offline", error=f"官方连接失败（{type(exc).__name__}），正在重连")
                        delay = min(60, delay * 2)
                    finally:
                        await self.ready(False)
                    await asyncio.sleep(delay)
        finally:
            await self.ready(False)
            if self.state is not None:
                await self._state("close")

    async def _connect(self, session):
        if time.time() >= self._gateway_expires:
            self._gateway_url = (await self.api.request("GET", "/gateway"))["url"]
            self._gateway_expires = time.time() + 600
        if urlparse(self._gateway_url).scheme != "wss":
            raise ValueError("官方网关未返回安全的 WSS 地址")
        async with session.ws_connect(self._gateway_url, max_msg_size=8 * 1024 * 1024) as ws:
            hello = await ws.receive_json(timeout=20)
            if hello.get("op") != 10:
                raise ValueError("官方网关未返回 Hello")
            interval = max(1, float(hello["d"]["heartbeat_interval"]) / 1000)
            token = "QQBot " + await self.api.token()
            if self._cursor.get("session_id") and self._cursor.get("seq") is not None:
                await ws.send_json({"op": 6, "d": {"token": token, **self._cursor}})
            else:
                await ws.send_json({"op": 2, "d": {"token": token, "intents": 1 << 25, "shard": [0, 1]}})
            self._ack_pending = False
            heartbeat = asyncio.create_task(self._heartbeat(ws, interval))
            queue = asyncio.Queue(maxsize=64)
            receiver = asyncio.create_task(self._receive_frames(ws, queue))
            processor = asyncio.create_task(self._process_frames(queue, session))
            drain = None
            try:
                done, _ = await asyncio.wait([receiver, processor, heartbeat], return_when=asyncio.FIRST_COMPLETED)
                if processor in done:
                    await processor
                if receiver not in done:
                    await heartbeat
                    return 4009
                close_code = await receiver
                # Media downloads must not block ACK reception. Drain bounded queued work on disconnect;
                # anything not committed is replayed from the last durable cursor on Resume.
                drain = asyncio.create_task(queue.join())
                done, _ = await asyncio.wait([drain, processor], timeout=30, return_when=asyncio.FIRST_COMPLETED)
                if processor in done:
                    await processor
                if close_code == 4006:
                    self._cursor = {}
                    await self._state("put", "gateway", {})
                return close_code
            finally:
                tasks = [heartbeat, receiver, processor] + ([drain] if drain else [])
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _receive_frames(self, ws, queue):
        async for message in ws:
            if message.type != aiohttp.WSMsgType.TEXT:
                if message.type == aiohttp.WSMsgType.ERROR:
                    raise ConnectionError("官方网关连接异常")
                continue
            payload = message.json()
            op = payload.get("op")
            if op == 11:
                self._ack_pending = False
            elif op == 7:
                return 4009
            elif op == 9:
                return 4006
            elif op == 0:
                if queue.full():
                    return 4009
                queue.put_nowait(payload)
        return ws.close_code

    async def _process_frames(self, queue, session):
        while True:
            payload = await queue.get()
            try:
                await self._dispatch(payload, session)
            finally:
                queue.task_done()

    async def _heartbeat(self, ws, interval):
        try:
            while True:
                await asyncio.sleep(interval)
                if self._ack_pending:
                    await ws.close(code=4009)
                    return
                self._ack_pending = True
                await ws.send_json({"op": 1, "d": self._cursor.get("seq")})
        except asyncio.CancelledError:
            raise
        except Exception:
            await ws.close(code=4009)

    async def _dispatch(self, payload, session):
        event_type, data = payload.get("t"), payload.get("d") or {}
        if data.get("group_openid"):
            # Record transport metadata before filtering, without message text or scene tokens.
            self.logger.debug(
                f"官方网关入站: event={event_type} group={data['group_openid']} "
                f"message_type={data.get('message_type')} content_length={len(data.get('content') or '')} "
                f"attachment_count={len(data.get('attachments') or [])} element_count={len(data.get('msg_elements') or [])}"
            )
        if event_type == "READY":
            self._cursor = {"session_id": data["session_id"], "seq": payload.get("s")}
            self.status["bot_id"] = str((data.get("user") or {}).get("id") or "")
        if event_type in {"READY", "RESUMED"}:
            self._connected_at = time.monotonic()
            self.status.update(status="online", error="")
            await self.ready(True)
        if event_type in MESSAGE_EVENTS and event_allowed(self.config, event_type, data):
            event_id = str(data.get("id") or "")
            if not event_id:
                raise ValueError("官方消息缺少稳定 ID")
            if not await self._state("seen", event_id):
                enriched = await asyncio.to_thread(enrich_event_profiles, self.state, event_type, data)
                enriched = await self._state("resolve_event_references", event_type, enriched)
                message = await build_message(self.config, event_type, enriched, session)
                message["message_info"]["additional_config"]["official_proactive_available"] = (
                    await self._proactive_available(str(data.get("group_openid") or ""))
                )
                private = event_type == "C2C_MESSAGE_CREATE"
                author = data.get("author") or {}
                target = str(author.get("user_openid") or author.get("id")) if private else str(data["group_openid"])
                scene = data.get("message_scene") or {}
                ref_idx = next((item.partition("=")[2] for item in scene.get("ext", [])
                                if isinstance(item, str) and item.startswith("msg_idx=")), "")
                await self._state("remember", event_id, target, private, float(message["timestamp"]), True, ref_idx)
                # Persist source before advancing the gateway cursor. A service failure is retried.
                await self.journal(self.config["id"], {"event_type": event_type, "data": data})
                accepted = await self.gateway.route_message(
                    GATEWAY, message,
                    route_metadata={"self_id": self.config["app_id"], "connection_id": self.config["id"]},
                    external_message_id=message["message_id"], dedupe_key=message["message_id"],
                )
                if not accepted:
                    self.logger.info("官方消息已记录，但被麦麦接收规则过滤")
                await self._state("mark", event_id, time.time())
                self.status["received"] += 1
                self.status["last_event_at"] = time.time()
        if payload.get("s") is not None:
            self._cursor["seq"] = payload["s"]
            await self._state("put", "gateway", self._cursor)

    async def send(self, message, route):
        if self.status["status"] != "online" or self.api is None:
            raise ValueError("官方端尚未连接，消息未发送")
        info = message.get("message_info") or {}
        group = (info.get("group_info") or {}).get("group_id")
        extra = info.get("additional_config") or {}
        private = not bool(group)
        canonical = str(group or extra.get("platform_io_target_user_id") or route.get("target_user_id") or "")
        target = raw_identity(self.config["app_id"], canonical)
        if private:
            if not self.config["allow_private"] or (self.config["private_users"] and target not in self.config["private_users"]):
                raise ValueError("官方端未允许与该用户私聊")
        elif self.config["groups"] and target not in self.config["groups"]:
            raise ValueError("群不在官方端允许名单内")
        text, images, quote_id = outbound_parts(message)
        quote_raw = raw_identity(self.config["app_id"], quote_id) if quote_id else ""
        async with self._send_lock:
            reference = await self._state("reply_target", target, private, quote_raw)
            if quote_raw and reference is None:
                raise ValueError("引用消息不属于当前会话或无法取得，消息未发送")
            # 被动回复凭据 id 与客户端引用索引 ref_idx 是两套不同标识。
            # 自己刚发的消息必须使用发送响应 ext_info.ref_idx，不能把 ROBOT1.0 id 填入引用框。
            quote_index = reference["ref_idx"] if quote_raw else ""
            if quote_raw and not quote_index:
                raise ValueError("目标消息缺少官方引用索引 ref_idx，无法发送有效引用；请使用修复后新收发的消息")
            if reference and not reference["incoming"]:
                reference = await self._state("reply_target", target, private)
            valid = reference and time.time() - reference["ts"] < (3600 if private else 300)
            if not private and extra.get("reply_continuation") is True:
                # 群被动文本回复会由QQ自动加@。后续无引用分段按配置尝试主动发送，
                # 不影响首段被动回复或纠错段对自己上一条消息的真实引用。
                if not self.config["allow_proactive"]:
                    raise ValueError("连续回复的后续分段需开启官方端主动发送，避免QQ重复自动@；本段未发送")
                valid = False
            if not valid and not self.config["allow_proactive"]:
                raise ValueError("已超过官方被动回复时限；当前端未开启主动发送")
            if not private and not valid and not await self._proactive_available(target):
                raise ValueError("官方已拒绝当前群主动发送；调整平台权限后保存端配置以重新尝试，本段未发送")
            if not text.strip() and not images:
                raise ValueError("消息正文为空")
            results = []
            payloads = ([{"msg_type": 0, "content": text}] if text.strip() else [])
            # Convert every image before sending, so unsupported images cannot cause partial text sends.
            converted = [await asyncio.to_thread(prepare_upload_image, raw) for raw in images]
            for raw, filename in converted:
                uploaded = await self.api.upload(target, private, raw, filename)
                payloads.append({"msg_type": 7, "media": {"file_info": uploaded["file_info"]}})
            sequences = (await self._state("reserve_replies", reference["id"], 4 if private else 5, len(payloads))) if valid else []
            for index, payload in enumerate(payloads):
                if valid:
                    payload["msg_id"] = reference["id"]
                    payload["msg_seq"] = sequences[index]
                if quote_raw:
                    payload["message_reference"] = {"message_id": quote_index}
                try:
                    response = await self.api.request("POST", self.api.target_path(target, private) + "/messages", payload)
                except Exception as exc:
                    if not private and not valid and isinstance(exc, OfficialError) and exc.code == 40034105:
                        await self._state("put", self._proactive_state_key(target), False)
                    detail = str(exc) if isinstance(exc, OfficialError) else type(exc).__name__
                    raise ValueError(f"官方发送失败；已成功{len(results)}条，未自动重发。{detail}") from exc
                results.append(response["id"])
                if not private and not valid:
                    await self._state("put", self._proactive_state_key(target), True)
                ref_idx = (response.get("ext_info") or {}).get("ref_idx") or ""
                await self._state("remember", response["id"], target, private, time.time(), False, ref_idx)
                self.status["sent"] += 1
                self.status["last_sent_at"] = time.time()
            return identity(self.config["app_id"], results[-1])
