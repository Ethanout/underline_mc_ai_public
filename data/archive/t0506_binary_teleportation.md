---
id: t0506
title: "二进制传送法"
title_en: "binary_teleportation"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/movetoscore"
source_type: "mcc_wiki"
source_issue: "questions/movetoscore"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["teleport", "scoreboard", "binary", "cross_version", "bedrock"]
verified_in_game: false
---

## 核心洞见

通过逐次检查 2 的幂次并相对传送，将记分板数值分解为二进制位逐步累加位移，实现跨版本（含基岩版）的分数到位置传送

## 代码示例

```mcfunction
execute as @a unless score @s xTmp matches 0 if score @s xTmp = @s xTmp run teleport @s 0 0 0

execute as @a[scores={xTmp=128..}] at @s run tp @s ~128 ~ ~
scoreboard players remove @a[scores={xTmp=128..}] xTmp 128

execute as @a[scores={xTmp=64..}] at @s run tp @s ~64 ~ ~
scoreboard players remove @a[scores={xTmp=64..}] xTmp 64

execute as @a[scores={xTmp=32..}] at @s run tp @s ~32 ~ ~
scoreboard players remove @a[scores={xTmp=32..}] xTmp 32

....
all the way down to 1, repeat for all 3 coordinates
```

## 文件结构

- data/<namespace>/functions/binary_tp_x.mcfunction
- data/<namespace>/functions/binary_tp_y.mcfunction
- data/<namespace>/functions/binary_tp_z.mcfunction

## 用法

将目标坐标值复制到临时记分板（如 xTmp），然后依次执行从最高 2 的幂到 1 的检查-传送-减法命令链。需为 X、Y、Z 三个坐标分别实现一套命令链。构建完数据包即可在游戏内通过 function 调用触发。

## 使用场景

['需要将玩家传送到由记分板计算出的精确位置，且无法使用宏或 End Gateway（如旧版本或基岩版）', '需要跨版本兼容（Java 和基岩版均可用）', '作为宏函数或 End Gateway 方法的备选方案，不依赖特定方块或版本特性']

## 机制原理

二进制传送法的核心思想是将一个整数坐标值分解为 2 的幂次之和（即二进制表示）。例如，坐标值 173 = 128 + 32 + 8 + 4 + 1。通过从最高位（如 128）到最低位（1）依次检查：若当前临时记分板值 >= 该幂次，则相对传送对应距离，并从记分板中减去该值。重复此过程直到记分板归零。由于每次传送都是相对位移（~128 ~ ~），最终位置等于所有位移之和，即原始坐标值。这种方法不需要修改 NBT、不需要特定方块、不依赖版本特性，仅使用基础的 execute、tp、scoreboard 命令，因此跨版本兼容。注意：需要先通过 tp @s 0 0 0 将玩家重置到原点（或已知参考点），否则相对位移会叠加在当前位置上。

## 注意事项

- 需要先重置玩家位置到原点（或已知参考点），否则相对位移会叠加在当前位置上
- 命令数量较多（每个坐标需要约 8-16 条命令，取决于坐标范围），但使用函数可以组织清晰
- 始终从最高的 2 的幂开始检查，否则算法不成立
- 适用于基岩版
