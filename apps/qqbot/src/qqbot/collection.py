"""Share manual and scheduled essence ingestion through one source pipeline."""
from __future__ import annotations

import json
import os

from .tricks import TrickStore


def model_classifier(post):
    def classify(message):
        # TODO(人工调): improve classification wording with real group examples.
        payload = {
            "model": os.environ.get("QQBOT_JUDGE_MODEL", "deepseek-flash"),
            "max_tokens": 1000,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "判断消息是否为 MC 数据包技术资料。输出 JSON：technical 布尔值，以及 title、purpose、version、code、limits、conclusion。未知字段写未知。"},
                {"role": "user", "content": json.dumps(message, ensure_ascii=False)},
            ],
        }
        effort = os.environ.get("QQBOT_JUDGE_REASONING_EFFORT", "medium")
        payload["reasoning_effort"] = effort
        if effort != "none":
            payload["thinking"] = {"type": "enabled"}
        data = post(payload)
        item = json.loads(data["choices"][0]["message"]["content"])
        if not isinstance(item, dict) or not isinstance(item.get("technical"), bool):
            raise ValueError("技术分类器返回格式无效")
        return item if item["technical"] else None
    return classify


def install_collection_tools(registry, classifier, root=None):
    tricks = TrickStore(registry.store, root or os.environ.get("QQBOT_TRICKS_DIR", "runtime/private/qq_tricks"), classifier)

    def collect(task, args):
        source = args.get("source", "history")
        handlers = {"history": registry.read_history, "forward": registry.read_forward, "essence": registry.read_essence}
        if source not in handlers:
            raise ValueError("收录来源必须是 history、forward 或 essence")
        result = handlers[source](task, args)
        return {"entries": tricks.sync(task["group_id"], result["messages"]), "missing": result["missing"]}

    registry.register("collect_tricks", collect, admin_only=True, libraries=("chat", "related"),
        properties={"source": "string", "count": "integer", "quote_id": "string", "start_id": "string", "end_id": "string", "forward_id": "string"})
    return tricks
