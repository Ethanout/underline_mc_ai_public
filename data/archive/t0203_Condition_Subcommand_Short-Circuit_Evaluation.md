---
id: t0203
title: 条件子命令的短路求值
title_en: Condition Subcommand Short-Circuit Evaluation
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["execute", "condition", "short-circuit", "performance"]
verified_in_game: false
---

## 核心洞见

execute 的条件子命令（if/unless）可以链式组合，并且具有短路求值特性：一旦某个条件失败，后续条件不会执行，这可以用于高效的多条件检查。

## 代码示例

```mcfunction
execute if entity @e[type=sheep] if block ~ ~-1 ~ minecraft:grass_block unless score @s count matches 0 run say Found sheep on grass with count > 0
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

在 `execute if ... if ... unless ... run ...` 中，条件从左到右依次评估，如果某个条件不满足，则立即停止并跳过 run 部分。这避免了不必要的实体或数据检查，提高了效率。

## 注意事项

- 常见误解：开发者常认为条件检查必须用多个 if 语句或嵌套 execute，实际上可以在一个 execute 命令中链式使用多个 if/unless，且性能更优。
