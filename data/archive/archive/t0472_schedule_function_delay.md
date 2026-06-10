---
id: t0472
title: "schedule延时函数"
title_en: "schedule_function_delay"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/blockdelay"
source_type: "mcc_wiki"
source_issue: "questions/blockdelay"
version_min: "1.14"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["schedule", "function", "delay", "timer", "datapack"]
verified_in_game: false
---

## 核心洞见

使用 `/schedule function` 命令可以在指定 tick 后执行一个函数，但函数会丢失调用者的命令上下文（实体、位置），需要额外技巧来保留上下文。

## 代码示例

```mcfunction
# 基础用法：每10秒循环执行
# function example:load
function example:loops/10s

# function example:loops/10s
schedule function example:loops/10s 10s
say This will run every 10 second.

# 保留实体上下文的延时执行
# 在需要延时的地方执行（如聊天栏或函数中）
execute store result score @s timer run time query gametime
scoreboard players add @s timer 150
schedule function example:delay_function 150t append

# function example:delay_function
execute store result score #this timer run time query gametime
execute as @e if score @s timer = #this timer run say Example Command.
```

## 文件结构

- data/example/functions/load.mcfunction
- data/example/functions/loops/10s.mcfunction
- data/example/functions/delay_function.mcfunction

## 用法

需要数据包支持。在函数中调用 `schedule function <函数路径> <时间>` 来安排延时执行。使用 `append` 参数可避免覆盖之前的调度。要保留实体上下文，需将当前游戏时间存入实体分数，延时后在目标函数中匹配分数。

## 使用场景

['需要全局延时执行一段逻辑（如定时广播、周期性事件）', '需要为多个实体分别安排不同延时的回调（配合游戏时间分数匹配）', '适合在数据包中替代命令方块实现更复杂的定时逻辑']

## 机制原理

`/schedule function` 命令会在指定 tick 后执行一个函数。默认情况下，新调度会覆盖同一函数的旧调度（除非使用 `append` 参数，1.15+）。被调度的函数以服务器（Server）为执行者，位置为世界出生点下方 Y=-64，因此会丢失调用时的实体上下文和位置。为了保留上下文，可以在调度前将当前游戏时间（`time query gametime`）存入实体的计分板，并加上延时值。在目标函数中再次读取游戏时间，找到分数匹配的实体来执行命令。这样每个实体可以有独立的延时，且不会互相干扰。

## 注意事项

- 被调度的函数总是以服务器为执行者，位置在 Y=-64，无法直接使用 `@s` 或 `@p` 获取调用时的实体
- 不要在 tick 函数中无条件调用 `schedule`，否则每 tick 都会覆盖之前的调度，导致函数永远不会执行
- 1.15+ 可使用 `append` 参数避免覆盖之前的调度
- 使用游戏时间匹配法时，如果同一 tick 有多个实体分数相同，会全部执行
- 此方法需要数据包支持，纯命令方块无法使用
