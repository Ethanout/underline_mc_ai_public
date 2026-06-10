---
id: t0519
title: "村民自定义交易"
title_en: "villager_custom_trades"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/shop"
source_type: "mcc_wiki"
source_issue: "questions/shop"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["villager", "trading", "nbt", "shop", "no-performance-cost"]
verified_in_game: false
---

## 核心洞见

通过修改村民的 Offers NBT 数据，可以创建无限次使用的自定义交易，无需任何命令循环

## 代码示例

```mcfunction
# 1.20.5+ 版本（使用组件）
/summon villager ~ ~ ~ {Offers:{Recipes:[{rewardExp:0b,maxUses:2147483647,buy:{id:"minecraft:diamond",count:1,components:{"minecraft:custom_data":{special:true}}},buyB:{id:"minecraft:emerald",count:1,components:{"minecraft:custom_data":{special:true}}},sell:{id:"minecraft:netherite_ingot",count:1,components:{"minecraft:custom_model_data":special:true}}}]}}

# 1.20.5 以下版本（使用 NBT）
/summon villager ~ ~ ~ {Offers:{Recipes:[{rewardExp:0b,maxUses:2147483647,buy:{id:"minecraft:diamond",Count:1b,tag:{special:true}},buyB:{id:"minecraft:emerald",Count:1b,tag:{special:true}},sell:{id:"minecraft:netherite_ingot",Count:1b,tag:{special:true}}}]}}
```

## 文件结构

（待补充）

## 用法

在游戏中执行 `/summon` 命令生成带有自定义交易的村民。玩家右键点击村民即可打开交易界面进行交易。

## 使用场景

['快速搭建无需命令循环的静态商店', '需要图形化交易界面的场景（村民交易GUI）', '不适合需要动态定价、交易记录或复杂逻辑的商店（村民交易是静态的）']

## 机制原理

村民的 `Offers` NBT 数据包含 `Recipes` 列表，每个配方定义了一次交易：`buy` 和 `buyB` 是玩家需要支付的物品（最多两种），`sell` 是玩家获得的物品。通过设置 `maxUses:2147483647`（整数最大值）使交易无限次可用，`rewardExp:0b` 禁用经验奖励。村民交易是原版机制，无需任何命令循环，因此不会造成性能问题。但交易是静态的，无法动态调整价格或触发额外效果。

## 注意事项

- 村民交易需要玩家主动交互，无法强制玩家购买
- 最多只能设置两种输入物品（buy 和 buyB），复杂交易需要变通（如使用潜影盒）
- 无法直接显示成功消息（可通过其他方式变通）
- 村民绑定在特定位置，除非使用命令传送
- 两个玩家不能同时访问同一个村民的交易界面
- 推荐使用在线生成器（如 mcstacker.net）生成命令，避免手动编写错误
- 1.20.5+ 使用 `components` 字段，1.20.5 以下使用 `tag` 字段，两者不兼容
