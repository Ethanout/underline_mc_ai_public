---
id: t0505
title: "分数坐标召唤实体"
title_en: "summon_entity_at_score_position"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/movetoscore"
source_type: "mcc_wiki"
source_issue: "questions/movetoscore"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["summon", "teleport", "scoreboard", "macro", "execute_store", "end_gateway"]
verified_in_game: false
---

## 核心洞见

通过宏函数或 execute store 将记分板数值直接注入 summon/tp 命令的坐标参数，实现从分数到位置的精确转换

## 代码示例

```mcfunction
# 方法1：宏函数（1.20.2+）
# Setup
scoreboard objectives add pos dummy
scoreboard players set X pos 10
scoreboard players set Y pos 64
scoreboard players set Z pos 10
function example:summon/pig

# function example:summon/pig
execute store result storage example:macro pos.x int 1 run scoreboard players get X pos
execute store result storage example:macro pos.y int 1 run scoreboard players get Y pos
execute store result storage example:macro pos.z int 1 run scoreboard players get Z pos
function example:summon/pig_macro with storage example:macro pos

# function example:summon/pig_macro
$summon minecraft:pig $(x) $(y) $(z) {Tags:["custom_pig"]}
$particle minecraft:happy_villager $(x) $(y) $(z) 0.5 0.5 0.5 0 200
$tellraw @a "Pig summoning at $(x) $(y) $(z)"

# 方法2：直接传参宏函数
# In chat
function example:macro_summon {id:"minecraft:pig",x:25.5d, y:65.5d, z:-15.5d}

# function example:macro_summon
$summon $(id) $(x) $(y) $(z)

# 方法3：execute store 直接修改实体Pos（非玩家）
execute store result entity @s Pos[0] double 1 run scoreboard players get @s posX
execute store result entity @s Pos[1] double 1 run scoreboard players get @s posY
execute store result entity @s Pos[2] double 1 run scoreboard players get @s posZ

# 方法4：先存到storage再批量写入（避免卸载实体）
data merge storage example:data {Pos:[0d,0d,0d]}
execute store result storage example:data Pos[0] double 1 run scoreboard players get @s posX
execute store result storage example:data Pos[1] double 1 run scoreboard players get @s posY
execute store result storage example:data Pos[2] double 1 run scoreboard players get @s posZ
data modify entity @s Pos set from storage example:data Pos
```

## 文件结构

- data/example/functions/summon/pig.mcfunction
- data/example/functions/summon/pig_macro.mcfunction
- data/example/functions/macro_summon.mcfunction

## 用法

构建数据包后，通过 function 命令调用对应函数。宏函数需先设置 storage 数据再调用 with storage；直接传参可在聊天栏执行 function example:macro_summon {id:"minecraft:pig",x:25.5d,y:65.5d,z:-15.5d}

## 使用场景

['需要根据记分板动态数值在指定坐标生成实体（如自定义传送点、刷怪系统）', '需要将玩家传送到由记分板计算出的精确位置', '需要批量处理多个实体的位置更新，避免逐个修改 NBT 导致的卸载问题']

## 机制原理

Minecraft 1.20.2 引入的宏函数允许在函数中使用 $(变量名) 占位符，执行时从 storage 或命令参数中读取实际值并替换到命令中。这绕过了传统命令中坐标参数必须为字面常量的限制。对于非玩家实体，execute store result entity 可以直接将记分板数值写入实体的 Pos NBT 数组，但逐个写入时若实体进入未加载区块会导致后续写入失败。先写入 storage 再整体复制到实体可以避免此问题，因为 storage 不依赖实体位置。对于玩家（无法修改 NBT），宏函数是最直接的方法；End Gateway 利用其 ExactTeleport 功能实现精确传送；二进制传送法通过逐次检查 2 的幂次并相对传送，将分数值分解为二进制位逐步累加位移，适用于所有版本包括基岩版。

## 注意事项

- 宏数据不能在同一个函数中设置并立即使用，必须分到两个函数
- 宏不能从 List/Array 读取，只能从对象读取；若输入是列表需先转换为对象
- 若坐标位于非完整方块（如半砖）内且下方无实心方块，实体可能掉落穿模
- 使用 End Gateway 时若 Age 标签未设为负数，新生成的传送门可能射出光束
- 1.20.5+ 中 End Gateway 的 ExitPortal 标签被替换为 exit_portal 整数数组
- 二进制传送法适用于基岩版
