---
id: t0206
title: "战利品表随机数"
title_en: "loot_table_random_number"
layer: technique
source_url: "https://datapack.wiki/guide/nbt-and-scores/random-numbers"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["random", "loot_table", "legacy"]
verified_in_game: false
---

## 核心洞见

战利品表可以生成随机数，即使物品数量被设为0，掉落物数量仍可被存储为随机值。

## 代码示例

```mcfunction
{
  "pools": [
    {
      "rolls": {
        "min": 1,
        "max": 10
      },
      "entries": [
        {
          "type": "minecraft:item",
          "name": "minecraft:stone",
          "functions": [
            {
              "function": "minecraft:set_count",
              "count": 0
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

该技术利用战利品表的rolls字段生成随机掉落次数，并通过set_count函数将物品数量设为0，从而避免实际掉落物品。执行loot spawn命令时，系统会计算rolls的随机值（在min和max之间），并触发掉落过程。通过execute store result，可以捕获这次掉落产生的物品数量（即rolls的结果），并将其存储到指定目标（如计分板）。关键点在于：即使物品数量被设为0，rolls的随机值仍然被计算并作为命令的输出结果。这利用了Minecraft中战利品表生成机制与命令存储系统的结合，提供了一种无需/random命令的随机数生成方法。与直觉相反，设置物品数量为0并不会阻止随机数的生成，因为rolls的随机性独立于物品数量。

## 注意事项

- 战利品表文件必须放置在数据包的loot_tables目录下，且命名空间需正确
- 使用loot spawn命令时，需要确保目标位置可执行掉落（如非空气方块上方）
- 该方法在1.20.2及以上版本中效率较低，应优先使用/random命令
- 常见误解：开发者可能认为随机数只能通过复杂的实体操作或外部工具生成，而忽略了战利品表作为随机数生成器的能力。
