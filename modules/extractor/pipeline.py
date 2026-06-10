"""
AI 提取流水线
使用 LLM 从原始内容中提取结构化数据包知识
"""
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
import sys
import os

from ..config import SILICONFLOW_KEY, DEEPSEEK_KEY

STRUCTURE_PROMPT = """\
你是一名资深 Minecraft Java Edition 数据包开发者，也是知识提炼专家。

任务：阅读用户提交的原始内容，提取「技术发现条目」(technique) 的结构化信息。

━━━ 各字段要求 ━━━

title：英文 snake_case 标题，简洁概括此技术
title_zh：中文标题，8字以内
layer：technique | concept | pattern
  - technique：具体可实现的技术点/解法
  - concept：基础概念/背景知识
  - pattern：跨技术的设计模式/架构思路
insight：一句话：这个条目揭示了什么非直觉的事实
code：完整可运行代码，保留原始注释；无则留空字符串
file_structure：实现此技术需要创建的文件路径列表，每条格式 data/<namespace>/functions/xxx.mcfunction
usage：写完代码后怎么调用/触发/接入数据包
use_cases：适用场景，1-3条
mechanism：完整的机制原理，包含推导过程，不少于100字
notes：注意事项列表，每条一条
version_min：最低 Minecraft 版本（如 1.13）
version_max：最高有效版本（留空=至今有效）
wiki_covers_this：Wiki 是否已完整覆盖此内容（true/false）
confidence：medium（有完整实现）| low（仅原理/片段）
tags：标签列表

━━━ 输出格式（直接输出 JSON，不加代码块）━━━
{
  "title": "snake_case_english_title",
  "title_zh": "中文标题",
  "layer": "technique",
  "insight": "一句话洞见",
  "code": "完整代码或空字符串",
  "file_structure": ["data/<namespace>/functions/xxx.mcfunction"],
  "usage": "调用/触发方式",
  "use_cases": "适用场景",
  "mechanism": "机制原理",
  "notes": ["注意事项1"],
  "version_min": "1.xx",
  "version_max": "",
  "wiki_covers_this": false,
  "confidence": "medium",
  "tags": ["tag1", "tag2"]
}

如果内容不是技术性内容或无法提取 technique，输出：
{"error": "无法提取技术条目", "reason": "原因说明"}
"""


def structure_inbox(content: str) -> dict:
    import openai
    from ..config import DEEPSEEK_KEY as _DEEPSEEK_KEY, SILICONFLOW_KEY as _SF_KEY

    api_key = ""
    api_base = "https://api.deepseek.com/v1"
    model = "deepseek-chat"

    if _DEEPSEEK_KEY.exists():
        api_key = _DEEPSEEK_KEY.read_text().strip()
    elif _SF_KEY.exists():
        api_key = _SF_KEY.read_text().strip()
        api_base = "https://api.siliconflow.cn/v1"
    else:
        api_key = os.environ.get("LLM_API_KEY", "")
        api_base = os.environ.get("LLM_API_BASE", "https://api.deepseek.com/v1")

    if not api_key:
        return {"ok": False, "error": "No API key available"}

    client = openai.OpenAI(api_key=api_key, base_url=api_base)

    MAX_CHARS = 40000
    article = content if len(content) <= MAX_CHARS else content[:MAX_CHARS]

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": STRUCTURE_PROMPT},
            {"role": "user", "content": f"请分析以下内容，提取 technique 条目：\n\n{article}"},
        ],
        temperature=0.1,
        max_tokens=4000,
    )

    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                result = json.loads(m.group())
            except Exception:
                return {"ok": False, "error": "Failed to parse LLM response", "raw": raw}
        else:
            return {"ok": False, "error": "Failed to parse LLM response", "raw": raw}

    if "error" in result:
        return {"ok": False, "error": result.get("reason", result["error"])}

    return {"ok": True, "data": result}

EXTRACTION_PROMPT = """You are a Minecraft datapack expert. Analyze the following content and extract datapack knowledge.

Rules:
1. Identify if this is about advancements, loot tables, predicates, functions, or commands
2. Extract all JSON datapack files exactly as shown
3. Extract all Minecraft commands
4. Determine if this technique requires a datapack to test
5. Determine the difficulty level
6. Output ONLY valid JSON, no other text

Raw Content:
```
{raw_content}
```

Output JSON format:
{{
  "title": "Technique title in English (keep original if already in Chinese)",
  "summary": "One sentence summary",
  "category": "advancement|predicate|loot_table|function|command|other",
  "minecraft_version": "version or 'unknown'",
  "difficulty": "beginner|intermediate|advanced",
  "requires_datapack": true/false,
  "datapack_files": [
    {{
      "type": "advancement|predicate|loot_table",
      "namespace": "example",
      "name": "file_name",
      "content": {{...}}
    }}
  ],
  "commands": ["cmd1", "cmd2"],
  "interactive_test": {{
    "required": true/false,
    "keys": ["key1"],
    "description": "what to test"
  }},
  "tags": ["tag1", "tag2"],
  "verification_steps": [
    {{
      "action": "command|press_key|deploy_datapack|check_advancement|screenshot",
      "params": {{}}
    }}
  ]
}}
"""


