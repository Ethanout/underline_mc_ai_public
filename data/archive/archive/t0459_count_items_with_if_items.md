---
id: t0459
title: "if items计数法"
title_en: "count_items_with_if_items"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/amountitems"
source_type: "mcc_wiki"
source_issue: "questions/amountitems"
version_min: "1.20.5"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["item-counting", "execute-if-items", "scoreboard", "item-components", "container"]
verified_in_game: false
---

## 核心洞见

execute if items 子命令会返回匹配物品的数量，可用于精确计数并存储到 scoreboard

## 代码示例

```mcfunction
# Example item
give @s diamond[minecraft:custom_data={diamond:true},minecraft:item_name="'Custom Diamond'"]

# Command blocks
execute as @a store result score @s diamonds if items entity @s container.* *[custom_data~{diamond:true}]
execute as @a[scores={diamonds=5}] run say I have exactly 5 coins.
execute as @a[scores={diamonds=1..4}] run say I have somewhere between 1 and 4 coins.
execute as @a[scores={diamonds=10..}] run say I have 10 or more coins.
execute as @a[scores={diamonds=..20}] run say I have 20 or less coins.

# Counting items in chest or any container
execute store result score #container diamonds if items block <pos> container.* *[custom_data~{diamond:true}]

# Counting items in ender_chest
execute as @a store result score @s diamonds if items entity @s enderchest.* *[custom_data~{diamond:true}]
```

## 文件结构

- data/<namespace>/functions/count_custom_items.mcfunction

## 用法

将命令放入函数或命令方块中执行。需要先创建 scoreboard 目标。对玩家执行时使用 as @a，对容器使用 block 坐标。

## 使用场景

['精确计数带有特定组件（如 custom_data、item_name）的自定义物品', '统计容器（箱子、潜影盒等）中特定物品的数量', '统计玩家末影箱中的物品数量', '需要比 clear 命令更灵活的匹配条件时']

## 机制原理

execute if items 子命令在 1.20.5 引入，它不仅是一个条件判断，还会返回匹配物品的数量。当与 execute store result 结合时，可以将这个数量存储到 scoreboard 中。与 clear 命令不同，if items 支持物品组件匹配（如 custom_data、item_name 等），并且可以作用于容器方块、末影箱等多种来源。container.* 表示所有容器槽位，* 表示匹配所有物品，配合物品谓词可以精确筛选。

## 注意事项

- 需要 Minecraft 1.20.5 或更高版本
- if items 返回的是匹配物品的总数，而不是堆叠数
- container.* 不包括盔甲栏和副手槽，如需包含需额外指定
- 物品谓词语法（如 [custom_data~{diamond:true}]）需要 1.20.5 及以上版本支持
