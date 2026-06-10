---
id: t0462
title: "动态磁石指南针"
title_en: "lodestone_compass_dynamic_target"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/compasstoplayer"
source_type: "mcc_wiki"
source_issue: "questions/compasstoplayer"
version_min: "1.16"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["compass", "lodestone", "data modify", "item tracking", "NBT"]
verified_in_game: false
---

## 核心洞见

通过 data modify 动态更新掉落物中磁石指南针的 LodestonePos NBT，可使指南针指向任意玩家或位置，无需放置磁石。

## 代码示例

```mcfunction
# Command block / tick function
execute as @e[type=item,nbt={Item:{tag:{playertracker:1b}}}] at @s run function namespace:update_compass

# function update_compass
tag @p add closest
tag @p[tag=!closest] add target
data modify entity @s Item.tag.LodestonePos.X set from entity @p[tag=target] Pos[0]
data modify entity @s Item.tag.LodestonePos.Y set from entity @p[tag=target] Pos[1]
data modify entity @s Item.tag.LodestonePos.Z set from entity @p[tag=target] Pos[2]
tag @a remove closest
tag @a remove target
data modify entity @s PickupDelay set value 0s
```

## 文件结构

- data/namespace/functions/update_compass.mcfunction

## 用法

构建完数据包后，使用 /give @s compass{LodestoneTracked:0b,LodestonePos:{X:0,Y:64,Z:0},LodestoneDimension:"minecraft:overworld",playertracker:1b} 给予一个带自定义标签的磁石指南针，然后将其丢在地上。数据包会在每个 tick 自动更新其指向为除最近玩家外的另一玩家（即第二近的玩家）。

## 使用场景

['制作指向特定玩家（如队友、敌人）的追踪指南针', '制作指向固定坐标（如基地、Boss 位置）的导航指南针', '不适合需要同时指向多个不同目标且不依赖掉落物的场景（1.17+ 可用 item modifier 改进）']

## 机制原理

1.16 引入的磁石指南针（Lodestone Compass）通过 NBT 标签 LodestonePos、LodestoneDimension 和 LodestoneTracked 定义指向位置。当 LodestoneTracked 设为 0b 时，指南针无需依赖实际存在的磁石，直接指向 NBT 中指定的坐标。利用 data modify 命令，可以从任意实体（如玩家）的 Pos 数据中复制坐标到掉落物中指南针的 LodestonePos，实现动态更新指向。此方法通过自定义标签 playertracker:1b 识别目标物品，使用 tag 命令选择目标玩家（排除最近玩家以模拟指向第二近的玩家），并在更新后重置 PickupDelay 确保物品可被拾取。

## 注意事项

- 原始给予的指南针必须已包含 LodestoneTracked、LodestonePos、LodestoneDimension 和自定义标签 playertracker:1b，否则 data modify 可能失败
- 此方法仅适用于掉落物形态的指南针，无法直接修改玩家背包中的物品（1.17+ 可用 item modifier 解决）
- PickupDelay 重置为 0s 是为了防止更新后物品无法立即拾取（原文表述需核实：原文中设置 PickupDelay 为 0s 可能意图是让物品可立即拾取，但实际行为需测试）
- 版本要求：Java Edition 1.16+