def _get_api_key() -> str:
    """从配置文件读取 API Key"""
    for path in [SILICONFLOW_KEY, DEEPSEEK_KEY]:
        if path.exists():
            return path.read_text().strip()
    return os.environ.get("LLM_API_KEY", "")


class AIExtractor:
    """AI 提取器"""

    def __init__(self, model: str = "deepseek-chat"):
        self.model = model
        self.api_key = _get_api_key()
        self.api_base = os.environ.get(
            "LLM_API_BASE",
            "https://api.deepseek.com/v1"  # DeepSeek 默认
        )

        # 尝试从文件判断 API
        if SILICONFLOW_KEY.exists():
            self.api_base = "https://api.siliconflow.cn/v1"

    def extract(self, raw_content: str) -> Optional[Dict[str, Any]]:
        """从原始内容提取结构化数据"""
        try:
            import openai
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )

            response = client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(
                        raw_content=raw_content[:4000]  # 限制长度
                    )
                }],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            text = response.choices[0].message.content
            return json.loads(text)

        except Exception as e:
            print(f"  LLM 提取失败: {e}")
            return None


class RuleExtractor:
    """规则提取器（LLM 不可用时的后备）"""

    @staticmethod
    def extract_title(content: str) -> str:
        """从内容提取标题"""
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Unknown Technique"

    @staticmethod
    def extract_commands(content: str) -> List[str]:
        """提取命令"""
        commands = []
        blocks = re.findall(
            r'```(?:mcfunction|minecraft)?\n(.*?)```',
            content, re.DOTALL
        )

        valid_prefixes = [
            'scoreboard', 'execute', 'give', 'summon', 'kill', 'tp',
            'setblock', 'fill', 'gamemode', 'time', 'weather', 'gamerule',
            'advancement', 'effect', 'function', 'item', 'loot', 'tag',
            'team', 'tellraw', 'title', 'trigger', 'return', 'data'
        ]

        for block in blocks:
            for line in block.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    cmd = line.lstrip('/')
                    if any(cmd.startswith(p) for p in valid_prefixes):
                        commands.append(cmd)

        return commands

    @staticmethod
    def extract_json_files(content: str) -> List[Dict[str, Any]]:
        """提取 JSON 数据包文件"""
        files = []
        json_blocks = re.findall(
            r'```json\n(.*?)\n```',
            content, re.DOTALL
        )

        for i, block in enumerate(json_blocks):
            try:
                data = json.loads(block)

                # 推断类型
                file_type = "other"
                if "criteria" in data:
                    file_type = "advancement"
                elif "pools" in data:
                    file_type = "loot_table"
                elif "condition" in data:
                    file_type = "predicate"

                files.append({
                    "type": file_type,
                    "namespace": "auto_extracted",
                    "name": f"extracted_{i}",
                    "content": data
                })
            except json.JSONDecodeError:
                continue

        return files

    @staticmethod
    def categorize(content: str) -> str:
        """分类"""
        if "advancement" in content.lower():
            return "advancement"
        elif "predicate" in content.lower():
            return "predicate"
        elif "loot_table" in content.lower() or "loot" in content.lower():
            return "loot_table"
        elif "function" in content.lower():
            return "function"
        return "command"

    def extract(self, raw_content: str) -> Dict[str, Any]:
        """规则提取"""
        commands = self.extract_commands(raw_content)
        json_files = self.extract_json_files(raw_content)

        return {
            "title": self.extract_title(raw_content),
            "category": self.categorize(raw_content),
            "commands": commands,
            "datapack_files": json_files,
            "requires_datapack": len(json_files) > 0,
            "difficulty": "intermediate",
            "minecraft_version": "unknown",
            "tags": [],
            "sources": []
        }


class Pipeline:
    """提取流水线"""

    def __init__(self, use_llm: bool = True):
        self.ai = AIExtractor() if use_llm else None
        self.rule = RuleExtractor()

    def process(self, raw_content: str) -> Dict[str, Any]:
        """
        处理原始内容，返回结构化条目

        先用 LLM 提取（如果可用），回退到规则提取
        """
        print("  AI 提取...")
        result = self.ai.extract(raw_content) if self.ai else None

        if result and result.get("title"):
            print(f"  ✅ AI 提取成功: {result['title'][:50]}")
            return result

        print("  ⚠️ AI 失败，回退到规则提取")
        result = self.rule.extract(raw_content)
        print(f"  ✅ 规则提取完成: {result['title'][:50]}")
        return result


# 测试
if __name__ == "__main__":
    import codecs
    if sys.platform == 'win32':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    test_content = """
# 物品耐久变化检测

使用 advancement 的 `item_durability_changed` 触发器检测玩家物品耐久变化。

```json
{
  "criteria": {
    "durability_changed": {
      "trigger": "minecraft:item_durability_changed",
      "conditions": {
        "durability": {
          "min": 1,
          "max": 100
        }
      }
    }
  },
  "rewards": {
    "function": "namespace:on_durability_change"
  }
}
```

```mcfunction
# 检测命令
execute as @a[advancements={namespace:item_durability_changed=true}] run say 耐久变化！
```
"""

    pipe = Pipeline(use_llm=False)  # 不用 LLM 测试
    result = pipe.process(test_content)
    print(json.dumps(result, indent=2, ensure_ascii=False))
