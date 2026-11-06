"""Persist connection settings separately from chat identity and knowledge."""

from __future__ import annotations

import re
import uuid

from .store import Store

OFFICIAL_CAPABILITIES = {
    "group_chat": True, "private_chat": True, "images": True,
    "all_group_messages": "需在官方平台开启接收所有消息",
    "history": "仅支持网关短时重连补发，不支持任意历史查询",
    "essence": False, "list_group_files": False,
}


class Endpoints:
    def __init__(self, store: Store):
        self.store = store

    def configs(self, *, private=False):
        rows = self.store.rows("SELECT value FROM state WHERE key LIKE 'endpoint:config:%' ORDER BY key")
        import json
        configs = [json.loads(row["value"]) for row in rows]
        return configs if private else [self.public(row) for row in configs]

    def get(self, endpoint_id):
        if not re.fullmatch(r"official-[a-f0-9]{12}", endpoint_id):
            raise ValueError("端 ID 无效")
        config = self.store.get_state("endpoint:config:" + endpoint_id, None)
        if config is None:
            raise ValueError("端不存在")
        return config

    def save(self, values, endpoint_id=None):
        previous = self.get(endpoint_id) if endpoint_id else {}
        endpoint_id = endpoint_id or "official-" + uuid.uuid4().hex[:12]
        config = {**previous, **values, "id": endpoint_id, "kind": "qq_official"}
        # An empty password field means keep the existing secret.
        config["app_secret"] = values.get("app_secret") or previous.get("app_secret", "")
        config.setdefault("enabled", False)
        config.setdefault("name", "官方 QQ 机器人")
        config.setdefault("app_id", "")
        config.setdefault("groups", [])
        config.setdefault("private_users", [])
        config.setdefault("allow_private", False)
        config.setdefault("allow_proactive", False)
        config.setdefault("receive_all", False)
        config.setdefault("group_bindings", {})
        config.setdefault("knowledge_groups", {})
        for field in ("group_bindings", "knowledge_groups"):
            mapping = config[field]
            if not isinstance(mapping, dict) or len(mapping) > 200:
                raise ValueError("群资料绑定必须是最多 200 项的对象")
            for openid, targets in mapping.items():
                if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", openid):
                    raise ValueError("群资料绑定的 OpenID 无效")
                targets = [targets] if field == "group_bindings" else targets
                if (not isinstance(targets, list) or len(targets) > 200
                        or any(not isinstance(g, str) or not re.fullmatch(r"[0-9]{1,32}", g) for g in targets)):
                    raise ValueError("旧群资料来源必须填写数字群号")
        if config["app_id"] and not re.fullmatch(r"[0-9]{1,32}", config["app_id"]):
            raise ValueError("AppID 必须是数字，群和用户名单请填写 OpenID")
        if config["enabled"] and (not config["app_id"] or not config["app_secret"]):
            raise ValueError("启用官方端前需要填写 AppID 和 AppSecret")
        for other in self.configs(private=True):
            if other["id"] != endpoint_id and config["app_id"] and other["app_id"] == config["app_id"]:
                raise ValueError("这个 AppID 已有接入端，请编辑原有端，避免重复连接")
        config["revision"] = previous.get("revision", 0) + 1
        self.store.set_state("endpoint:config:" + endpoint_id, config)
        return self.public(config)

    def read_groups(self, group_id: str, *, knowledge: bool = False) -> list[str]:
        """Explicit read aliases only; never change task identity or grant write rights."""
        groups = [group_id]
        parts = group_id.split(":")
        if len(parts) != 3 or parts[0] != "official":
            return groups
        _, app_id, openid = parts
        for config in self.configs(private=True):
            if (not config["enabled"] or config["app_id"] != app_id
                    or (config["groups"] and openid not in config["groups"])):
                continue
            bound = config.get("group_bindings", {}).get(openid)
            if bound:
                groups.append(bound)
            if knowledge:
                groups.extend(config.get("knowledge_groups", {}).get(openid, []))
        return list(dict.fromkeys(groups))

    def public(self, config):
        value = {key: item for key, item in config.items() if key != "app_secret"}
        value["secret_configured"] = bool(config.get("app_secret"))
        runtime = self.store.get_state("endpoint:runtime:" + config["id"], {})
        current = runtime.get("revision") == config.get("revision")
        fresh = self.store.clock() - runtime.get("updated", 0) < 45
        if not config.get("enabled"):
            status = "disabled"
        elif not current:
            status = "pending"
        elif not fresh:
            status = "offline"
        else:
            status = runtime.get("status", "pending")
        value["runtime"] = {**runtime, "status": status, "fresh": fresh}
        value["capabilities"] = OFFICIAL_CAPABILITIES
        prefix = f"official:{config['app_id']}:"
        value["seen_groups"] = [
            row["group_id"][len(prefix):] for row in self.store.rows(
                "SELECT DISTINCT group_id FROM messages WHERE group_id LIKE ? LIMIT 200", (prefix + "%",)
            )
        ]
        return value

    def report(self, endpoint_id, values):
        config = self.get(endpoint_id)
        if values.get("revision") != config["revision"]:
            return False
        # Never persist raw transport exceptions, tokens, or arbitrary bridge data.
        allowed = {"revision", "status", "error", "received", "sent", "last_event_at", "last_sent_at", "bot_id"}
        status = {key: value for key, value in values.items() if key in allowed}
        status["updated"] = self.store.clock()
        self.store.set_state("endpoint:runtime:" + endpoint_id, status)
        return True

    def remove(self, endpoint_id):
        config = self.get(endpoint_id)
        if config["enabled"]:
            raise ValueError("请先停用这个端，再移除配置；聊天和知识记录会保留")
        self.store.write("DELETE FROM state WHERE key IN (?, ?)",
                         ("endpoint:config:" + endpoint_id, "endpoint:runtime:" + endpoint_id))
