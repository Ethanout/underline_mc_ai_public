"""Task-bound tool permissions are rechecked on every invocation."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass

from .runtime import RuntimeSettings
from .store import dumps


def admin_ids():
    return {
        item.strip() for item in os.environ.get("QQBOT_ADMIN_IDS", "").split(",") if item.strip()
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
        vector_search=None,
        image_view=None,
        max_items=None,
        max_chars=None,
    ):
        self.store, self.onebot, self.vector_search, self.image_view = (
            store,
            onebot,
            vector_search,
            image_view,
        )
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
        self.runtime = RuntimeSettings(store)
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
            "search_memory",
            self.search_memory,
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
        self.register(
            "remember", self.remember, True, ("unrelated",), properties={"content": "string"}
        )
        self.register(
            "forget", self.forget, True, ("unrelated",), properties={"memory_id": "string"}
        )
        self.register(
            "adjust_runtime",
            lambda t, a: self.runtime.adjust(a["name"], a["value"], a["reason"]),
            properties={"name": "string", "value": "number", "reason": "string"},
        )
        self.register("reset_runtime", self.reset_runtime, True)
        self.register(
            "record_memory_use",
            self.record_memory_use,
            libraries=("related",),
            properties={"memory_id": "string", "position": "string", "quality": "number"},
        )

    def register(
        self, name, handler, admin_only=False, libraries=("chat",), properties=None, parameters=None
    ):
        schema = parameters or {key: {"type": kind} for key, kind in (properties or {}).items()}
        self.definitions[name] = Tool(
            handler,
            admin_only,
            libraries,
            {"type": "object", "properties": schema},
            "仅返回实际取得的资料，不能补造缺失历史。",
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
            if args.get("category") == "unrelated" and not self.is_admin(task):
                raise PermissionError("普通成员不能读取无关库")
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
        keyword = str(args.get("keyword", ""))
        rows = self.store.messages(task["group_id"])
        speaker = args.get("speaker")
        cutoff = self.store.clock() - max(0, float(args.get("days", 36500))) * 86400
        rows = [
            r
            for r in rows
            if keyword in self.store.text(r)
            and r["ts"] >= cutoff
            and (not speaker or str(speaker) in (r["user_id"], r["nickname"], r["card"]))
        ]
        if self.vector_search:
            hits = self.vector_search(task["group_id"], keyword)
            for hit in hits:
                row = self.store.message(task["group_id"], hit["id"])
                if row and row["id"] not in {r["id"] for r in rows}:
                    rows.append(row)
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

    def search_memory(self, task, args):
        queries = args.get("queries", [])
        if not isinstance(queries, list) or not 1 <= len(queries) <= 3:
            raise ValueError("记忆检索需要 1–3 条查询")
        rows = self.store.rows("SELECT * FROM memory_state WHERE group_id=?", (task["group_id"],))
        hits = {}
        for row in rows:
            if row["category"] != "related" and not self.is_admin(task):
                continue
            if json.loads(row["state"]).get("merged_into"):
                continue
            if any(str(query) in row["content"] for query in queries):
                label = (
                    "约定"
                    if row["kind"] == "note" and row["author"] in admin_ids()
                    else row["kind"]
                )
                hits[row["id"]] = {**row, "label": label, "date": row["updated"]}
        for query in queries:
            for row in self.search_chat(task, {"keyword": query})["messages"]:
                hits[row["id"]] = {**row, "label": "聊天", "date": row["ts"]}
        return {"results": list(hits.values())}

    def remember(self, task, args):
        content = str(args.get("content", "")).strip()
        if not content:
            raise ValueError("记忆内容不能为空")
        mid = "note:" + uuid.uuid4().hex
        metadata = {
            "author_name": task["nickname"],
            "strength": 86400,
            "activation": 0,
            "last_used": self.store.clock(),
            "evidence": [],
        }
        self.store.write(
            "INSERT INTO memory_state VALUES(?,?,?,?,?,?,?,?,?)",
            (
                mid,
                task["group_id"],
                "unrelated",
                "note",
                task["user_id"],
                f"{task['nickname'] or task['user_id']}说他倾向于：{content}；可根据当时情境回应。",
                dumps([]),
                dumps(metadata),
                self.store.clock(),
            ),
        )
        self.store.memory_change(mid, "remember", {"author": task["user_id"]})
        return {"id": mid, "label": "约定"}

    def forget(self, task, args):
        rows = self.store.rows(
            "SELECT * FROM memory_state WHERE id=? AND group_id=?",
            (args.get("memory_id"), task["group_id"]),
        )
        if not rows or rows[0]["kind"] != "note":
            raise ValueError("只能删除当前群的 note，不能删除聊天原文")
        self.store.recycle(rows[0])
        return {"status": "recycled"}

    def reset_runtime(self, task, args):
        self.store.write("DELETE FROM runtime_overrides")
        return {"status": "reset"}

    def view_image(self, task, args):
        mid = self._message_id(task, args["message_id"])
        row = self.store.message(task["group_id"], mid)
        if not row:
            return {"images": [], "missing": [mid]}
        if not self.image_view:
            raise RuntimeError("图片输入工具未配置")
        return self.image_view(json.loads(row["raw"]))

    def record_memory_use(self, task, args):
        from .memory_model import MemoryService

        return MemoryService(self.store).record_use(
            task["group_id"],
            args["memory_id"],
            args["position"],
            float(args.get("quality", 1)),
            allow_unrelated=self.is_admin(task),
        )
