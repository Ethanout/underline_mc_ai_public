---
id: t0298
title: 智能合并与冲突解决
title_en: Smart Merging and Conflict Resolution
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-datapack/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["beet", "merging", "conflict-resolution", "tags"]
verified_in_game: false
---

## 核心洞见

Beet 能自动合并多个来源的标签和语言文件，并智能解决冲突，无需手动编写合并逻辑。

## 代码示例

```mcfunction
# 两个插件分别添加标签
ctx.data.functions["demo:func"].tags.append("minecraft:load")
# 另一个插件也添加同一标签，Beet 自动合并
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Beet 内置了针对标签（tags）和语言文件（languages）的合并策略。当多个插件或源文件定义相同命名空间的标签时，Beet 自动合并其值列表。对于其他资源，Beet 提供可配置的冲突解决策略（如覆盖、保留、报错）。

## 注意事项

- 常见误解：开发者通常认为合并数据包资源需要手动编写合并脚本或使用外部工具，且容易产生冲突。
