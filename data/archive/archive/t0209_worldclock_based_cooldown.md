---
id: t0209
title: "世界时钟冷却"
title_en: "worldclock_based_cooldown"
layer: technique
source_url: "https://datapack.wiki/guide/cooldown"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["cooldown", "performance", "worldclock", "scoreboard"]
verified_in_game: false
---

## 核心洞见

利用世界时钟的单调递增时间戳替代逐 tick 递减计分板，实现零 tick 开销的冷却计时。

## 代码示例

```mcfunction
# 初始化世界时钟（在 load.mcfunction 中执行一次）
scoreboard objectives add worldclock dummy
scoreboard players set #tick worldclock 0

# 每 tick 递增时钟（在 tick.mcfunction 中执行）
scoreboard players add #tick worldclock 1

# 设置冷却（在动作触发函数中执行）
# 假设冷却时长为 100 tick（5秒）
scoreboard players operation @s cooldown = #tick worldclock
scoreboard players add @s cooldown 100

# 检查冷却（在动作触发函数中执行）
execute if score @s cooldown <= #tick worldclock run say Cooldown expired!
# 如果冷却未结束，可以执行其他逻辑
execute if score @s cooldown > #tick worldclock run say Cooldown active
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

世界时钟是一个每 tick 递增 1 的计分板目标（如 `worldclock`），每次执行动作时，将当前时钟值加上冷却时长（tick 数）存入玩家的冷却计分板。检查冷却时，只需比较当前时钟值与存储值：若当前值 >= 存储值，则冷却已结束。该技术利用了世界时钟的单调递增特性，将 O(n) 的每 tick 递减操作（n 为冷却中的玩家数）降为 O(1) 的存储与比较操作。关键推导：设冷却时长为 C tick，动作执行时的时钟值为 T，则冷却结束时刻为 T+C。检查时只需判断 `当前时钟值 >= T+C` 是否成立。与直觉的递减实现相比，该技术不需要任何 tick 循环，仅在动作执行和检查时执行命令，极大减少了系统负载。

## 注意事项

- 世界时钟必须每 tick 递增，否则时间计算会偏移
- 世界时钟值可能溢出（约 2^31 tick ≈ 2.5 年），需要定期重置或使用更大的存储类型
- 玩家首次使用前 cooldown 计分板未初始化，需要先设置一个默认值（如 0）避免比较异常
- 常见误解：开发者通常认为冷却必须通过每 tick 递减一个计分板值来实现，导致大量实体或玩家同时冷却时产生不必要的 tick 循环开销。
