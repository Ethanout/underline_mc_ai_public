---
id: t0518
title: "积分商店系统"
title_en: "score_shop_with_functions"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/shop"
source_type: "mcc_wiki"
source_issue: "questions/shop"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["shop", "scoreboard", "currency", "function", "conditional-execution"]
verified_in_game: false
---

## 核心洞见

使用 dummy 记分板作为货币，通过函数上下文保持和条件执行实现高效的积分商店

## 代码示例

```mcfunction
# function example:buy/diamond
execute if entity @s[scores={coins=10..}] run function example:buy/diamond/success
tellraw @s[scores={coins=..9}] {"text":"You don't have 10 coins","color":"red"}

# function example:buy/diamond/success
give @s diamond
scoreboard players remove @s coins 10
tellraw @s {"text":"You bought a diamond","color":"green"}
```

## 文件结构

- data/example/functions/buy/diamond.mcfunction
- data/example/functions/buy/diamond/success.mcfunction

## 用法

通过 `execute as <player> run function example:buy/diamond` 调用，函数必须以玩家身份执行（as）。玩家需要先有 `coins` 记分板目标。

## 使用场景

['服务器经济系统中用虚拟货币购买物品', '需要快速、低开销的交易系统（函数比命令块更高效）', '不适合需要复杂交易条件（如等级限制、冷却时间）的场景']

## 机制原理

该技术使用 `dummy` 类型的记分板作为货币系统。核心机制是：1）通过 `execute if entity @s[scores={coins=10..}]` 条件判断玩家是否有足够积分；2）满足条件时调用子函数执行交易（给予物品、扣除积分、发送消息）；3）不满足条件时直接发送提示消息。函数版本的优势在于保持 `@s` 上下文，无需使用标签，比命令块版本更简洁高效。`scoreboard players remove` 直接扣除积分，无需额外检查，因为条件判断已确保玩家有足够积分。

## 注意事项

- 函数 `example:buy/diamond` 必须以玩家身份执行（as）
- 记分板 `coins` 必须是 `dummy` 类型，不能是 `dummy` 以外的类型（如 `deathCount`）
- 命令块版本中，标签 `buyer_diamond` 和 `buy.diamond` 的命名不一致（原文有下划线差异），需注意统一
