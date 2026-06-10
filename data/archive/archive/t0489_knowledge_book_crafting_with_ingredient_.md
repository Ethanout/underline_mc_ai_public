---
id: t0489
title: "知识书合成NBT原料"
title_en: "knowledge_book_crafting_with_ingredient_nbt"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/customcrafting"
source_type: "mcc_wiki"
source_issue: "questions/customcrafting"
version_min: "1.20"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["custom_crafting", "knowledge_book", "advancement_trigger", "recipe_crafted", "nbt_ingredient"]
verified_in_game: false
---

## 核心洞见

利用1.20新增的recipe_crafted触发器及其ingredients条件，可以在原版合成表中检测带NBT的原料并给予自定义结果。

## 代码示例

```mcfunction
# recipe example:some_custom_result (1.15-1.20.4)
{
  "type": "minecraft:crafting_shaped",
  "pattern": [
    "E E",
    "RDR",
    "RRR"
  ],
  "key": {
    "E": {
      "item": "minecraft:emerald"
    },
    "D": {
      "item": "minecraft:diamond"
    },
    "R": {
      "item": "minecraft:redstone"
    }
  },
  "result": {
    "item": "minecraft:knowledge_book"
  }
}

# loot_table example:some_custom_result (1.15-1.20.4)
{
  "pools": [
    {
      "rolls": 1,
      "entries": [
        {
          "type": "minecraft:item",
          "name": "minecraft:ender_eye",
          "functions": [
            {
              "function": "minecraft:set_name",
              "entity": "this",
              "name": {
                "text": "Some Custom Result",
                "italic": false
              }
            },
            {
              "function": "minecraft:set_nbt",
              "tag": "{custom_result:true}"
            }
          ]
        }
      ]
    }
  ]
}

# advancement example:recipe/root
{
  "criteria": {
    "root_recipe": {
      "trigger": "minecraft:impossible"
    }
  }
}

# advancement example:recipe/some_custom_result (1.20+，支持原料NBT检测)
{
  "parent": "example:recipe/root",
  "criteria": {
    "requirement": {
      "trigger": "minecraft:recipe_crafted",
      "conditions": {
        "recipe_id": "example:some_custom_result",
        "ingredients": [
          {
            "items": [
              "minecraft:emerald"
            ],
            "nbt": "{some:true}"
          },
          {
            "items": [
              "minecraft:emerald"
            ],
            "nbt": "{some:true}"
          },
          {
            "items": [
              "minecraft:diamond"
            ],
            "nbt": "{custom:true}"
          },
          {
            "items": [
              "minecraft:redstone"
            ],
            "nbt": "{data:true}"
          },
          {
            "items": [
              "minecraft:redstone"
            ],
            "nbt": "{data:true}"
          },
          {
            "items": [
              "minecraft:redstone"
            ],
            "nbt": "{data:true}"
          },
          {
            "items": [
              "minecraft:redstone"
            ],
            "nbt": "{data:true}"
          },
          {
            "items": [
              "minecraft:redstone"
            ],
            "nbt": "{data:true}"
          }
        ]
      }
    }
  },
  "rewards": {
    "function": "example:recipe_reset",
    "loot": [
      "example:some_custom_result"
    ]
  }
}

# function example:recipe_reset (1.20+)
advancement revoke @s from example:recipe/root
clear @s minecraft:knowledge_book

# 1.20.5+ 仅需配方文件即可（结果支持自定义数据，原料不支持）
# recipe example:some_custom_result
{
  "type": "minecraft:crafting_shaped",
  "pattern": [
    "E E",
    "RDR",
    "RRR"
  ],
  "key": {
    "E": {
      "item": "minecraft:emerald"
    },
    "D": {
      "item": "minecraft:diamond"
    },
    "R": {
      "item": "minecraft:redstone"
    }
  },
  "result": {
    "id": "minecraft:ender_eye",
    "components": {
      "minecraft:item_name": "'Some Custom Result'",
      "minecraft:custom_data": {"custom_result": true }
    }
  }
}
```

## 文件结构

- data/example/recipes/some_custom_result.json
- data/example/loot_tables/some_custom_result.json
- data/example/advancements/recipe/root.json
- data/example/advancements/recipe/some_custom_result.json
- data/example/functions/recipe_reset.mcfunction

## 用法

构建数据包后，玩家在原版工作台中按照配方摆放物品（需使用带NBT的自定义原料），合成后触发advancement，通过loot table给予自定义结果物品，同时执行函数清除知识书和撤销进度。

## 使用场景

['需要利用原版合成界面且支持NBT原料检测的合成系统', '希望自定义配方显示在合成书中的场景（1.20+）', '1.20.5+仅需自定义结果时，可直接在配方文件中使用components字段，无需advancement和函数']

## 机制原理

该技术利用1.20新增的`recipe_crafted`触发器，该触发器在玩家实际完成合成时触发（而非仅解锁配方）。其`ingredients`条件可以检测合成原料的NBT数据，每个条目对应一个原料槽位。当玩家使用带正确NBT的原料合成时，触发器激活，执行奖励函数和loot table。奖励函数撤销所有自定义配方进度并清除知识书，防止重复触发。1.20.5+版本中，如果只需要自定义结果（不需要自定义原料），可以直接在配方文件的`result.components`中指定数据组件，无需额外的advancement和函数。

## 注意事项

- 1.20之前的版本（1.15-1.19）只能通过recipe_unlocked触发器实现，但无法检测原料NBT，只能自定义结果
- 1.20+的recipe_crafted触发器可以检测原料NBT，但玩家仍可使用普通原料合成，此时只会得到知识书；需要额外机制防止这种情况
- ingredients条件中每个条目对应一个原料槽位，如果配方中使用多个相同物品，需要重复列出
- 1.20.5+版本中，如果使用自定义标签如`custom:1`，配方结果中的标签会被转换为`custom:1b`（JSON转NBT格式）
- 此方法无法在合成书中显示自定义配方图标，合成结果在书中显示为知识书
