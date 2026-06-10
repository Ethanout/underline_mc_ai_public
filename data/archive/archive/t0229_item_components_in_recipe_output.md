---
id: t0229
title: "配方输出组件化"
title_en: "item_components_in_recipe_output"
layer: technique
source_url: "https://datapack.wiki/guide/adding-new-features/custom-items/crafting"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.20.5"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["recipe", "item_components", "custom_item", "1.20.5+"]
verified_in_game: false
---

## 核心洞见

从1.20.5开始，配方输出可以直接指定item components，无需额外advancement或函数即可创建带自定义组件的物品。

## 代码示例

```mcfunction
{
  "type": "minecraft:crafting_shaped",
  "pattern": [
    "ttt",
    " s ",
    " s "
  ],
  "key": {
    "t": {
      "item": "minecraft:turtle_scute"
    },
    "s": {
      "item": "minecraft:stick"
    }
  },
  "result": {
    "id": "minecraft:iron_pickaxe",
    "count": 1,
    "components": {
      "minecraft:tool": {
        "rules": [
          {
            "blocks": "minecraft:turtle_egg",
            "speed": 6,
            "correct_for_drops": true
          }
        ],
        "default_mining_speed": 3,
        "damage_per_block": 1
      },
      "minecraft:item_name": "{\"text\":\"sCUTE-axe\"}"
    }
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Minecraft 1.20.5（数据包格式34）引入了item components系统，配方（recipe）的result字段现在支持components子字段，可以直接在配方JSON中定义输出物品的组件，如自定义名称、工具属性、耐久等。这使得创建自定义物品的合成配方变得非常简单：只需在配方文件的result对象中添加components字段，列出所需的组件即可。系统会自动将这些组件应用到合成输出的物品上，无需任何额外的命令或advancement。这个机制的核心是配方系统原生支持了组件数据，消除了旧版本中NBT无法在配方中使用的限制。

## 注意事项

- 配方输入（key中的物品）目前不支持components，无法要求输入物品具有特定组件
- components字段中的JSON需要正确转义，特别是字符串中的引号
- 某些组件可能不适用于所有物品类型，需要确保组件与物品ID兼容
- 常见误解：开发者可能认为自定义物品的合成配方仍然需要像旧版本一样使用占位符和advancement，或者认为components只能在give命令或loot表中使用。
