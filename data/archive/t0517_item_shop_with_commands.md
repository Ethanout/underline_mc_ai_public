---
id: t0517
title: "物品交易商店"
title_en: "item_shop_with_commands"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/shop"
source_type: "mcc_wiki"
source_issue: "questions/shop"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["shop", "item-trading", "scoreboard", "clear-command", "tag-system"]
verified_in_game: false
---

## 核心洞见

通过记分板存储物品数量并配合标签选择器，可以实现基于物品交换的玩家商店系统

## 代码示例

```mcfunction
# Command blocks
tag @p add buyer.netherite
execute as @a[tag=buyer.netherite] store result score @s diamonds run clear @s diamond 0
give @a[tag=buyer.netherite,scores={diamonds=5..}] netherite_ingot 1
clear @a[tag=buyer.netherite,scores={diamonds=5..}] diamond 5
tellraw @a[tag=buyer.netherite,scores={diamonds=5..}] {"text":"You bought a netherite ingot for 5 diamonds","color":"green"}
tellraw @a[tag=buyer.netherite,scores={diamonds=..4}] {"text":"You don't have 5 diamonds","color":"dark_red"}
tag @a remove buyer.netherite

# function example:load
scoreboard objectives add diamonds dummy

# function example:buy/netherite
execute store result score @s diamonds run clear @s diamond 0
execute if entity @s[scores={diamonds=5..}] run function example:buy/netherite/success
execute unless entity @s[scores={diamonds=5..}] run tellraw @s {"text":"You don't have 5 diamonds","color":"dark_red"}

# function example:buy/netheirte/success
give @s netherite_ingot 1
clear @s diamond 5
tellraw @s {"text":"You bought a netherite ingot for 5 diamonds","color":"green"}

# 1.20.5+ alternative counting command (replace in function)
execute store result score @s diamonds if items entity @s container.* diamond

# Command blocks for multiple items
tag @p add buyer.example
execute as @a[tag=buyer.example] run tag @s[scores={diamonds=5..,emeralds=2..}] add buy.example
clear @a[tag=buy.example] diamond 5
clear @a[tag=buy.example] emerald 2
give @a[tag=buy.example] gold_block 1
tag @a remove buy.example
tag @a remove buyer.example
```

## 文件结构

- data/example/functions/load.mcfunction
- data/example/functions/buy/netherite.mcfunction
- data/example/functions/buy/netherite/success.mcfunction
- data/example/functions/buy/diamond.mcfunction
- data/example/functions/buy/diamond/success.mcfunction

## 用法

对于命令方块版本：放置一个按钮或压力板连接命令方块链，玩家触发后自动执行。对于函数版本：通过 `execute as <player> run function example:buy/netherite` 调用，函数必须以玩家身份执行（as）。

## 使用场景

['服务器中创建用物品交换物品的商店（如用5个钻石换1个下界合金锭）', '需要精确控制交易条件（如玩家必须有足够物品才能交易）的场景', '不适合需要复杂交易逻辑（如多物品组合、动态定价）的场景，此时应考虑更高级的架构']

## 机制原理

该技术利用 `clear` 命令的计数功能（`clear @s diamond 0` 返回玩家拥有的钻石数量）配合 `execute store result score` 将数量存入记分板。然后通过 `scores={diamonds=5..}` 选择器筛选出拥有足够物品的玩家，执行给予和清除操作。关键点在于：1）使用标签（tag）确保命令块版本中正确选择目标玩家；2）函数版本利用 `@s` 保持上下文；3）先检查数量再执行交易，避免部分扣除。对于1.20.5+，`execute if items` 提供了更直接的物品计数方式，无需消耗物品。多物品交易时，需要为每个物品创建独立的记分板，并通过嵌套标签确保玩家同时拥有所有所需物品。

## 注意事项

- 命令块版本中，必须在最后移除标签，避免玩家被意外重新选中
- 函数 `example:buy/netherite` 必须以玩家身份执行（as）
- 1.20.5+ 推荐使用 `execute if items` 替代 `clear` 计数，但该方法不兼容低于1.20.5的版本
- 清除物品必须在移除标签之前完成，否则可能导致玩家未扣除物品但获得商品
- 多物品交易时，需要为每个物品创建独立的记分板
