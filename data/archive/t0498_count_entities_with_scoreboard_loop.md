---
id: t0498
title: "循环累加计数"
title_en: "count_entities_with_scoreboard_loop"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/numplayers"
source_type: "mcc_wiki"
source_issue: "questions/numplayers"
version_min: "1.0"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["entity counting", "scoreboard", "loop", "cross-platform"]
verified_in_game: false
---

## 核心洞见

通过实体标记和循环累加，可以在所有版本中实现实体计数

## 代码示例

```mcfunction
scoreboard objectives add result dummy
scoreboard players set @e[tag=counter] result 0
execute as @a[team=red] run scoreboard players add @e[tag=counter] result 1
execute as @e[tag=counter,scores={result=2}] run say there are exactly 2 people on the red team
```

## 文件结构

- data/<namespace>/functions/count_players.mcfunction

## 用法

在函数中依次执行上述命令。需要预先创建一个带有 counter 标签的实体（如 armor stand），并创建 result 记分板。执行后，counter 实体的 result 分数即为匹配玩家数量。

## 使用场景

['在 Java 和 Bedrock 双版本兼容的场景下需要计数', '无法使用 execute store 的旧版本（1.12 及以下）', '需要同时处理多个不同条件的计数']

## 机制原理

通过一个标记实体（tag=counter）作为计数器。先将计数器分数归零，然后对每个匹配的玩家执行一次 add 操作，使计数器分数增加。最终计数器的分数等于匹配玩家数量。这种方法虽然繁琐但兼容性好，不依赖特定版本特性。与 execute store 方法相比，它需要额外的实体和多次命令执行，但可以在所有版本中工作。

## 注意事项

- 需要预先创建带有 counter 标签的实体
- 每次计数前需要重置计数器分数
- 适用于 Java 和 Bedrock 双版本
- 效率低于 execute store 方法，建议 Java 版本使用 Method 1
