---
id: t0399
title: "计分板监听挖掘结束"
title_en: "scoreboard_mining_end_detection"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202506/2/content"
source_type: "feature_article"
source_issue: "202506"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["计分板", "挖掘结束", "tick函数", "事件监听"]
verified_in_game: false
---

## 核心洞见

通过计分板统计挖掘次数，结合 tick 函数可以间接监听方块挖掘结束事件，弥补缺少直接触发器的缺陷。

## 代码示例

```mcfunction
# load 函数
scoreboard objectives add _Spawner_ minecraft.mined:minecraft.spawner

# tick 函数
execute as @a if score @s _Spawner_ matches 1 run function cit:2

# cit:2 函数
scoreboard players reset @s _Spawner_
effect give @s minecraft:haste 10 1
effect give @s minecraft:strength 10 1
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Minecraft 的计分板系统可以追踪玩家挖掘特定方块的数量（如 minecraft.mined:minecraft.spawner）。当玩家完成挖掘一个方块后，该统计值会增加 1。通过在 tick 函数中检查所有玩家的该计分板值是否大于等于 1，可以检测到挖掘事件。检测到后立即重置计分板值，并执行奖励函数。这种方法虽然无法传递方块坐标或区分工具，但能监听挖掘结束事件，弥补了 hit_block 只监听开始、进度触发器需要复杂条件的不足。其原理是利用计分板的实时更新特性，在 tick 循环中轮询。

## 注意事项

- 无法传递被挖掘方块的坐标信息
- 无法区分玩家使用的工具或魔咒
- 统计值可能因其他原因（如创造模式挖掘）增加，需要额外过滤
- 需要确保计分板在 load 函数中初始化，且 tick 函数持续运行
- 常见误解：开发者可能认为挖掘结束事件无法被监听，只能使用进度或魔咒触发器，但计分板统计（minecraft.mined）可以在挖掘完成后更新，配合 tick 函数实现事件检测。
