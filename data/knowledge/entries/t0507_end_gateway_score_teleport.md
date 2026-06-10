---
id: t0507
title: "末地折跃门分数传送"
title_en: "end_gateway_score_teleport"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/movetoscore"
source_type: "mcc_wiki"
source_issue: "questions/movetoscore"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["teleport", "scoreboard", "end_gateway", "execute_store", "nbt"]
verified_in_game: false
---

## 核心洞见

利用末地折跃门方块的 ExactTeleport 和 ExitPortal NBT 标签，通过 execute store 动态设置出口坐标，实现玩家精确传送

## 代码示例

```mcfunction
# 1.13 - 1.20.4
setblock 0 5 0 minecraft:end_gateway{ExactTeleport:1b,ExitPortal:{X:0,Y:0,Z:0},Age:-9223372036854775808L}
execute store result block 0 5 0 ExitPortal.X int 1 run scoreboard players get @s MapX
execute store result block 0 5 0 ExitPortal.Y int 1 run scoreboard players get @s MapY
execute store result block 0 5 0 ExitPortal.Z int 1 run scoreboard players get @s MapZ
tp @s 0 5 0

# 1.20.5+
setblock 0 5 0 minecraft:end_gateway{ExactTeleport:1b,exit_portal:[I;0,0,0],Age:-9223372036854775808L}
execute store result block 0 5 0 exit_portal[0] int 1 run scoreboard players get @s MapX
execute store result block 0 5 0 exit_portal[1] int 1 run scoreboard players get @s MapY
execute store result block 0 5 0 exit_portal[2] int 1 run scoreboard players get @s MapZ
tp @s 0 5 0
```

## 文件结构

（待补充）

## 用法

在函数中依次执行：放置末地折跃门方块（设置 ExactTeleport 和 Age），用 execute store 将记分板值写入出口坐标 NBT，最后将玩家传送到折跃门方块位置触发传送。构建完数据包即可在游戏内调用该函数。

## 使用场景

['需要将玩家传送到由记分板计算出的精确位置，且版本在 1.13 以上', '作为宏函数的替代方案（1.20.2 之前或不想使用数据包宏时）', '需要一次性传送大量玩家到不同位置（每个玩家可独立设置折跃门出口）']

## 机制原理

末地折跃门方块（end_gateway）具有 ExactTeleport 标签，当设为 1b 时，玩家进入该方块会被精确传送到 ExitPortal（1.20.5 前）或 exit_portal（1.20.5+）指定的坐标，而非随机传送。通过 execute store result block 可以将记分板数值动态写入方块的 NBT 标签，从而在运行时设定目标坐标。Age 标签设为极负数（-9223372036854775808L）可防止折跃门射出光束。玩家通过 tp 进入折跃门方块位置触发传送。此方法利用了方块 NBT 可被 execute store 修改的特性，而玩家 NBT 不可修改，因此绕过了玩家位置无法直接写入的限制。

## 注意事项

- 折跃门方块位置必须在已加载区块中
- 若 Age 标签未设为负数，新放置的折跃门可能射出光束
- 1.20.5+ 中 ExitPortal 复合标签被替换为 exit_portal 整数数组，语法不同
- 每次传送都需要重新放置折跃门方块（或确保方块未被破坏）
- 此方法依赖特定方块，在自定义维度或超平坦世界中可能不适用
