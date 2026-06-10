---
id: t0192
title: 物品栏变化触发器
title_en: Inventory Changed Trigger
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-advancement/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["advancement", "trigger", "inventory"]
verified_in_game: false
---

## 核心洞见

`inventory_changed` 可以检测物品栏中任何物品的变化，包括数量、耐久度、组件等，而不仅仅是物品的添加或移除。

## 代码示例

```mcfunction
advancement grant @s only minecraft:story/smelt_iron
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

当玩家的物品栏发生任何变化时，`inventory_changed` 触发器会被激活。这包括物品数量的变化、耐久度的变化、物品组件的修改等。

## 注意事项

- 常见误解：开发者可能认为 `inventory_changed` 只能检测物品的添加或移除，但实际上它可以检测物品的任何属性变化。
