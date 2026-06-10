---
id: t0520
title: "标记实体存背包"
title_en: "store_player_inventory_via_marker"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/storeinventory"
source_type: "mcc_wiki"
source_issue: "questions/storeinventory"
version_min: "1.17"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["inventory", "marker", "nbt", "storage", "entity"]
verified_in_game: false
---

## 核心洞见

利用 marker 实体可以存储任意 NBT 数据的特性，将玩家背包完整复制到 marker 的 data 字段中，实现离线级背包存储。

## 代码示例

```mcfunction
# function example:new_marker
# summon marker
summon marker ~ ~ ~ {Tags:["inv_store","inv_new"]}

# link marker to player    
scoreboard players operation @e[tag=inv_new] id = @s id

# copy Inventory of player to marker data.Inventory
data modify entity @e[tag=inv_new,limit=1] data.Inventory set from from entity @s Inventory

# remove the new tag to get ready for the next player
tag @e[tag=inv_new] remove inv_new
```

## 文件结构

- data/example/functions/new_marker.mcfunction

## 用法

以玩家身份运行 `function example:new_marker`（需先建立 scoreboard ID 系统）。执行后会在当前位置生成一个 marker 实体，其 data.Inventory 字段保存了该玩家的完整背包数据，并通过 id 分数与玩家绑定。

## 使用场景

['需要将玩家背包保存到实体上，以便后续在任意时间、任意维度归还（如小游戏切换阶段、临时传送场景）', '需要为每个玩家独立保存背包，且希望实体随区块加载/卸载自动管理生命周期', '不适合需要频繁读写大量玩家背包的场景（性能开销较大）']

## 机制原理

marker 实体是 Minecraft 中一种特殊的实体，它没有碰撞箱、没有渲染、没有 AI，但可以像其他实体一样拥有自定义 NBT 数据。通过 `data modify entity` 命令，可以将玩家的 `Inventory` NBT 数组完整复制到 marker 的 `data.Inventory` 字段中。由于 marker 实体可以被 `scoreboard players operation` 通过 ID 系统与玩家绑定，因此可以实现玩家与背包数据的持久化关联。与使用 `storage` 相比，marker 实体的优势在于它会随区块加载/卸载自动管理，且天然支持按实体 ID 查询，无需额外维护列表结构。

## 注意事项

- 执行该函数时建议在出生点区块或确保加载的区块中执行，以保证 marker 实体保持加载
- 需要预先建立 scoreboard ID 系统（如 `id` 计分板）来关联玩家和 marker
- marker 实体在 1.17+ 可用，1.20.5+ 中行为未变化
- 此方法仅存储背包数据，归还时需要额外实现（见文章后续部分）
