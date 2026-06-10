---
id: t0522
title: "收纳袋批量投递物品列表"
title_en: "bundle_contents_bulk_item_delivery"
layer: technique
source_url: "manual:pasted-text.txt"
source_type: manual
version_min: "1.21.2"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["bundle_contents", "item_entity", "macro", "storage", "inventory"]
verified_in_game: false
---

## 核心洞见

收纳袋的 `bundle_contents` 组件可以直接接收物品列表。把该列表写入一个低生命值、着火的收纳袋物品实体，可让实体立即销毁并一次性释放列表中的全部物品，绕过逐项遍历。

## 代码示例

```mcfunction
$summon minecraft:item ~ ~ ~ {Item:{id:bundle,components:{bundle_contents:$(storage_list)}},Fire:200,Health:1}
```

## 机制原理

与容器物品不同，`bundle_contents` 接受不带槽位号的物品堆列表，因此 storage 中的列表可以直接宏替换进去。物品实体死亡时，收纳袋内容会释放为独立物品实体；低 `Health` 配合 `Fire` 让收纳袋本体在玩家捡起前销毁。

## 使用场景

- 将大型 storage 物品列表交付给附近玩家
- 调试时快速物化动态生成的物品列表

## 注意事项

- 该方法会在世界中生成大量物品实体，并不保证全部进入指定玩家背包。
- 附近其他玩家或漏斗也可能捡取物品。
- 必须测试物品实体上限、堆叠行为和服务器性能。

