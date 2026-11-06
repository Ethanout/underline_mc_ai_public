"""Official QQ HTTP API; credentials and HTTP failures never enter chat text."""

from __future__ import annotations

import asyncio
import time
from typing import Any
from urllib.parse import quote

API_URL = "https://api.bot.qq.com"
TOKEN_URL = API_URL + "/app/getAppAccessToken"
ERRORS = {
    100007: "AppID 无效或机器人状态异常", 100016: "AppID 或 AppSecret 不正确",
    304103: "被动回复消息已过期", 40034005: "被动回复消息已过期",
    40034100: "主动消息超过官方频率限制", 40034105: "没有主动消息权限",
    40034128: "被动回复时间或次数超限", 40054002: "机器人在当前群被禁言",
    40054003: "机器人不是当前群成员", 40054005: "消息被官方去重",
    40054010: "当前权限不允许发送 URL", 40054016: "官方机器人已下线",
    850019: "官方接口不支持这个媒体格式", 850026: "官方服务器下载媒体失败",
}


class OfficialError(RuntimeError):
    def __init__(self, code: Any, detail="官方接口请求失败"):
        self.code = code
        super().__init__(f"{ERRORS.get(code, detail)}（错误码 {code}）")


class OfficialAPI:
    def __init__(self, session, app_id, app_secret, clock=time.time):
        self.session = session
        self.app_id = app_id
        self.app_secret = app_secret
        self.clock = clock
        self._token = ""
        self._expires = 0.0
        self._token_lock = asyncio.Lock()

    async def token(self):
        async with self._token_lock:
            if self._token and self.clock() < self._expires:
                return self._token
            async with self.session.post(
                TOKEN_URL, json={"appId": self.app_id, "clientSecret": self.app_secret}
            ) as response:
                value = await response.json(content_type=None)
                if response.status != 200 or value.get("code") not in (None, 0):
                    raise OfficialError(value.get("code", response.status), "官方应用鉴权失败")
            if not value.get("access_token"):
                raise OfficialError("invalid_token_response", "鉴权响应缺少 access_token")
            self._token = value["access_token"]
            self._expires = self.clock() + max(1, float(value["expires_in"]) - 60)
            return self._token

    async def request(self, method, path, payload=None):
        for attempt in range(2):
            token = await self.token()
            async with self.session.request(
                method, API_URL + path, json=payload,
                headers={"Authorization": "QQBot " + token, "X-Union-Appid": self.app_id},
            ) as response:
                value = await response.json(content_type=None)
                if response.status == 401 and attempt == 0:
                    self._expires = 0
                    continue
                if response.status >= 400 or value.get("code") not in (None, 0):
                    raise OfficialError(value.get("code", response.status))
                return value
        raise OfficialError(401, "官方应用凭证已失效")

    @staticmethod
    def target_path(target, private):
        return "/v2/" + ("users/" if private else "groups/") + quote(target, safe="")

    async def upload(self, target, private, raw, filename):
        import base64
        if len(raw) > 5 * 1024 * 1024:
            raise OfficialError("media_too_large", "首版官方端仅支持不超过5 MiB的图片")
        return await self.request("POST", self.target_path(target, private) + "/files", {
            "file_type": 1, "srv_send_msg": False, "file_name": filename,
            "file_data": base64.b64encode(raw).decode("ascii"),
        })
