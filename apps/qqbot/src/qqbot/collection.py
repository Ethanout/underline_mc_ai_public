"""Share manual and scheduled essence ingestion through one source pipeline."""

from __future__ import annotations

import json
import os

from .reply import thinking_fields, token_budget
from .tricks import TrickStore


CLASSIFY_PROMPT = """判断一条 QQ 群消息（可能来自群精华或合并转发）是不是值得收录的 Minecraft 原版创作技术资料。

算技术资料（technical=true）：
- 数据包、命令、函数、execute、计分板、NBT/物品组件、战利品表、进度、谓词、资源包、着色器的技巧或写法；
- 教程、步骤、原理解释、性能或版本差异说明；
- 工具、生成器、插件、资料或文档链接，并说了用来干什么；
- 失败经验：踩过的坑、某写法在某版本不行、bug 的原因和绕法。

不算（technical=false）：闲聊、玩梗、表情包、只问不答的提问、"这个好强""学到了"之类的反应、没有说明的裸链接、和 MC 技术无关的编程闲聊、群公告和活动通知。拿不准就 false。

technical=true 时再填这些字段，消息里没说的一律写"未知"，不要自己补：
- title：一句话标题
- purpose：用来做什么
- version：适用的 MC 版本，比如 1.20.5+；没提就写未知
- code：消息里原样的命令或代码，没有就写未知
- limits：限制、前提和注意事项
- conclusion：核心结论，一两句

只输出一个 JSON 对象，例如：
{"technical": true, "title": "用 execute store 读取实体坐标", "purpose": "把实体 Y 坐标存进计分板", "version": "未知", "code": "execute store result score @s y run data get entity @s Pos[1]", "limits": "只取整数部分", "conclusion": "data get 的结果可以直接 store 进计分板"}"""


def model_classifier(post):
    def classify(message):
        # First draft; when something is wrongly collected or missed, add that
        # case to CLASSIFY_PROMPT as an example.
        payload = {
            "model": os.environ.get("QQBOT_JUDGE_MODEL", "deepseek-flash"),
            "max_tokens": 1000,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": CLASSIFY_PROMPT,
                },
                {"role": "user", "content": json.dumps(message, ensure_ascii=False)},
            ],
        }
        effort = os.environ.get("QQBOT_JUDGE_REASONING_EFFORT", "low")
        payload.update(thinking_fields(effort), max_tokens=token_budget(1000, effort))
        data = post(payload)
        item = json.loads(data["choices"][0]["message"]["content"])
        if not isinstance(item, dict) or not isinstance(item.get("technical"), bool):
            raise ValueError("技术分类器返回格式无效")
        return item if item["technical"] else None

    return classify


def install_collection_tools(registry, classifier, root=None):
    tricks = TrickStore(
        registry.store,
        root or os.environ.get("QQBOT_TRICKS_DIR", "runtime/private/qq_tricks"),
        classifier,
    )

    def collect(task, args):
        source = args.get("source", "history")
        handlers = {
            "history": registry.read_history,
            "forward": registry.read_forward,
            "essence": registry.read_essence,
        }
        if source not in handlers:
            raise ValueError("收录来源必须是 history、forward 或 essence")
        result = handlers[source](task, args)
        return {
            "entries": tricks.sync(task["group_id"], result["messages"]),
            "missing": result["missing"],
        }

    registry.register(
        "collect_tricks",
        collect,
        admin_only=True,
        libraries=("chat", "related"),
        properties={
            "source": "string",
            "count": "integer",
            "quote_id": "string",
            "start_id": "string",
            "end_id": "string",
            "forward_id": "string",
        },
    )
    return tricks
