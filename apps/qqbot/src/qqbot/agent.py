"""Persist task and tool checkpoints without requiring LangGraph at import."""
from __future__ import annotations

import json
import os
import time
import urllib.request

from .prompts import AGENT_SYSTEM_PROMPT
from .store import dumps

EMOTION_RULES = "兴奋是参与欲，心情是愉快程度，兴趣是关注度，精力是可用能量，烦躁是厌烦程度，亲近是熟悉感。"
CHAT_RULES = "你在刷群，接着这段聊天说话。回应 >> 标记的人，同时顾及前面的话题。工具只报告实际取得的资料，缺失历史不能补造。"


def make_post(api_key, timeout=45):
    def post(payload):
        request = urllib.request.Request("https://api.deepseek.com/chat/completions",
            data=dumps(payload).encode(), method="POST", headers={
                "Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    return post


def prompt_messages(transcript, style_notes="", emotions="", now="", instruction="", images=None):
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT + "\n" + EMOTION_RULES + "\n" + CHAT_RULES},
        {"role": "system", "content": "风格笔记（人设优先）\n" + style_notes},
        {"role": "user", "content": "本群最近对话\n" + transcript},
    ]
    suffix = f"本次任务：{instruction}\n当前时间：{now}\n情绪数值：{emotions}"
    content = [{"type": "text", "text": suffix}, *(images or [])] if images else suffix
    messages.append({"role": "user", "content": content})
    return messages


class Agent:
    def __init__(self, store, registry, post, model=None, effort=None, max_rounds=3,
                 max_tokens=220, capabilities=None, use_langgraph=False):
        self.store, self.registry, self.post = store, registry, post
        self.model = model or os.environ.get("QQBOT_MODEL", "deepseek-flash")
        self.effort = effort or os.environ.get("QQBOT_REASONING_EFFORT", "medium")
        self.max_rounds, self.max_tokens = max_rounds, max_tokens
        self.capabilities = capabilities
        self.use_langgraph = use_langgraph

    def require(self, feature):
        if self.capabilities is not None and not self.capabilities.get(feature, False):
            labels = {"tools": "工具调用", "images": "图片输入", "thinking": "思考参数"}
            detail = self.capabilities.get("errors", {}).get(feature, "能力探测未通过")
            raise RuntimeError(f"模型不支持{labels[feature]}：{detail}")

    def _request(self, task, messages, schemas):
        payload = {"model": self.model, "max_tokens": self.max_tokens, "messages": messages}
        payload["reasoning_effort"] = self.effort
        if schemas:
            self.require("tools")
            payload["tools"] = schemas
        if self.effort != "none":
            self.require("thinking")
            payload.update(thinking={"type": "enabled"}, reasoning_effort=self.effort)
        data = self.post(payload)
        message = data["choices"][0]["message"]
        self.store.audit(task, "model", {"model": self.model},
                         {"reasoning_length": len(message.get("reasoning_content") or ""), "usage": data.get("usage", {})})
        # Reasoning is never forwarded as chat content or assistant content.
        return {key: value for key, value in message.items() if key in {"role", "content", "tool_calls"}}

    def run(self, task, messages):
        saved_task = self.store.task(task["id"])
        if saved_task and saved_task["status"] in {"completed", "sent"}:
            return saved_task["result"]
        if any(isinstance(m.get("content"), list) and any(p.get("type") == "file" for p in m["content"]) for m in messages):
            self.require("images")
        self.store.update_task(task["id"], "running")
        if self.use_langgraph:
            try:
                return self._graph(task, messages)
            except ImportError:
                pass
        return self._loop(task, messages)

    def _loop(self, task, messages):
        checkpoint = self.store.get_state("agent:" + task["id"], {"messages": messages, "round": 0})
        current = checkpoint["messages"]
        schemas = self.registry.tools_for(task)
        for index in range(checkpoint["round"], self.max_rounds + 1):
            pending = checkpoint.get("pending")
            message = pending if pending else self._request(task, current, schemas if index < self.max_rounds else [])
            calls = message.get("tool_calls") or []
            if not calls:
                answer = str(message.get("content") or "")
                if not answer:
                    raise RuntimeError("DeepSeek 没有返回正文")
                self.store.update_task(task["id"], "completed", answer)
                return answer
            if index == self.max_rounds:
                raise RuntimeError("模型在强制收尾时仍返回工具调用")
            self.store.set_state("agent:" + task["id"], {"messages": current, "round": index, "pending": message})
            current.append({**message, "role": "assistant"})
            for call in calls:
                function = call["function"]
                try:
                    args = json.loads(function.get("arguments", "{}"))
                except ValueError:
                    args = {}
                run_id = f"{task['id']}:{index}:{call['id']}"
                previous = self.store.rows("SELECT * FROM tool_runs WHERE id=?", (run_id,))
                if previous:
                    result = json.loads(previous[0]["result"]) if previous[0]["status"] == "done" else {"error": "上次调用中断，结果未知，不能自动重复执行"}
                else:
                    # An intent record prevents replaying irreversible side effects after a crash.
                    self.store.write("INSERT INTO tool_runs VALUES(?,?,?)", (run_id, "started", "{}"))
                    result = self.registry.execute(task, function["name"], args)
                    self.store.write("UPDATE tool_runs SET status='done',result=? WHERE id=?", (dumps(result), run_id))
                current.append({"role": "tool", "tool_call_id": call["id"], "content": dumps(result)})
                if function["name"] == "view_image" and result.get("images"):
                    self.require("images")
                    current.append({"role": "user", "content": [
                        {"type": "text", "text": "工具读取的图片"}, *result["images"]]})
            checkpoint = {"messages": current, "round": index + 1}
            self.store.set_state("agent:" + task["id"], checkpoint)
        raise RuntimeError("工具循环未能收尾")

    def _graph(self, task, messages):
        from langgraph.graph import StateGraph, START, END
        from langgraph.checkpoint.sqlite import SqliteSaver
        from typing import TypedDict

        class State(TypedDict):
            answer: str

        graph = StateGraph(State)
        graph.add_node("tool_loop", lambda state: {"answer": self._loop(task, messages)})
        graph.add_edge(START, "tool_loop")
        graph.add_edge("tool_loop", END)
        checkpoint_path = self.store.path + ".checkpoints"
        with SqliteSaver.from_conn_string(checkpoint_path) as saver:
            return graph.compile(checkpointer=saver).invoke({"answer": ""},
                {"configurable": {"thread_id": task["id"]}})["answer"]
