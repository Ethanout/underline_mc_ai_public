---
id: t0521
title: "宏+战利品表归还背包"
title_en: "return_inventory_via_macro_and_loot_table"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/storeinventory"
source_type: "mcc_wiki"
source_issue: "questions/storeinventory"
version_min: "1.20.2"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["inventory", "macro", "loot_table", "item_replace", "components", "1.20.5"]
verified_in_game: false
---

## 核心洞见

利用 1.20.2+ 的宏功能动态读取背包 NBT 中的 Slot/id/Count/tag，再通过内联战利品表（1.20.5+ 用 set_components）将物品精确放回玩家原始槽位。

## 代码示例

```mcfunction
# 1.20.2-1.20.4 版本
# function example:load
scoreboard objectives add Slot dummy

# function example:returning
## Read player Scoreboard ID
execute store result storage example:inv this.ID int 1 run scoreboard players get @s ID 
## Reading the selected player's data from the entire array of data of all players.
function example:returning/read with storage example:inv this
## Create an empty tag if there is no tag data in the current slot.
execute unless data storage example:inv this.Inventory[-1].tag run data modify storage example:inv this.Inventory[-1].tag set value "" 
## Running the function of returning items from the end of the list.
function example:returning/item with storage example:inv this.Inventory[-1]

# function example:returning/read
$data modify storage example:inv this set from storage example:inv players[{ID:$(ID)}]

# function example:returning/item
## Set the current slot to select slot processing
$scoreboard players set #this Slot $(Slot)
execute if score #this Slot matches 0..35 run function example:returning/inventory with storage example:inv this.Inventory[-1]
execute unless score #this Slot matches 0..35 run function example:returning/equipment with storage example:inv this.Inventory[-1]
## After returning the current item, remove this slot from storage and start returning the next item
data remove storage example:inv this.Inventory[-1]
execute unless data storage example:inv this.Inventory[-1].tag run data modify storage example:inv this.Inventory[-1].tag set value "" 
function example:returning/item with storage example:inv this.Inventory[-1]

# function example:returning/inventory
## For inventory slots, can directly insert Slot into the /item command
function example:returning/equipment with storage example:inv this.Inventory[-1]
$item replace entity @s container.$(Slot) $(id)$(tag) $(Count)

# function example:returning/equipment
## Equipment slots require converting slot number to slot name
$execute if score #this Slot matches -106 run item replace entity @s weapon.offhand $(id)$(tag) $(Count)
$execute if score #this Slot matches 100 run item replace entity @s armor.feet $(id)$(tag) $(Count)
$execute if score #this Slot matches 101 run item replace entity @s armor.legs $(id)$(tag) $(Count)
$execute if score #this Slot matches 102 run item replace entity @s armor.chest $(id)$(tag) $(Count)
$execute if score #this Slot matches 103 run item replace entity @s armor.head $(id)$(tag) $(Count)

# 1.20.5+ 版本（使用内联战利品表）
# function example:load
scoreboard objectives add Slot dummy

# function example:returning
execute store result storage example:inv this.ID int 1 run scoreboard players get @s ID
function example:returning/read with storage example:inv this
execute unless data storage example:inv this.Inventory[-1].components run data modify storage example:inv this.Inventory[-1].components set value {}
function example:returning/item with storage example:inv this.Inventory[-1]

# function example:returning/read
$data modify storage example:inv this set from storage example:inv players[{ID:$(ID)}]

# function example:returning/item
$scoreboard players set #this Slot $(Slot)
execute if score #this Slot matches 0..35 run function example:returning/inventory with storage example:inv this.Inventory[-1]
execute unless score #this Slot matches 0..35 run function example:returning/equipment with storage example:inv this.Inventory[-1]
data remove storage example:inv this.Inventory[-1]
execute unless data storage example:inv this.Inventory[-1].components run data modify storage example:inv this.Inventory[-1].components set value {} 
function example:returning/item with storage example:inv this.Inventory[-1]

# function example:returning/inventory with storage example:inv this.Inventory[-1]
$loot replace entity @s container.$(Slot) loot {pools:[{rolls:1,entries:[{type:"minecraft:item",name:"$(id)",functions:[{function:"minecraft:set_count",count:$(count)},{function:"minecraft:set_components",components:$(components)}]}]}]}

# function example:returning/equipment
$execute if score #this Slot matches -106 run loot replace entity @s weapon.offhand loot {pools:[{rolls:1,entries:[{type:"minecraft:item",name:"$(id)",functions:[{function:"minecraft:set_count",count:$(count)},{function:"minecraft:set_components",components:$(components)}]}]}]}
$execute if score #this Slot matches 100 run loot replace entity @s armor.feet loot {pools:[{rolls:1,entries:[{type:"minecraft:item",name:"$(id)",functions:[{function:"minecraft:set_count",count:$(count)},{function:"minecraft:set_components",components:$(components)}]}]}]}
$execute if score #this Slot matches 101 run loot replace entity @s armor.legs loot {pools:[{rolls:1,entries:[{type:"minecraft:item",name:"$(id)",functions:[{function:"minecraft:set_count",count:$(count)},{function:"minecraft:set_components",components:$(components)}]}]}]}
$execute if score #this Slot matches 102 run loot replace entity @s armor.chest loot {pools:[{rolls:1,entries:[{type:"minecraft:item",name:"$(id)",functions:[{function:"minecraft:set_count",count:$(count)},{function:"minecraft:set_components",components:$(components)}]}]}]}
$execute if score #this Slot matches 103 run loot replace entity @s armor.head loot {pools:[{rolls:1,entries:[{type:"minecraft:item",name:"$(id)",functions:[{function:"minecraft:set_count",count:$(count)},{function:"minecraft:set_components",components:$(components)}]}]}]}
```

