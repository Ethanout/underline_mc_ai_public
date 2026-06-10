---
id: t0195
title: 实体交互触发器
title_en: Entity Interaction Trigger
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-advancement/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["advancement", "trigger", "entity", "interaction"]
verified_in_game: false
---

## 核心洞见

`player_interacted_with_entity` 可以检测玩家与实体的交互，包括右键点击、攻击等，而不仅仅是交易或驯服。

## 代码示例

```mcfunction
advancement grant @s only minecraft:adventure/interact_with_entity
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

当玩家与一个实体进行交互（如右键点击、攻击）时，`player_interacted_with_entity` 触发器会被激活，可以检测交互的实体类型和玩家状态。

## 注意事项

- 常见误解：开发者可能认为只有特定的交互（如交易、驯服）才能被检测，但实际上任何与实体的交互都可以触发。
