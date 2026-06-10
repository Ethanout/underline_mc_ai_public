---
id: t0200
title: 奖励战利品表的 this_entity 上下文
title_en: Reward Loot Table this_entity Context
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-advancement/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["advancement", "rewards", "loot table", "this_entity"]
verified_in_game: false
---

## 核心洞见

奖励战利品表在生成时，this_entity 上下文被设置为达成进度的玩家，允许战利品表根据玩家属性（如装备、状态效果）动态生成物品。

## 代码示例

```mcfunction
{
  "rewards": {
    "loot": ["namespace:custom_loot"]
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

在 advancement 的 rewards 中指定 loot 字段，战利品表生成时会将 this_entity 设为该玩家，因此可以在战利品表条件中使用 player_has_advancement、player_killed_entity 等条件，或通过函数动态调整物品。

## 注意事项

- 常见误解：开发者可能认为奖励战利品表只是简单的随机物品列表，无法感知玩家状态。
