---
id: t0486
title: "NBT与计分板互转"
title_en: "nbt_scoreboard_interop"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/nbttransfer"
source_type: "mcc_wiki"
source_issue: "questions/nbttransfer"
version_min: "1.13"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["nbt", "scoreboard", "data-get", "execute-store", "data-transfer"]
verified_in_game: false
---

## 核心洞见

通过 /execute store 和 /data get 的组合，可以在计分板分数和任意数值型 NBT 标签之间双向读写，包括列表和复合标签中的数值。

## 代码示例

```mcfunction
# NBT --> Score: 将实体的X坐标乘以100后存入计分板
# 用法：执行此函数后，@s 的 y_pos 分数将等于其Y坐标的100倍
# 注意：/data get 的结果会被截断为整数，使用缩放因子可保留小数精度
execute store result score @s y_pos run data get entity @s Pos[1] 100

# Score --> NBT: 将计分板分数写入实体NBT
# 用法：将 @s 的 y_speed 分数乘以0.05后写入最近苦力怕的Y轴运动
# 注意：数据类型必须与目标NBT标签匹配（此处Motion[1]为double）
execute store result entity @e[type=creeper,limit=1,sort=nearest] Motion[1] double 0.05 run scoreboard players get @s y_speed

# NBT --> NBT: 直接从一个NBT路径复制到另一个NBT路径
# 用法：将最近鸡的X坐标复制给最近猪的X坐标
# 注意：中间结果始终被截断为整数，因此需要缩放/反缩放来保留精度
execute store result entity @e[type=pig,limit=1,sort=nearest] Pos[0] double 0.01 run data get entity @e[type=chicken,limit=1,sort=nearest] Pos[0] 100
```

## 文件结构

（待补充）

## 用法

这些命令可以直接在聊天栏、命令方块或函数文件中执行。无需额外文件结构，只需确保目标实体/方块存在且计分板目标已创建。

## 使用场景

['将实体的位置、旋转、速度等浮点NBT数据存入计分板进行数学运算（如计算距离、角度）', '将计分板运算结果写回实体NBT以控制行为（如设置运动、自定义模型数据）', '在不同实体之间复制NBT数值（如同步位置、属性）']

## 机制原理

该技术的核心在于 Minecraft 命令系统的两个关键机制：
1. `/data get` 命令会返回指定 NBT 路径的数值作为命令结果（command result），该结果会被截断为整数。通过可选的 `<scale>` 参数，可以在截断前对数值进行缩放，从而保留小数精度（例如乘以100再存储，读取时再除以100）。
2. `/execute store result` 可以将后续命令的返回值（command result）存储到指定目标：可以是计分板分数（`score <target> <objective>`），也可以是实体或方块的 NBT 路径（`entity <target> <path>` 或 `block <pos> <path>`）。写入 NBT 时需指定数据类型（byte/double/float/int/long/short）和缩放因子。
3. 组合使用：`/execute store result score ... run data get ...` 实现 NBT→计分板；`/execute store result entity ... run scoreboard players get ...` 实现计分板→NBT；`/execute store result entity ... run data get ...` 实现 NBT→NBT 直接复制。
4. 关键限制：命令结果始终是整数，因此 NBT→NBT 直接复制时，即使源和目标都是浮点类型，中间也会经过整数截断，必须通过缩放/反缩放来保持精度。

## 注意事项

- 玩家（Player）的 NBT 数据无法通过 `/execute store result entity` 修改，这是 Minecraft 的安全限制
- 写入 NBT 时，数据类型参数必须与目标标签的实际类型匹配，否则可能导致错误或数据损坏
- 缩放因子在读取和写入时是独立的：读取时乘以 scale 再截断整数，写入时乘以 scale 再按指定类型存储
- NBT→NBT 直接复制时，中间结果始终被截断为整数，即使源和目标都是浮点类型，也需要缩放来保留精度
- 此功能在 Minecraft 1.13 及以后版本中可用