## 文件结构

- data/example/functions/load.mcfunction
- data/example/functions/returning.mcfunction
- data/example/functions/returning/read.mcfunction
- data/example/functions/returning/item.mcfunction
- data/example/functions/returning/inventory.mcfunction
- data/example/functions/returning/equipment.mcfunction

## 用法

以玩家身份运行 `function example:returning`。该函数会从 storage `example:inv` 中读取该玩家的背包数据（需先通过存储函数保存），然后逐个槽位将物品放回玩家背包。支持主背包（0-35）、盔甲栏（100-103）和副手（-106）。

## 使用场景

['需要精确将物品放回玩家原始槽位（如小游戏结束后恢复玩家装备）', '需要支持 1.20.5+ 的组件系统（set_components）', '适合与 storage 存储方案配合使用，实现完整的背包保存-归还系统']

## 机制原理

1.20.2 引入的宏功能允许在函数中使用 `$` 前缀和 `$(变量名)` 语法动态插入数据。本技术利用宏读取 storage 中每个物品的 Slot、id、Count、tag（1.20.4 及以前）或 components（1.20.5+）字段，然后通过 `item replace` 或内联战利品表将物品精确放回对应槽位。对于 1.20.5+，由于物品标签被组件系统取代，无法直接通过 `item replace` 命令的 NBT 参数指定组件，因此改用内联战利品表（在函数中直接写 JSON 战利品表）配合 `set_components` 函数来设置物品组件。内联战利品表必须写在宏函数内部，不能作为独立文件。

## 注意事项

- 需要 1.20.2+ 版本（宏功能）
- 1.20.5+ 必须使用内联战利品表方式，因为 item replace 命令不再支持直接指定组件数据
- 内联战利品表必须写在宏函数内部，不能作为独立 loot_table 文件
- 对于没有 tag/components 的物品，需要先设置空值再运行宏，否则宏会报错
- 盔甲栏和副手槽位不能直接用 slot 数字插入，需要单独处理（通过 scoreboard 判断 slot 值）
- 此方法会从 storage 中删除已归还的物品（`data remove`），因此是破坏性操作
