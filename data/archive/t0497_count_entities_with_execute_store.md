---
id: t0497
title: "实体计数存储"
title_en: "count_entities_with_execute_store"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/numplayers"
source_type: "mcc_wiki"
source_issue: "questions/numplayers"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["entity counting", "execute store", "scoreboard", "selector"]
verified_in_game: false
---

## 核心洞见

execute store result 可以将实体选择器的匹配数量直接存入记分板，无需循环累加

## 代码示例

```mcfunction
scoreboard objectives add result dummy
execute store result score #count result if entity @a[team=red]
execute if score #count result matches 2 run say there are exactly 2 players on team red.
```

## 文件结构

- data/<namespace>/functions/check_players.mcfunction

## 用法

在函数中依次执行上述三条命令，或通过命令方块/函数调用。第一条命令创建记分板（只需执行一次），后两条命令组合使用即可检测精确人数。

## 使用场景

['检测团队中是否有恰好2名玩家以触发特定游戏机制', '检测区域内实体数量是否在指定范围内（如2-9个）', '替代循环累加计数方式，简化记分板操作']

## 机制原理

execute store result score <目标> <记分板> if entity <选择器> 会将 if entity 命令的返回结果（即匹配的实体数量）存储到指定记分板分数中。if entity 命令本身返回的是匹配实体数量（成功次数），store result 捕获这个数值。然后通过 execute if score ... matches <范围> 来检测该数值是否满足条件。这与朴素实现（循环累加）不同，它直接利用命令返回值，无需中间实体或循环，更简洁高效。

## 注意事项

- 需要 1.13 及以上版本
- fake player #count 是推荐的存储目标，避免使用实体
- matches 支持范围语法，如 2.. 表示2及以上，..2 表示2及以下
