---
id: t0323
title: 自定义附魔完整实现
title_en: Complete Custom Enchantment Implementation
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-enchantment/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["custom enchantment", "effect component", "post_attack", "damage modifier", "life steal"]
verified_in_game: false
---

## 核心洞见

通过组合多个效果组件（post_attack和damage），可以在一个附魔中同时实现伤害加成和生命偷取效果，而无需使用函数或计分板。

## 代码示例

```mcfunction
{
  "effects": {
    "minecraft:post_attack": [
      {
        "enchanted": "attacker",
        "affected": "attacker",
        "effect": {
          "type": "minecraft:apply_mob_effect",
          "to_apply": {
            "id": "minecraft:regeneration",
            "duration": 60,
            "amplifier": { "type": "minecraft:linear", "base": 0, "per_level_above_first": 0 }
          }
        }
      }
    ],
    "minecraft:damage": [
      {
        "effect": {
          "type": "minecraft:add",
          "value": { "type": "minecraft:linear", "base": 1.0, "per_level_above_first": 0.5 }
        }
      }
    ]
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

在附魔JSON中，effects字段可以包含多个效果类型，如minecraft:post_attack用于攻击后触发效果，minecraft:damage用于修改伤害。每个效果可以独立配置条件和参数，通过线性公式实现等级缩放。

## 注意事项

- 常见误解：开发者常认为自定义附魔必须通过数据包函数或计分板来实现复杂效果，实际上可以直接在附魔定义中组合多个效果组件。
