---
id: t0224
title: "物品组件基础"
title_en: "item_components_intro"
layer: technique
source_url: "https://datapack.wiki/wiki/concepts/item-components"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.20.5"
version_max: ""
wiki_covers_this: true
confidence: low
tags: ["item", "data-component", "command"]
verified_in_game: false
---

## 核心洞见

物品组件是 Minecraft 中通过数据驱动方式为物品添加属性的核心机制，每个物品默认拥有特定组件，可通过命令修改。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

物品组件是 Minecraft 1.20.5+ 引入的数据驱动系统，替代了旧的 NBT 标签。每个物品类型（如食物、工具）默认关联一组组件（如 `minecraft:consumable` 使物品可食用）。通过 `/give` 或 `/item` 命令，可以覆盖或移除这些组件，从而改变物品行为。例如，给非食物物品添加 `minecraft:consumable` 组件可使其可食用。组件数据结构在 Wiki 上有完整列表，支持自定义属性如名称、描述、耐久等。

## 注意事项

- 组件覆盖可能移除默认行为，需谨慎操作
- 不同版本组件格式可能变化，需参考对应 Wiki
- 常见误解：开发者可能认为物品属性是硬编码的，只能通过 NBT 修改，而不知道物品组件是独立的数据结构，可以动态添加或移除。
