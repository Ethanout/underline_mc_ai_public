# 知识提取策略：对抗 LLM 的 MCF 盲区

## 问题

LLM 缺乏 MCF（Minecraft Function）特化思维：
- 不理解 `execute store success` 遇到 `return` 的微妙行为
- 不知道 `scoreboard players operation` 整数除法做状态机的非显而易见性
- 会把 Wiki 参考文档重述为"技巧"，而不是提取真正的反直觉洞见
- 对应训练数据极少，编造风险高

## 当前数据

- 219 条：manual 10, feature_article 77, mcc_wiki 65, datapack_wiki 20, mcf_skill 2
- confidence: high 1, ? 173（几乎全是低置信度）
- 只有 10 条手写高质量稿

## 三层防御

### 第 1 层：事实提取（让 LLM 做它擅长的事）

不要问"提取技巧"，而是问具体事实：

```
阅读以下 Minecraft Wiki 页面，提取以下事实（仅从原文中提取，不要编造）：

1. **边界行为**：文档中提到了哪些"如果做了 X，实际会发生 Y（Y 可能和你期望不同）"的行为？
2. **版本差异**：行为在不同版本间有变化吗？
3. **参数限制**：X 的取值范围是什么？超出范围会发生什么？
4. **隐式规则**：文档中暗示但未明确说明的规则？
5. **已知 bug/特性**：标注为"特性"或"有意为之"的非直觉行为？

如果原文没有提到以上任何一项，输出 {"has_insights": false}
```

这比"提取技巧"靠谱得多——LLM 擅长从文本中提取明确陈述的事实，不擅长判断"什么是非直觉的"。

### 第 2 层：人机协作验证（利用你的专业知识）

你不是从零开始写——你是**审核员**：

1. LLM 提取事实（第 1 层）
2. 你快速浏览，标记：
   - ✅ 正确且有洞见 → 保留
   - ⚠️ 正确但平淡 → 降级为 concept
   - ❌ 错误或编造 → 删除
   - 💡 激发新想法 → 手写补充

3. 把手写高质量稿作为 **few-shot 示例**，让 LLM 学习"什么是好条目"

### 第 3 层：游戏内验证（最终真相）

所有提取的命令类条目，最终用游戏验证：

```
知识库条目 → 提取命令 → Mineflayer 执行 → 结果对比 → 通过/失败
知识库条目 → 构建数据包 → 游戏加载 → 行为验证 → 通过/失败
```

验证失败 = LLM 编造了内容，删除或修正。

## 实现建议

### 改进提取提示（crawl_and_extract.py）

替换当前的 EXTRACT_SYSTEM，分为两步：

**Step 1: 事实提取**（低风险）
```python
FACT_EXTRACT_SYSTEM = """\
你是 Minecraft 数据包文档分析器。从以下页面中提取事实，仅提取原文明确陈述的内容。

输出格式：
{
  "page_title": "页面标题",
  "has_insights": true/false,
  "facts": [
    {
      "type": "boundary_behavior" | "version_diff" | "parameter_limit" | "implicit_rule" | "known_behavior",
      "description": "事实描述（照搬原文）",
      "quote": "原文关键句",
      "confidence": "certain" | "likely" | "inferred"
    }
  ],
  "code_snippets": [
    {"language": "mcfunction/json", "code": "原文代码块", "context": "这段代码在说明什么"}
  ]
}

重要规则：
- 只提取原文明确陈述的事实，不要编造
- confidence=inferred 仅用于"原文暗示但未直接说明"
- 如果页面只是参考文档（如命令语法列表），output has_insights=false
"""
```

**Step 2: 技巧合成**（高风险，需要你的审核）
```python
TECHNIQUE_SYNTHESIS_SYSTEM = """\
你是 Minecraft 数据包开发者。基于以下提取的事实，合成技术发现条目。

重要：你收到的输入是从 Minecraft Wiki 提取的事实。你的任务是：
1. 判断哪些事实组合起来构成了"非直觉的技术发现"
2. 不要重述基础语法——读者已经知道命令是什么
3. 只输出你确信理解了其机制原理的条目
4. 如果你不确定某个机制为什么工作，在 notes 中标注"（需核实）"

你可以参考以下高质量条目作为范例：
{few_shot_examples}

输出格式同现有 EXTRACT_SYSTEM。
"""
```

### Few-shot 示例

用你手写的 10 条 manual 条目作为 few-shot，教会 LLM：
- 什么是真正的"非直觉洞察"
- mechanism 字段应该解释"为什么"，不是"是什么"
- 代码必须是可运行的，不是伪代码
- notes 应该包含真正的坑，不是泛泛而谈

### 游戏验证流程

```bash
# 1. 爬取新数据
python scripts/crawlers/wiki_crawler.py --wiki zh --mode deep

# 2. 事实提取（低风险）
python scripts/crawlers/crawl_and_extract.py --phase extract --model deepseek --fact-only

# 3. 人工审核
# 在 Web UI 中标记：✅ 正确 ⚠️ 平淡 ❌ 错误 💡 新想法

# 4. 技巧合成（高风险，需要 fact 作为基础）
python scripts/crawlers/crawl_and_extract.py --phase extract --model deepseek --synth-only

# 5. 游戏验证
python scripts/validation/knowledge_validator.py
```

## 总结

| 方案 | 风险 | 收益 |
|------|------|------|
| 直接让 LLM "提取技巧" | 高（编造、重述） | 快但垃圾多 |
| 事实提取 → 人工审核 → 技巧合成 | 中（需要人工审核） | 质量可控 |
| 游戏验证兜底 | 低（真相标准） | 最终保障 |

**推荐：第 2 层 + 第 3 层组合**。LLM 做事实提取，你做审核和补充，游戏做最终验证。