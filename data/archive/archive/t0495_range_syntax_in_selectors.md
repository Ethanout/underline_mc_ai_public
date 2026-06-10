---
id: t0495
title: "选择器范围语法"
title_en: "range_syntax_in_selectors"
layer: concept
source_url: "https://minecraftcommands.github.io/wiki/questions/range"
source_type: "mcc_wiki"
source_issue: "questions/range"
version_min: "1.13"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["selector", "syntax", "range"]
verified_in_game: false
---

## 核心洞见

Minecraft 选择器中的范围语法（min..max）是一种简洁的数值区间匹配方式，支持开区间和闭区间，但不适用于 NBT 检查。

## 代码示例

（原文无完整代码示例）

## 文件结构

（待补充）

## 用法

无需调用，直接在目标选择器参数（如 scores、distance）中使用即可，例如：@p[distance=1..5]

## 使用场景

['在命令中筛选特定距离范围内的实体，如检测半径 10 格内的玩家', '在计分板条件中匹配分数区间，如检测分数在 5 到 10 之间的玩家', '不适合用于 NBT 检查，因为 NBT 不支持范围语法']

## 机制原理

Minecraft 命令解析器在解析目标选择器参数时，识别 `..` 作为范围分隔符。`min..max` 表示包含 min 和 max 的闭区间；省略 min 表示无下限（如 `..5` 表示 ≤5），省略 max 表示无上限（如 `5..` 表示 ≥5）；只写一个数字（如 `5`）表示精确匹配该值。该语法适用于数值型参数如 `distance`、`scores`、`level`、`gamemode`（数值 ID）等，但 NBT 检查（如 `nbt={}`）不支持此语法，因为 NBT 是结构化数据而非数值区间。

## 注意事项

- 范围语法仅适用于数值型选择器参数，不适用于 NBT 检查
- 部分参数（如 distance）支持小数范围，如 0.5..0.9
- 范围是包含边界的（闭区间）
