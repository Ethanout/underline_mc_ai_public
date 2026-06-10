---
id: t0516
title: "朝向发射实体"
title_en: "shoot_facing_direction"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/shootfacing"
source_type: "mcc_wiki"
source_issue: "questions/shootfacing"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: high
tags: ["motion", "vector", "projectile", "local-coordinates", "entity-shooting"]
verified_in_game: false
---

## 核心洞见

利用局部坐标和世界零点，通过位置差计算运动向量，无需手动计算三角函数即可让实体沿玩家朝向飞行。

## 代码示例

```mcfunction
# Method 1: 简化版（依赖世界零点加载，推荐使用 marker）
# 以玩家身份和位置执行
# 在世界零点处召唤临时实体，位于玩家前方1格
execute positioned 0.0 0 0.0 run summon marker ^ ^ ^1 {Tags:["direction"]}
# 召唤弹射物实体（例如羊，也可以是箭/雪球等）
summon sheep ~ ~ ~ {Tags:["projectile"]}
# 将标记实体的位置复制到弹射物的运动标签
数据修改实体 @e[type=sheep,tag=projectile,limit=1] Motion set from entity @e[type=marker,tag=direction,limit=1] Pos
# 清理
tag @e[tag=projectile] remove projectile
kill @e[tag=direction]

# Method 2: 改进版（不依赖零点加载，推荐使用 marker）
# 主函数（以玩家身份和位置执行）
# 在玩家位置召唤标记实体
summon marker ~ ~ ~ {Tags:["direction"]}
# 以标记实体身份，在世界零点位置执行函数获取运动向量
execute as @e[tag=direction,limit=1] positioned 0.0 0.0 0.0 run function example:get_motion
# 在玩家眼睛前方召唤弹射物
execute anchored eyes run summon sheep ^ ^ ^1 {Tags:["projectile"]}
# 将存储的运动向量应用到弹射物
data modify entity @e[tag=projectile,limit=1] Motion set from storage example:storage Motion
# 清理
tag @e[tag=projectile] remove projectile

# 函数 example:get_motion
# 以标记实体身份，位于世界零点，但旋转仍为玩家朝向
# 将实体向前传送1格
tp @s ^ ^ ^1
# 将当前位置存储到NBT存储中
data modify storage example:storage Motion set from entity @s Pos
# 删除标记实体
kill @s

# Method 3: 使用计分板存储所有值（消耗高，不推荐）
# 假设已创建计分板 pos
# 以玩家身份和位置执行
# 召唤临时实体
summon marker ^ ^ ^1 {Tags:["direction"]}
# 获取玩家和目标的坐标（放大1000倍）
execute store result score #playerX pos run data get entity @s Pos[0] 1000
execute store result score #playerY pos run data get entity @s Pos[1] 1000
execute store result score #playerZ pos run data get entity @s Pos[2] 1000
execute store result score #targetX pos as @e[type=marker,tag=direction,limit=1] run data get entity @s Pos[0] 1000
execute store result score #targetY pos as @e[type=marker,tag=direction,limit=1] run data get entity @s Pos[1] 1000
execute store result score #targetZ pos as @e[type=marker,tag=direction,limit=1] run data get entity @s Pos[2] 1000
# 计算差值
scoreboard players operation #targetX pos -= #playerX pos
scoreboard players operation #targetY pos -= #playerY pos
scoreboard players operation #targetZ pos -= #playerZ pos
# 召唤弹射物实体
summon sheep ~ ~ ~ {Tags:["projectile"]}
# 应用运动（缩小1000倍）
execute store result entity @e[type=sheep,tag=projectile,limit=1] Motion[0] double 0.001 run scoreboard players get #targetX pos
execute store result entity @e[type=sheep,tag=projectile,limit=1] Motion[1] double 0.001 run scoreboard players get #targetY pos
execute store result entity @e[type=sheep,tag=projectile,limit=1] Motion[2] double 0.001 run scoreboard players get #targetZ pos
# 清理
tag @e[tag=projectile] remove projectile
kill @e[tag=direction]

# 视觉错误修复（下一tick更新Air标签）
execute as @e[tag=projectile] store result entity @s Air short 1 run time query gametime

# 命令方块完整示例
# 聊天栏中：
scoreboard objectives add click used:carrot_on_a_stick
forceload add -1 -1 0 0
# 命令方块链：
execute as @e[tag=projectile] store result entity @s Air short 1 run time query gametime
tag @e[tag=projectile] remove projectile
execute as @a[scores={click=1..}] at @s anchored eyes run summon snowball ^ ^ ^ {Tags:["projectile"]}
execute rotated as @a[scores={click=1..}] positioned 0.0 0.0 0.0 positioned ^ ^ ^1 summon minecraft:area_effect_cloud run data modify entity @e[tag=projectile,limit=1] Motion set from entity @s Pos
scoreboard players reset @a click

# 数据包完整示例
# function example:tick
execute as @a[scores={click=1..}] at @s run function example:click

# function example:click
scoreboard players reset @s click
execute anchored eyes positioned ^ ^ ^ summon snowball run function example:shootfacing

# function example:shootfacing
tag @s add this
execute positioned 0.0 0.0 0.0 positioned ^ ^ ^1 summon minecraft:area_effect_cloud run data modify entity @e[tag=this,limit=1] Motion set from entity @s Pos
tag @s remove this
tag @s add fix
schedule function example:fix 2t replace

# function example:fix
execute unless entity @s as @e[tag=fix] run function example:fix
execute store result entity @s Air short 1 run time query gametime
tag @s remove fix
```

