---
id: t0475
title: "execute if items 灵活检测"
title_en: "execute_if_items_flexible_detection"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/detectitem"
source_type: "mcc_wiki"
source_issue: "questions/detectitem"
version_min: "1.20.5"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["execute if items", "item detection", "component predicate", "1.20.5"]
verified_in_game: false
---

## 核心洞见

1.20.5+ 的 `execute if items` 支持按槽位范围、组件子谓词、OR 条件等灵活检测物品，比传统 NBT 目标选择器更强大。

## 代码示例

```mcfunction
# 检测任意槽位中的自定义标签物品
execute as @a if items entity @s container.* minecraft:stick[minecraft:custom_data~{awesome_stick:true}]

# 检测主手物品（使用物品标签）
execute as @a if items entity @s weapon.mainhand #minecraft:banners

# 检测带有特定附魔的物品（子谓词）
execute as @a if items entity @s hotbar.* *[minecraft:enchantments~[{"enchantment":"minecraft:unbreaking"}]]

# 检测耐久度范围
execute as @a if items entity @s weapon *[minecraft:damage~{durability:{max:10}}]

# OR 条件：检测伤害 ≤5 或 ≥40 的物品
execute as @a if items entity @s hotbar.* *[minecraft:damage~{damage:{max:5}}|minecraft:damage~{damage:{min:40}}]

# 检测掉落物
execute as @e[type=item] if items entity @s contents minecraft:stick[minecraft:custom_data~{awesome_stick:true}]

# 检测容器中的物品数量
execute if items block ~ ~ ~ container.* *[minecraft:count~{min:8}]
```

## 文件结构

（待补充）

## 用法

直接在命令方块或数据包函数中使用，无需额外文件。

## 使用场景

['需要检测玩家任意槽位（包括容器、盔甲栏、副手）中的特定物品，而不仅限于主手。', '需要按物品属性（如耐久度、附魔、数量）进行范围或条件组合检测。', '检测掉落物、物品展示框、弹射物中的物品。']

## 机制原理

`execute if items` 是 1.20.5 引入的新子命令，它直接操作物品槽位系统，支持：1) 槽位范围（如 `hotbar.*`、`container.*`）；2) 物品谓词（`<item>[<component>~<predicate>]`），其中 `~` 表示子谓词匹配，允许部分匹配组件数据；3) OR 条件（用 `|` 分隔多个谓词）。相比传统 NBT 检测，它更高效、更灵活，且不依赖数据包即可使用。

## 注意事项

- 槽位范围不支持 `distance=1..5` 这种语法，只能使用 `*` 通配符。
- `container.*` 不包括副手、盔甲栏和末影箱槽位，需额外命令检测这些槽位。
- 组件精确匹配（`=`）要求完全一致，推荐使用子谓词（`~`）以避免因其他组件差异导致失败。
- 此功能仅适用于 1.20.5 及以上版本。
