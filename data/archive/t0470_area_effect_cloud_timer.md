---
id: t0470
title: "AEC延时器"
title_en: "area_effect_cloud_timer"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/blockdelay"
source_type: "mcc_wiki"
source_issue: "questions/blockdelay"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["area_effect_cloud", "timer", "delay", "command_block"]
verified_in_game: false
---

## 核心洞见

利用 Area Effect Cloud 的 Age 和 Duration 标签，可以创建一个精确到 tick 的、可定位的延时触发器，无需额外计分板或函数。

## 代码示例

```mcfunction
# 1.20.4 and below
summon area_effect_cloud ~ ~ ~ {Tags:["delay"],Age:-100,Particle:"block air"} 

# 1.20.5 and above
summon area_effect_cloud ~ ~ ~ {Tags:["delay"],Age:-100,Particle:{type:"block",block_state:"minecraft:air"}} 

# 以下3条命令按顺序放在循环-连锁命令方块时钟上，每 tick 执行一次
tag @e[type=area_effect_cloud,tag=delay,nbt={Age:-1}] add delayActivating
execute at @e[type=area_effect_cloud,tag=delayActivating] run data merge block ~ ~ ~ {auto:true}
execute at @e[type=area_effect_cloud,tag=delayActivating] run data merge block ~ ~ ~ {auto:false}

# 使用示例：在(10,64,30)处延时70tick后激活命令方块
summon area_effect_cloud 10 64 30 {Tags:["delay"],Age:-70,Particle:{type:"block",block_state:"minecraft:air"}}

# 使用刷怪蛋生成AEC（1.13-1.20.4）
give @s bat_spawn_egg{EntityTag:{id:"minecraft:area_effect_cloud",Tags:["delay"],Duration:100,Radius:0f,WaitTime:0}}

# 使用刷怪蛋生成AEC（1.20.5+）
give @s bat_spawn_egg[entity_data={id:"minecraft:area_effect_cloud",Tags:["delay"],Duration:100,Radius:0f,WaitTime:0}]

# 在指定位置延时后执行任意命令（命令方块/tick函数中）
execute at @e[type=area_effect_cloud,tag=delay,nbt={Age:99}] run summon zombie
```

## 文件结构

（待补充）

## 用法

构建完数据包即可在游戏内测试效果。将3条检测命令放在循环-连锁命令方块时钟上，然后使用 summon 命令生成带有指定 Age 负值的 AEC 即可触发延时。

## 使用场景

['需要在特定位置精确延时执行一次命令（如延时生成怪物、激活红石机械）', '需要多个独立、不同延时的定时器，且不想使用计分板或函数', '适合在命令方块系统中实现简单的一次性延时，无需数据包']

## 机制原理

Area Effect Cloud (AEC) 实体拥有 `Age` 和 `Duration` 两个 NBT 标签。每游戏刻，AEC 的 `Age` 自动增加 1。当 `Age` 达到 `Duration` 时，AEC 会消失。通过将 `Age` 设为负值（如 -100），AEC 需要经过 100 tick 后 `Age` 才会增长到 0，再经过 `Duration`（默认 0）后消失。在 `Age` 变为 -1 的那一 tick，AEC 即将消失，此时可以检测 `nbt={Age:-1}` 来触发命令。由于 AEC 是实体，可以精确控制其位置，因此可以在指定坐标处执行命令。通过设置不同的负 `Age` 值，可以实现不同的延时长度。

## 注意事项

- AEC 默认会产生粒子，需要将 `Particle` 设为 `"block air"`（1.20.4及以下）或 `{type:"block",block_state:"minecraft:air"}`（1.20.5及以上）来消除粒子
- 使用刷怪蛋生成 AEC 时，需要额外设置 `Radius:0f` 和 `WaitTime:0`，否则 AEC 不会立即开始计时
- 按 F3+B 可显示实体碰撞箱以查看 AEC
- 此方法适合一次性延时，如需周期性延时请使用 Marker + 计分板方法
