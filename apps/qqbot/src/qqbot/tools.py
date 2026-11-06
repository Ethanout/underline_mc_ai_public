"""Task-bound tool permissions are rechecked on every invocation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from . import docs
from .store import dumps


def admin_ids():
    return {
        item.strip() for item in os.environ.get("QQBOT_ADMIN_IDS", "").split(",") if item.strip()
    }


NO_INVENTION = "仅返回实际取得的资料，不能补造缺失历史。"
DESCRIPTIONS = {
    "search_chat": "按关键词在本群聊天记录里找消息，可限定发言人和最近几天。",
    "read_chat_around": "读某条消息前后的聊天。",
    "read_history": "读发起消息（或它引用的消息）之前的若干条，或者一段编号范围。",
    "read_quoted": "读某条消息引用的原消息。",
    "read_forward": "读本群出现过的合并转发。",
    "read_essence": "读本群的精华消息列表。",
    "view_image": "看某条消息里的图片。",
    "search_knowledge": "查本群的数据包技巧库、Underline 的教程和 mcfunction 资料，再查聊天记录。技巧是 AI 整理、未验证的。",
    "collect_tricks": "把一段聊天、一条合并转发或精华里的数据包技术内容收进技巧库（管理员）。",
    "read_file": "读本机文件（管理员）。配置和密钥文件读不了。",
    "write_file": "写本机文件（管理员）。",
    "run_command": "在本机执行命令（管理员）。",
    "web_read": "读一个网页（管理员）。",
    "web_search": "网页搜索（管理员）。",
}


@dataclass
class Tool:
    handler: object
    admin_only: bool
    libraries: tuple
    parameters: dict
    description: str


class ToolRegistry:
    def __init__(
        self,
        store,
        onebot=None,
        image_view=None,
        max_items=None,
        max_chars=None,
    ):
        self.store, self.onebot, self.image_view = store, onebot, image_view
        self.max_items = max(
            1,
            int(
                max_items if max_items is not None else os.environ.get("QQBOT_TOOL_MAX_ITEMS", "20")
            ),
        )
        self.max_chars = max(
            200,
            int(
                max_chars
                if max_chars is not None
                else os.environ.get("QQBOT_TOOL_MAX_CHARS", "12000")
            ),
        )
        self.definitions = {}
        self.register(
            "search_chat",
            self.search_chat,
            properties={
                "keyword": "string",
                "speaker": "string",
                "days": "number",
                "limit": "integer",
            },
        )
        self.register(
            "read_chat_around",
            self.read_chat_around,
            properties={"message_id": "string", "before": "integer", "after": "integer"},
        )
        self.register(
            "read_history",
            self.read_history,
            properties={
                "count": "integer",
                "quote_id": "string",
                "start_id": "string",
                "end_id": "string",
            },
        )
        self.register("read_quoted", self.read_quoted, properties={"message_id": "string"})
        self.register("read_forward", self.read_forward, properties={"forward_id": "string"})
        self.register("read_essence", self.read_essence)
        self.register("view_image", self.view_image, properties={"message_id": "string"})
        self.register(
            "search_knowledge",
            self.search_knowledge,
            libraries=("related", "chat"),
            parameters={
                "queries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 3,
                }
            },
        )

    def register(
        self,
        name,
        handler,
        admin_only=False,
        libraries=("chat",),
        properties=None,
        parameters=None,
        description="",
    ):
        schema = parameters or {key: {"type": kind} for key, kind in (properties or {}).items()}
        self.definitions[name] = Tool(
            handler,
            admin_only,
            libraries,
            {"type": "object", "properties": schema},
            (description or DESCRIPTIONS.get(name, "")) + NO_INVENTION,
        )

    def bound_task(self, task):
        bound = self.store.task(task["id"])
        if not bound or any(str(bound[key]) != str(task[key]) for key in ("group_id", "user_id")):
            raise PermissionError("任务身份不匹配")
        return bound

    def is_admin(self, task):
        return str(task["user_id"]) in admin_ids()

    def tools_for(self, task):
        task = self.bound_task(task)
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": spec.description,
                    "parameters": spec.parameters,
                },
            }
            for name, spec in sorted(self.definitions.items())
            if not spec.admin_only or self.is_admin(task)
        ]

    def execute(self, task, name, args=None):
        args = args or {}
        denied = False
        try:
            task = self.bound_task(task)
            spec = self.definitions.get(name)
            if spec is None or (spec.admin_only and not self.is_admin(task)):
                raise PermissionError("没有权限调用这个工具")
            if not isinstance(args, dict):
                raise ValueError("工具参数必须是对象")
            if "group_id" in args and str(args["group_id"]) != task["group_id"]:
                raise PermissionError("不能跨群读取资料")
            result = spec.handler(task, args)
        except PermissionError as exc:
            denied = True
            result = {"error": str(exc)}
        except (ValueError, KeyError, OSError, RuntimeError, TypeError) as exc:
            result = {"error": str(exc)}
        # Keep full results in the local audit. Only model-facing results are bounded.
        self.store.audit(task, name, args, result, denied)
        return self._bounded(result)

    def _bounded(self, result):
        result = json.loads(dumps(result))
        if not isinstance(result, dict):
            result = {"result": result}
        for key in ("messages", "results", "images"):
            if isinstance(result.get(key), list) and len(result[key]) > self.max_items:
                omitted = result[key][self.max_items :]
                result[key] = result[key][: self.max_items]
                if key == "messages":
                    result.setdefault("missing", []).append(
                        {
                            "truncated_count": len(omitted),
                            "first_id": omitted[0].get("message_id", omitted[0].get("id")),
                            "last_id": omitted[-1].get("message_id", omitted[-1].get("id")),
                        }
                    )
                result["truncated"] = True
        if len(dumps(result)) > self.max_chars:
            for key in ("messages", "results"):
                while result.get(key) and len(dumps(result)) > self.max_chars:
                    row = result[key].pop()
                    result.setdefault("missing", []).append(
                        row.get("message_id", row.get("id", "结果超预算"))
                    )
                    result["truncated"] = True
            if len(dumps(result)) > self.max_chars:
                result = {
                    "content": dumps(result)[: max(0, self.max_chars - 150)],
                    "truncated": True,
                }
        return result

    def _message_id(self, task, mid):
        if ":" in str(mid) and not str(mid).startswith(task["group_id"] + ":"):
            raise PermissionError("不能跨群读取消息")
        return str(mid).removeprefix(task["group_id"] + ":")

    def _output(self, rows, missing=()):
        return {
            "messages": [{**row, "text": self.store.text(row)} for row in rows],
            "order": "asc",
            "missing": list(missing),
        }

    def search_chat(self, task, args):
        from .endpoints import Endpoints

        keyword = str(args.get("keyword", ""))
        rows = [row for group in Endpoints(self.store).read_groups(task["group_id"])
                for row in self.store.messages(group)]
        speaker = args.get("speaker")
        cutoff = self.store.clock() - max(0, float(args.get("days", 36500))) * 86400
        rows = [
            r
            for r in rows
            if keyword in self.store.text(r)
            and r["ts"] >= cutoff
            and (not speaker or str(speaker) in (r["user_id"], r["nickname"], r["card"]))
        ]
        rows.sort(key=lambda r: (r["ts"], r["id"]))
        limit = max(0, min(self.max_items, int(args.get("limit", self.max_items))))
        return self._output(rows[-limit:] if limit else [])

    def read_chat_around(self, task, args):
        mid = self._message_id(task, args["message_id"])
        rows = self.store.messages(task["group_id"])
        index = next((i for i, row in enumerate(rows) if row["message_id"] == mid), None)
        if index is None:
            return self._output([], [mid])
        before, after = max(0, int(args.get("before", 5))), max(0, int(args.get("after", 5)))
        missing = []
        if index < before:
            missing.append({"before": mid, "count": before - index})
        if index + after >= len(rows):
            missing.append({"after": mid, "count": index + after + 1 - len(rows)})
        return self._output(rows[max(0, index - before) : index + after + 1], missing)

    def read_history(self, task, args):
        rows = self.store.messages(task["group_id"])
        count = max(0, min(1000, int(args.get("count", 10))))
        positions = {r["message_id"]: i for i, r in enumerate(rows)}
        if "start_id" in args or "end_id" in args:
            start = self._message_id(
                task, args.get("start_id", rows[0]["message_id"] if rows else "")
            )
            end = self._message_id(task, args.get("end_id", rows[-1]["message_id"] if rows else ""))
            missing = [mid for mid in (start, end) if mid not in positions]
            if missing:
                return self._output([], missing)
            return self._output(rows[positions[start] : positions[end] + 1])
        trigger = self.store.message(task["group_id"], task["trigger_id"])
        quote = args.get("quote_id") or (trigger["quote_id"] if trigger else "")
        anchor = self._message_id(task, quote or task["trigger_id"])
        if anchor not in positions:
            return self._output([], [anchor])
        stop = positions[anchor] + (1 if quote else 0)
        start = max(0, stop - count)
        return self._output(
            rows[start:stop],
            [{"before": anchor, "count": count - (stop - start)}] if stop - start < count else [],
        )

    def read_quoted(self, task, args):
        mid = self._message_id(task, args.get("message_id", task["trigger_id"]))
        row = self.store.message(task["group_id"], mid)
        quote = row["quote_id"] if row else ""
        target = self.store.message(task["group_id"], quote) if quote else None
        return self._output([target] if target else [], [] if target else [quote or mid])

    def _call(self, action, params):
        if not self.onebot:
            raise RuntimeError("OneBot 工具未配置")
        return self.onebot(action, params)

    def read_forward(self, task, args):
        fid = str(args["forward_id"])
        # A forward id is readable only after its source appeared in this group.
        referenced = any(
            s.get("type") == "forward" and str(s.get("data", {}).get("id")) == fid
            for row in self.store.messages(task["group_id"])
            for s in json.loads(row["segments"])
        )
        if not referenced:
            raise PermissionError("合并转发不属于当前群的已知消息")
        data = self._call("get_forward_msg", {"id": fid})
        from .essence_exporter import find_list

        messages = find_list(data)
        for message in messages:
            if message.get("group_id") is not None and str(message["group_id"]) != task["group_id"]:
                raise PermissionError("不能跨群读取合并转发")
        return {
            "messages": sorted(messages, key=lambda m: float(m.get("time", 0))),
            "order": "asc",
            "missing": [] if messages else [fid],
        }

    def read_essence(self, task, args):
        from .essence_exporter import find_list, has_message_content, message_id

        rows = find_list(self._call("get_essence_msg_list", {"group_id": task["group_id"]}))
        result, missing = [], []
        for row in rows:
            mid = message_id(row)
            if row.get("group_id") is not None and str(row["group_id"]) != task["group_id"]:
                raise PermissionError("不能跨群读取精华")
            if not has_message_content(row):
                local = self.store.message(task["group_id"], mid)
                if local:
                    row = {**row, "message": json.loads(local["segments"])}
                else:
                    missing.append(mid)
            result.append(row)
        return {
            "messages": sorted(result, key=lambda r: float(r.get("time", 0))),
            "order": "asc",
            "missing": missing,
        }

    def search_knowledge(self, task, args):
        """The group's trick library, Underline's docs, then chat history, for 1-3 keywords."""
        queries = args.get("queries", [])
        if not isinstance(queries, list) or not 1 <= len(queries) <= 3:
            raise ValueError("检索需要 1–3 条关键词")
        queries = [str(query) for query in queries if str(query).strip()]
        if not queries:
            raise ValueError("检索关键词不能为空")
        hits = {}
        from .endpoints import Endpoints

        groups = Endpoints(self.store).read_groups(task["group_id"], knowledge=True)
        placeholders = ",".join("?" for _ in groups)
        rows = self.store.rows(
            f"SELECT * FROM memory_state WHERE group_id IN ({placeholders}) AND kind='trick'", groups
        )
        for row in rows:
            if any(query in row["content"] for query in queries):
                hits[row["id"]] = {
                    "id": row["id"],
                    "label": "技巧（AI 整理、未验证）",
                    "content": row["content"],
                    "sources": json.loads(row["sources"]),
                    "date": row["updated"],
                    "group_id": row["group_id"],
                }
        for query in queries:
            for row in docs.library().search(query, limit=4):
                hits.setdefault(row["id"], row)
        from .research import ResearchLibrary

        research = ResearchLibrary(self.store)
        for query in queries:
            for group in groups:
                for row in research.search(group, query):
                    hits.setdefault(row["id"], {**row, "group_id": group})
        for query in queries:
            for row in self.search_chat(task, {"keyword": query})["messages"]:
                hits[row["id"]] = {**row, "label": "聊天", "date": row["ts"]}
        return {"results": list(hits.values())}

    def view_image(self, task, args):
        mid = self._message_id(task, args["message_id"])
        row = self.store.message(task["group_id"], mid)
        if not row:
            return {"images": [], "missing": [mid]}
        if not self.image_view:
            raise RuntimeError("图片输入工具未配置")
        return self.image_view(json.loads(row["raw"]))
