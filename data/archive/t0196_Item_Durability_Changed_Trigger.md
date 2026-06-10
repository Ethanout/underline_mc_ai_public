---
id: t0196
title: 物品耐久度变化触发器
title_en: Item Durability Changed Trigger
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-advancement/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["advancement", "trigger", "durability", "item"]
verified_in_game: false
---

## 核心洞见

`item_durability_changed` 可以检测任何物品的耐久度变化，包括工具、武器、盔甲等，而不仅仅是特定物品。

## 代码示例

```mcfunction
advancement grant @s only minecraft:adventure/durability_changed
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

当玩家物品栏中任何物品的耐久度发生变化时，`item_durability_changed` 触发器会被激活，可以检测变化前后的耐久度值。

## 注意事项

- 常见误解：开发者可能认为只有工具或武器才有耐久度变化，但实际上任何有耐久度的物品（如盔甲、钓鱼竿）都可以被检测。
