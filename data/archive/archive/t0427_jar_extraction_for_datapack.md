---
id: t0427
title: "拆解 JAR 学数据包"
title_en: "jar_extraction_for_datapack"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202505/4/content"
source_type: "feature_article"
source_issue: "202505"
version_min: "1.13"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["datapack", "learning", "jar_extraction"]
verified_in_game: false
---

## 核心洞见

通过解压原版 .jar 文件，可以直接查看和模仿 Minecraft 原版数据包的结构和内容，是学习数据包制作的高效方法。

## 代码示例

```mcfunction
// 解压 .jar 文件（以 1.20.1 为例）
// 路径: .minecraft/versions/1.20.1/1.20.1.jar
// 解压后查看 data/minecraft 目录

// 示例：自定义精准采集 II 的附魔文件
// Doom_CustomEnchantment/data/minecraft/enchantment/silk_touch.json
{
  "anvil_cost": 8,
  "description": {
    "translate": "enchantment.minecraft.silk_touch"
  },
  "effects": {
    "minecraft:block_experience": [
      {
        "effect": {
          "type": "minecraft:set",
          "value": 0.0
        }
      }
    ]
  },
  "exclusive_set": "#minecraft:exclusive_set/mining",
  "max_cost": {
    "base": 65,
    "per_level_above_first": -50
  },
  "max_level": 2,
  "min_cost": {
    "base": 15,
    "per_level_above_first": 0
  },
  "slots": [
    "mainhand"
  ],
  "supported_items": "#minecraft:enchantable/mining_loot",
  "weight": 1
}

// 示例：修改刷怪笼战利品表以支持精准采集 II
// Doom_CustomEnchantment/data/minecraft/loot_table/blocks/spawner.json
{
  "type": "minecraft:block",
  "random_sequence": "minecraft:blocks/spawner",
  "pools": [
    {
      "rolls": 1,
      "entries": [
        {
          "type": "item",
          "name": "spawner",
          "conditions": [
            {
              "condition": "match_tool",
              "predicate": {
                "components": {
                  "enchantments": {
                    "silk_touch": 2
                  }
                }
              }
            },
            {
              "condition": "random_chance",
              "chance": 0.25
            }
          ]
        }
      ]
    }
  ]
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Minecraft 1.6+ 版本将游戏资源模块化存储在 .minecraft/versions 目录下的 .jar 文件中。解压后，按照路径 data/minecraft 可以找到原版数据包的所有文件，包括配方、战利品表、附魔、进度等。这些文件是官方定义的、经过测试的完整数据包结构。通过模仿这些文件，开发者可以快速理解数据包的格式规范、命名空间、JSON 语法等。例如，要创建自定义附魔，可以复制原版的 silk_touch.json 文件，修改 max_level 和效果参数，再修改对应方块（如刷怪笼）的战利品表以支持该附魔。关键推导：原版数据包是“最佳实践”的参考，因为它们是游戏本身使用的，格式和逻辑都经过验证。与直觉相反，新手常认为“原创”需要完全独立编写，但实际上模仿原版结构能避免格式错误，并快速掌握数据包的设计模式。

## 注意事项

- 解压 .jar 文件时不要原地解压，应复制到其他目录，避免污染游戏文件
- 不同版本的原版数据包结构可能不同，1.20.5 后附魔使用组件格式而非 NBT
- 常见误解：新手认为数据包制作需要从零开始编写所有文件，而不利用原版已有的结构和配置作为模板。
