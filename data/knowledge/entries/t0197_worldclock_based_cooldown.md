---
id: t0197
title: "世界时钟冷却"
title_en: "worldclock_based_cooldown"
layer: technique
source_url: "https://datapack.wiki/guide/cooldown/worldclock"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.20.5"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["world_clock", "cooldown", "performance", "scoreboard", "time"]
verified_in_game: false
---

## 核心洞见

利用世界时钟存储时间戳，通过分数运算实现无 tick 依赖的高性能冷却系统

## 代码示例

```mcfunction
scoreboard objectives add last_used dummy

# check_cooldown.mcfunction
execute store result score #current_time last_used run time of <namespace>:cooldown query time
scoreboard players operation #current_time last_used -= @s last_used
execute if score #current_time last_used matches ..100 run tellraw @s {color:"red",text:"This is on cooldown! Wait before you try again."}
execute if score #current_time last_used matches ..100 run return fail
execute store result score @s last_used run time of <namespace>:cooldown query time
return 1
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用 Minecraft 1.20.5+ 引入的世界时钟系统（world clock），它本质上是一个高精度的时间计数器，可以通过 `time of <namespace>:<clock> query time` 查询当前时间戳。核心机制是：在 `check_cooldown` 函数中，先获取当前世界时钟时间存入临时分数 `#current_time`，然后减去玩家 `last_used` 分数中存储的上次使用时间戳，得到时间差。如果时间差小于冷却阈值（如 100 ticks），则返回失败；否则更新玩家分数为当前时间并返回成功。由于世界时钟是全局自动递增的，不需要任何 tick 函数维护，因此性能极高。关键推导：时间差 = 当前时间 - 上次使用时间，当差值小于阈值时表示冷却未结束。与朴素实现（每 tick 递减分数）相比，此技术将计算从持续更新变为按需查询，大幅减少函数调用次数。

## 注意事项

- 不要修改 cooldown 世界时钟本身，否则会破坏冷却计算
- 每个不同的冷却需要独立的 last_used 分数板和 check_cooldown 函数
- 世界时钟需要重启世界才能生效，/reload 不够
- 常见误解：开发者通常使用每 tick 递减的分数计时器来实现冷却，这需要持续运行函数，性能开销大
