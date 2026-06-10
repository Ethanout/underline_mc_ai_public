---
id: t0483
title: "修改玩家物品"
title_en: "modify_player_inventory_item"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/modifyinventory"
source_type: "mcc_wiki"
source_issue: "questions/modifyinventory"
version_min: "1.14"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["item modification", "player inventory", "item modifier", "loot table", "shulker box"]
verified_in_game: false
---

## 核心洞见

通过 /item 命令和 item_modifier 可以直接修改玩家物品栏中的物品，无需复制到中间容器。

## 代码示例

```mcfunction
# 1.20.5+ 示例：为手持物品添加食物组件（如果该物品不是食物）
execute as @a if items entity @s weapon *[!minecraft:food] run item modify entity @s weapon {function:"minecraft:set_components", components: {"minecraft:food": {nutrition:1, saturation:2, can_always_eat:true, eat_seconds:3.2}}}

# 1.20.5+ 示例：将铁剑改为金剑，保留其他组件
execute as @a run item modify entity @s weapon {function:"minecraft:filtered", item_filter: {items:"minecraft:iron_sword"}, modifier: {function:"minecraft:set_item", item:"minecraft:golden_sword"}}

# 1.17+ 使用 item replace 的示例：添加附魔
# 设置
setblock chest <pos>
# 将玩家物品复制到箱子
item replace block <pos> container.0 from entity <player> weapon.mainhand
# 修改物品数据
data modify block <pos> Items[0] merge value {tag: {Enchantments: [{id: "minecraft:knockback", lvl: 1s}]}}
# 将物品返回玩家
item replace entity <player> weapon.mainhand from block <pos> container.0

# 1.17+ 使用 item modify 的示例：添加附魔（需要数据包）
# 命令
item modify entity <player> weapon.mainhand example:add_knockback

# 数据包中的 item_modifier 文件 (data/example/item_modifiers/add_knockback.json)
{
  "function": "minecraft:set_enchantments",
  "enchantments": {
    "knockback": 1
  },
  "add": true
}

# 1.16 及以下版本：使用潜影盒和 loot 命令
# 初始化
setblock <pos> minecraft:yellow_shulker_box

# 编辑物品
# 将物品复制到 storage
data modify storage lilith:example Item set from entity <player> SelectedItem
# 修改物品数据，设置 Slot 为 0
data modify storage lilith:example Item merge value {tag: {Enchantments: [{id: "minecraft:knockback", lvl: 1s}]}}
data modify storage lilith:example Item.Slot set value 0b
# 将 storage 中的物品复制到潜影盒
data modify block <pos> Items append from storage lilith:example Item
# 将潜影盒中的物品替换到玩家手中
loot replace entity <player> weapon.mainhand 1 mine <pos> minecraft:air{drop_contents: 1b}
```

## 文件结构

- data/example/item_modifiers/add_knockback.json

## 用法

构建完数据包即可在游戏内测试效果。对于 1.17+ 的 item modify 方法，需要先创建 item_modifier JSON 文件，然后使用 /item modify 命令触发。对于 1.16 及以下版本，需要先放置潜影盒，然后执行一系列命令。

## 使用场景

['动态修改玩家手中的物品，例如添加附魔、修改组件、改变物品 ID。', '在数据包中实现自定义物品升级或转换系统。', '在不替换整个物品的情况下，仅修改物品的特定属性（如食物组件）。']

## 机制原理

该技术利用了 Minecraft 1.17 引入的 /item 命令及其 modify 子命令。item modify 命令可以直接对指定实体或方块槽位中的物品应用 item_modifier（物品修饰器），而无需将物品复制到中间容器。item_modifier 是一个 JSON 文件，定义了对物品的修改操作，例如设置组件、添加附魔、改变物品 ID 等。在 1.20.5 版本中，item_modifier 的功能得到了扩展，支持通过 filtered 函数进行条件过滤，以及通过 set_item 函数改变物品 ID 而不影响其他组件。对于 1.16 及以下版本，由于无法直接修改玩家物品，需要使用一个技巧：通过自定义潜影盒的战利品表，使得当使用特定物品（minecraft:air{drop_contents: 1b}）挖掘潜影盒时，潜影盒会掉落其内容物。然后，将玩家物品放入潜影盒，再使用 loot replace 命令模拟挖掘，将物品直接放入玩家物品栏。

## 注意事项

- 1.17+ 的 item replace 方法在不使用数据包的情况下，每个游戏刻只能处理一个物品。
- 1.16 及以下版本的方法需要放置潜影盒，建议放置在常加载区块中，以避免不断设置方块。
- 1.16 及以下版本的方法依赖于自定义潜影盒战利品表，社区已建立标准（黄色潜影盒），建议使用以避免冲突。
- 1.20.5+ 的 set_item 函数在改变物品 ID 时，某些不兼容的组件（如 max_stack_size 和 max_damage）可能会被自动调整。
- 1.15 版本修复了 MC-123307，导致无法直接使用 data modify 和 execute store 修改玩家物品栏。