## 文件结构

- data/example/functions/get_motion.mcfunction
- data/example/functions/tick.mcfunction
- data/example/functions/click.mcfunction
- data/example/functions/shootfacing.mcfunction
- data/example/functions/fix.mcfunction

## 用法

构建完数据包后，玩家使用胡萝卜钓竿（或其他触发方式）即可在玩家朝向方向发射弹射物。也可通过函数命令手动调用。

## 使用场景

['制作自定义弹射物武器（如魔法弹、火球）', '实现玩家朝向发射任意实体（如羊、TNT）', '需要精确控制弹射物运动向量且避免手动三角计算的场景']

## 机制原理

该技术的核心原理是利用局部坐标 `^ ^ ^` 和世界零点 `0 0 0` 来简化向量计算。Motion 是一个三维向量，表示实体每 tick 移动的方块数。要计算玩家朝向的运动向量，需要知道起点 P（玩家位置）和终点 T（玩家前方1格位置），然后计算差值 V = T - P。

方法1利用数学性质：当玩家位于世界零点时，`^ ^ ^1` 位置的坐标直接就是运动向量（因为 P = (0,0,0)，所以 V = T - 0 = T）。通过 `execute positioned 0.0 0.0 0.0` 将执行位置临时设为世界零点，然后使用 `^ ^ ^1` 召唤实体，该实体的 Pos 就是所需的运动向量。最后通过 `data modify` 将这个位置数据直接复制到弹射物的 Motion 标签。

方法2使用计分板进行精确计算：分别获取玩家和前方1格实体的坐标（放大1000倍以保留精度），计算差值，再缩小后写入 Motion。这种方法允许在计算后对运动向量进行任意修改（如调整速度、添加随机偏移等）。

视觉错误修复是因为某些实体在生成并立即设置 Motion 后，客户端不会立即更新其位置，导致视觉上出现延迟。通过在下一 tick 更新实体的 Air 标签（或其他 NBT 数据），强制客户端重新同步实体状态，从而消除视觉滞后。

## 注意事项

- 方法1需要世界零点 (0,0,0) 所在的区块被加载，否则标记实体可能丢失
- Motion 值被限制在 [-10, 10] 范围内，超出会被截断
- 方法2使用计分板存储时，坐标放大1000倍，当坐标超过2,000,000时可能溢出，可改为100倍
- 视觉修复必须在下一 tick 执行，不能在同一 tick（原文表述需核实：schedule 使用2tick延迟是因为tick函数在schedule函数之前运行）
- 1.19.4+ 版本可使用 `execute summon` 简化流程
- 旧版本（无 marker 实体）可用 area_effect_cloud 替代
