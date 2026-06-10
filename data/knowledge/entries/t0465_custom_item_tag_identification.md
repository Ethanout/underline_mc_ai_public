---
id: t0465
title: "物品自定义标签"
title_en: "custom_item_tag_identification"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/customitemtag"
source_type: "mcc_wiki"
source_issue: "questions/customitemtag"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["item", "nbt", "custom_data", "identification", "detection"]
verified_in_game: false
---

## 核心洞见

利用物品的 tag 或 custom_data 组件存储任意 NBT 数据，实现物品的持久化标识与检测。

## 代码示例

```mcfunction
# 1.20.5 and above
give @s minecraft:stick[minecraft:custom_data={my_custom_tag:true}]

# 1.20.4 and below
give @s minecraft:stick{my_custom_tag:true}

# 1.20.5 and above
summon item ~ ~ ~ {Item:{id:"minecraft:stick",components:{"minecraft:custom_data":{my_custom_tag:true}}}}

# 1.20.4 and below
summon item ~ ~ ~ {Item:{id:"minecraft:stick",Count:1b,tag:{my_custom_tag:true}}}

# 1.20.5 and above
@a[nbt={Inventory:[{components:{"minecraft:custom_data":{my_custom_tag:true}}}]}]

# 1.20.4 and below
@a[nbt={Inventory:[{tag:{my_custom_tag:true}}]}]

# 1.20.5 and above
execute as @e[type=item] if items entity @s contents *[custom_data~{my_custom_tag:true}]
execute if entity @e[type=item,nbt={Item:{components:{"minecraft:custom_data":{my_custom_tag:true}}}}]

# 1.20.4 and below
execute if entity @e[type=item,nbt={Item:{tag:{my_custom_tag:true}}}]
```

## 文件结构

（待补充）

## 用法

直接在命令中执行 give/summon 命令即可创建带自定义标签的物品；使用 @a[nbt=...] 或 execute if entity 等命令检测物品。无需额外数据包文件。

## 使用场景

['检测玩家是否头戴特定自定义物品（如任务道具）', '区分同种物品的不同变体（如不同功能的木棍）', '在掉落物中筛选特定标识的物品（如自定义掉落物）']

## 机制原理

Minecraft 在 1.20.4 及以下版本中，物品的 tag 标签可以存储任意 NBT 数据，且游戏不会自动移除未知数据。1.20.5 及以上版本引入了组件系统，使用 minecraft:custom_data 组件替代了 tag 标签，同样可以存储任意自定义数据。这使得开发者可以在物品上附加自定义标识（如 my_custom_tag:true），然后通过 NBT 检测（@a[nbt=...]）或物品组件检测（if items entity ...）来识别这些物品。关键点在于：物品的 tag/custom_data 是持久化的，不会因物品移动、堆叠或存储而丢失，且与实体上的 scoreboard tag 不同，它属于物品本身而非容器实体。

## 注意事项

- 1.20.5 及以上版本必须使用 minecraft:custom_data 组件，旧版 tag 语法不再有效
- 通过 loot table 或 recipe 设置自定义数据时，注意 JSON 到 NBT 的隐式类型转换（如整数可能被转为 byte/short）
- Bedrock 版不支持自定义 NBT 标签，需使用物品数据值或颜色代码作为替代方案
- scoreboard tag（如 @e[tag=blah]）属于掉落物实体，不属于物品本身，不能用于检测物品栏中的物品
