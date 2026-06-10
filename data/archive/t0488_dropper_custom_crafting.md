---
id: t0488
title: "投掷器自定义合成"
title_en: "dropper_custom_crafting"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/customcrafting"
source_type: "mcc_wiki"
source_issue: "questions/customcrafting"
version_min: "1.19.4"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["custom_crafting", "dropper_crafting", "block_nbt", "ui_crafting"]
verified_in_game: false
---

## 核心洞见

利用投掷器/发射器的物品存储界面作为合成网格，通过检测方块NBT数据实现支持NBT的自定义合成。

## 代码示例

```mcfunction
# 1.19.4 - 1.20.4 版本：放置自定义合成台的刷怪蛋
give @p bat_spawn_egg{EntityTag:{id:"minecraft:item_display",Tags:["custom_crafting","placing"],Rotation:[0f,0f],brightness:{sky:10,block:10},transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0.5f,0f],scale:[1.01f,1.01f,1.01f]},item:{id:"minecraft:crafting_table",Count:1b}},display:{Name:'"Custom Crafting Table"'}}

# 1.20.5+ 版本：放置自定义合成台的刷怪蛋
give @p bat_spawn_egg[entity_data={id:"minecraft:item_display",Tags:["custom_crafting","placing"],Rotation:[0f,0f],brightness:{sky:10,block:10},transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0.5f,0f],scale:[1.01f,1.01f,1.01f]},item:{id:"minecraft:crafting_table",count:1}},item_name='"Custom Crafting Table"']

# 控制器命令（1.19.4 - 1.20.4）
execute at @e[type=item_display,tag=custom_crafting,tag=placing] run setblock ~ ~ ~ dropper[facing=up]{CustomName:'"Custom Crafting Table"'}
tag @e[type=item_display,tag=custom_crafting,tag=placing] remove placing
execute as @e[type=item_display,tag=custom_crafting] at @s unless block ~ ~ ~ dropper[facing=up] run data modify entity @e[type=item,distance=..1,nbt={Item:{id:"minecraft:dropper"}},limit=1] Item set value {id:"minecraft:bat_spawn_egg",Count:1b,tag:{EntityTag:{id:"minecraft:item_display",Tags:["custom_crafting","placing"],Rotation:[0f,0f],brightness:{sky:10,block:10},transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0.5f,0f],scale:[1.01f,1.01f,1.01f]},item:{id:"minecraft:crafting_table",Count:1b}},display:{Name:'"Custom Crafting Table"'}}}
execute as @e[type=item_display,tag=custom_crafting] at @s unless block ~ ~ ~ dropper[facing=up] run kill @s

# 配方命令示例（1.19.4 - 1.20.4）
execute at @e[type=item_display,tag=custom_crafting] if block ~ ~ ~ dropper{Items:[{Slot:0b,id:"minecraft:emerald",Count:1b}, {Slot:2b,id:"minecraft:emerald",Count:1b}, {Slot:3b,id:"minecraft:redstone",Count:1b}, {Slot:4b,id:"minecraft:diamond",Count:1b}, {Slot:5b,id:"minecraft:redstone",Count:1b}, {Slot:6b,id:"minecraft:redstone",Count:1b}, {Slot:7b,id:"minecraft:redstone",Count:1b}, {Slot:8b,id:"minecraft:redstone",Count:1b}]} run data modify block ~ ~ ~ Items set value [{Slot:4b,id:"minecraft:ender_eye",Count:1b,tag:{custom_result:true,display:{Name:'{"text":"Some Custom Result","italic":false}'}}}]

# 配方命令示例（1.20.5+）
execute at @e[type=item_display,tag=custom_crafting] if items block ~ ~ ~ container.0 emerald[custom_data~{some:true}] unless items block ~ ~ ~ container.1 * if items block ~ ~ ~ container.2 emerald[custom_data~{some:true}] if items block ~ ~ ~ container.3 redstone[custom_data~{data:true}] if items block ~ ~ ~ container.4 diamond[custom_data~{custom:true}] if items block ~ ~ ~ container.5 redstone[custom_data~{data:true}] if items block ~ ~ ~ container.6 redstone[custom_data~{data:true}] if items block ~ ~ ~ container.7 redstone[custom_data~{data:true}] if items block ~ ~ ~ container.8 redstone[custom_data~{data:true}] run data modify block ~ ~ ~ Items set value [{Slot:4b,id:"minecraft:ender_eye",count:1b,components:{"minecraft:custom_data":{custom_result:true},"minecraft:item_name":'"Some Custom Result"'}}]
```

## 文件结构

（待补充）

## 用法

1. 使用刷怪蛋放置自定义合成台（item_display实体）
2. 控制器命令自动在实体位置放置朝上的投掷器
3. 玩家打开投掷器界面放入物品
4. 配方命令检测投掷器内的物品是否符合配方，符合则替换为合成结果
5. 破坏投掷器时，控制器命令会返还刷怪蛋并清除item_display实体

## 使用场景

['需要类似工作台的UI交互且支持NBT自定义物品的合成系统', '比地板合成更美观、更可控的合成方式', '不适合需要大量配方的场景（每个配方一个命令方块）']

## 机制原理

该技术使用投掷器/发射器的物品存储界面模拟3x3合成网格。核心机制是：通过`item_display`实体作为视觉装饰，在实体位置放置一个朝上的投掷器。玩家打开投掷器界面放入物品后，配方命令使用`if block ~ ~ ~ dropper{Items:[...]}`检测投掷器方块NBT中的Items列表是否匹配配方。匹配成功后，使用`data modify block ~ ~ ~ Items set value [...]`将投掷器内的物品替换为合成结果。1.20.5+版本可以使用`if items block`命令更精确地检测物品组件。控制器部分负责放置投掷器、在投掷器被破坏时返还刷怪蛋并清理实体。

## 注意事项

- 此方法需要1.19.4+版本（使用item_display），早期版本可用falling_block替代
- 空槽位中如果玩家放入了非配方物品，这些物品会被删除；可以通过`unless data block`检查空槽位来避免
- 可以使用F3+I复制投掷器的完整NBT数据来辅助编写配方检测命令，但需要移除无关的NBT数据
- 每个配方需要一个独立的命令方块
- 1.20.5+版本中配方检测推荐使用`if items block`命令，更简洁且支持组件匹配
