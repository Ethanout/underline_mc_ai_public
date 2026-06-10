---
id: t0207
title: "计分板冷却"
title_en: "tick_based_scoreboard_cooldown"
layer: technique
source_url: "https://datapack.wiki/guide/cooldown/scoreboard"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.20.5"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["cooldown", "scoreboard", "tick", "return", "execute"]
verified_in_game: false
---

## 核心洞见

利用每 tick 递减计分板分数，可以实现基于游戏刻的冷却计时器，并通过 return fail/success 控制后续命令执行。

## 代码示例

```mcfunction
scoreboard objectives add my_cd dummy

scoreboard players remove @a[scores={my_cd=1..}] my_cd 1

# If the player is still on cooldown, tell the player and stop here.
execute if score @s my_cd matches 1.. run tellraw @s {color:"red",text:"This is on cooldown! Wait before you try again."}
execute if score @s my_cd matches 1.. run return fail

# If the function hasn't yet been stopped, then the player is not on a cooldown
# so we can set the cooldown and then return a success. 

scoreboard players set @s my_cd 100
return 1

execute as <player> if function <namespace>:check_cooldown run summon creeper
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术基于计分板 dummy 目标只能由命令修改的特性，以及游戏每 tick 执行一次 tick 函数的机制。核心流程：1) 在 load 函数中创建 dummy 计分板 my_cd；2) 在 tick 函数中，对所有 my_cd 分数 ≥1 的玩家执行 scoreboard players remove 1，实现每 tick 减 1；3) 在 check_cooldown 函数中，先检查执行者 my_cd 分数：若 ≥1 则发送提示并 return fail 终止，否则设置分数为 100（代表 5 秒冷却）并 return 1 表示成功。外部通过 execute if function 调用 check_cooldown，根据返回值决定是否执行后续命令。关键非直觉点：return fail 会立即终止函数并返回失败状态，而 return 1 返回成功，这允许在命令链中优雅地控制流程，无需复杂的条件分支。

## 注意事项

- 每 tick 对所有在线玩家执行 scoreboard players remove 命令，当玩家数量多或冷却数量多时性能开销大，因为命令每 tick 运行一次
- 多个冷却需要多个计分板目标和对应的 check_cooldown 函数，导致 tick 函数中命令数量线性增长
- 冷却时间以 tick 为单位（20 tick = 1 秒），设置 100 表示 5 秒，但若需要精确到秒需注意 tick 与秒的换算
- return fail 会立即停止函数，因此必须在设置冷却之前检查，否则冷却会被跳过
- 常见误解：开发者可能认为冷却需要复杂的计时系统或外部插件，或者用 advancement 和进度检测来实现，而忽略了计分板加 tick 函数的简单组合。
