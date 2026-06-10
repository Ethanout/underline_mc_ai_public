---
id: t0487
title: "地板合成NBT"
title_en: "floor_crafting_with_nbt"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/customcrafting"
source_type: "mcc_wiki"
source_issue: "questions/customcrafting"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["custom_crafting", "item_detection", "floor_crafting", "nbt"]
verified_in_game: false
---

## 核心洞见

利用物品实体Age标签和store success机制，在地面上通过检测多个带NBT的物品实体实现自定义合成。

## 代码示例

```mcfunction
# 1.13 - 1.20.4 版本示例（无动画）
# Command block / tick function
execute at @a as @e[type=item,distance=..6,nbt={OnGround:true,Item:{id:"minecraft:emerald",Count:2b,tag:{some:true}}}] at @s store success entity @s Age short 6000 store success entity @e[type=item,distance=..0.5,limit=1,nbt={OnGround:true,Item:{id:"minecraft:diamond",Count:1b,tag:{custom:true}}}] Age short 6000 store success entity @e[type=item,distance=..0.5,limit=1,nbt={OnGround:true,Item:{id:"minecraft:redstone",Count:5b,tag:{data:true}}}] Age short 6000 run summon item ~ ~ ~ {Item:{id:"minecraft:ender_eye",Count:1b,tag:{custom_result:true,display:{Name:'{"text":"Some Custom Result","italic":false}'}}}}

# 1.19.4 - 1.20.4 版本示例（含动画）
# Command blocks / tick function
execute at @a as @e[type=item,distance=..6,nbt={OnGround:true,Item:{id:"minecraft:emerald",Count:2b,tag:{some:true}}}] at @s if block ~ ~ ~ air store success entity @s Age short 6000 store success entity @e[type=item,distance=..0.5,limit=1,nbt={OnGround:true,Item:{id:"minecraft:diamond",Count:1b,tag:{custom:true}}}] Age short 6000 store success entity @e[type=item,distance=..0.5,limit=1,nbt={OnGround:true,Item:{id:"minecraft:redstone",Count:5b,tag:{data:true}}}] Age short 6000 summon area_effect_cloud store success score @s craft_anim run summon item ~ ~ ~ {Fire:20s,Item:{id:"minecraft:shulker_box",Count:1b,tag:{BlockEntityTag:{Items:[{Slot:0b,id:"minecraft:ender_eye",Count:1b,tag:{display:{Name:'{"text":"Some Custom Result","italic":false}'}}}]}}}}
execute at @e[type=area_effect_cloud,scores={craft_anim=1}] run particle minecraft:reverse_portal ~ ~.2 ~ 0 0 0 0.025 100
execute at @e[type=area_effect_cloud,scores={craft_anim=1}] run playsound minecraft:entity.evoker.prepare_wololo neutral @a

# 1.20.5+ 版本示例（含动画）
# Command blocks / tick function
execute at @a as @e[type=item,distance=..6,nbt={OnGround:true,Item:{id:"minecraft:emerald",count:2,components:{"minecraft:custom_data":{some:true}}}}] at @s if block ~ ~ ~ air store success entity @s Age short 6000 store success entity @e[type=item,distance=..0.5,limit=1,nbt={OnGround:true,Item:{id:"minecraft:diamond",count:1,components:{"minecraft:custom_data":{custom:true}}}}] Age short 6000 store success entity @e[type=item,distance=..0.5,limit=1,nbt={OnGround:true,Item:{id:"minecraft:redstone",count:5,components:{"minecraft:custom_data":{data:true}}}}] Age short 6000 summon area_effect_cloud store success score @s craft_anim run summon item ~ ~ ~ {Fire:20s,Item:{id:"minecraft:shulker_box",count:1,components:{"minecraft:container":[{slot:0,item:{id:"minecraft:ender_eye",count:1,components:{"minecraft:item_name":'{"text":"Some Custom Result"}'}}}]}}}
execute at @e[type=area_effect_cloud,scores={craft_anim=1}] run particle minecraft:reverse_portal ~ ~.2 ~ 0 0 0 0.025 100
execute at @e[type=area_effect_cloud,scores={craft_anim=1}] run playsound minecraft:entity.evoker.prepare_wololo neutral @a
```

## 文件结构

（待补充）

## 用法

将命令放入命令方块或tick函数中运行。构建完数据包/放置命令方块后，玩家将所需物品丢在地上，物品会自动被检测并消耗，生成合成结果。

## 使用场景

['需要支持NBT自定义物品作为合成原料和结果的简单合成系统', '快速原型验证，每个配方只需一个命令方块', '不适合需要精确UI交互或大量配方的场景（命令长度受限）']

## 机制原理

该技术利用`execute store success entity`链式检测多个物品实体。核心机制是：以玩家为中心选择第一个原料物品实体，然后在其位置依次检测其他原料物品（通过`distance=..0.5`限制范围）。每次`store success entity @s Age short 6000`将检测成功的结果写入该物品的Age标签，Age乘以6000会使物品立即消失（Age达到6000时物品被清除）。如果所有原料检测都成功，则执行`run`后的命令生成合成结果。动画部分使用`area_effect_cloud`存储成功分数，然后通过后续命令播放粒子和音效。使用`Fire:20s`的潜影盒作为结果容器，可以一次给予玩家多个物品，且潜影盒被火焰烧毁时会掉落其内容物。

## 注意事项

- 强烈建议所有自定义原料使用自定义标签（custom tag）来缩短命令长度并提高可读性
- 每个原料的选择器必须指定`limit=1`和`distance=..0.5`
- 建议添加`OnGround:true`检查，确保物品落地后才触发合成
- 如果使用潜影盒动画，需要检查当前方块是否为空气，防止在水中合成时潜影盒被熄灭
- 动画相关的命令必须严格放在所有配方命令之后
- 单个命令长度限制为32k字符，因此配方原料数量受此限制
- 1.20.5+版本中NBT标签被组件（components）取代，命令格式有变化
