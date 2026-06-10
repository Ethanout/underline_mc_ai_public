---
id: t0522
title: "潜影盒归还背包"
title_en: "return_inventory_via_shulkerbox_trick"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/storeinventory"
source_type: "mcc_wiki"
source_issue: "questions/storeinventory"
version_min: "1.17"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["inventory", "shulker_box", "loot", "give", "trick"]
verified_in_game: false
---

## 核心洞见

利用潜影盒的 drop_contents 战利品表特性，将 marker 实体中的背包物品逐个通过潜影盒中转，再用 /loot give 归还给玩家，避免物品掉落在地。

## 代码示例

```mcfunction
# 前提：需要有一个黄色潜影盒放置在世界的某个位置（记为 <pos>）
# 需要预先设置好 drop_contents 战利品表（见 wiki/questions/modifyinventory）

# function namespace:restore_shulker_main
# 以 marker 实体身份执行，目标玩家标记为 @a[tag=target]
# count the amount of items in the array so we know how often to repeat
execute store result score #items temp run data get entity @s data.Inventory
# if there is at least one item, start the process.
execute if score #items temp matches 1.. positioned <pos> run function namespace:restore_shulker

# remove entity, it served its purpose. If you want to keep it around
# you should first copy the data and work on the copy instead.
kill @s

# function namespace:restore_shulker
# reset the shulkerbox
data merge block ~ ~ ~ {Items:[]}
# remove Slot data from item
data remove entity @s data.Inventory[0].Slot
# copy first item over to the shulkerbox
data modify block ~ ~ ~ Items append from entity @s data.Inventory[0]
# use /loot to give it back to the player
loot give @a[tag=target] mine ~ ~ ~ minecraft:air{drop_contents:1b}
# remove the first entry in the list
data remove entity @s data.Inventory[0]
# remove 1 from the amount of items that we still need to process
scoreboard players remove #items temp 1

# run the same function again if there are more items to process
execute if score #items temp matches 1.. run function namespace:restore_shulker
```

## 文件结构

- data/namespace/functions/restore_shulker_main.mcfunction
- data/namespace/functions/restore_shulker.mcfunction
- data/namespace/loot_tables/drop_contents.json（需自行创建，参考 wiki/questions/modifyinventory）

## 用法

以 marker 实体身份运行 `function namespace:restore_shulker_main`，目标玩家需有 `target` 标签。该函数会逐个将 marker 中的物品通过黄色潜影盒中转，使用 `/loot give` 归还给玩家。如果玩家背包满，剩余物品会留在潜影盒中（但函数每次都会清空潜影盒，所以实际会丢失）。

## 使用场景

['需要将物品归还给玩家，但不关心原始槽位（物品会进入玩家背包任意空位）', '玩家可能正在移动或附近有其他玩家，不希望物品掉落在地', '适合物品数量不超过 36 个（玩家背包容量）的场景']

## 机制原理

黄色潜影盒（minecraft:yellow_shulker_box）有一个特殊的战利品表机制：当使用 `/loot give` 或 `/loot insert` 命令指定 `minecraft:air{drop_contents:1b}` 作为来源时，游戏会读取该潜影盒的 Items 数据，将其中的物品以战利品形式给予玩家。本技术利用这一特性：先将 marker 实体中的单个物品复制到潜影盒（同时移除 Slot 数据，因为潜影盒只有 27 个槽位，Slot 值可能超出范围导致物品被丢弃），然后立即用 `/loot give` 将潜影盒中的物品给予玩家。每次只处理一个物品，循环直到所有物品归还完毕。

## 注意事项

- 需要预先放置一个黄色潜影盒在世界中，并配置好 drop_contents 战利品表
- 每次循环都会清空潜影盒（`data merge block ~ ~ ~ {Items:[]}`），确保只处理当前物品
- 必须移除物品的 Slot 数据，否则 Slot 值超出潜影盒范围（0-26）会导致物品被丢弃
- 如果玩家背包已满，`/loot give` 不会给予物品，且该物品会丢失（因为潜影盒已被清空）
- 此方法一次只处理一个物品，效率较低，但避免了大量物品实体掉落
- 需要 dummy 计分板（如 temp）来计数
