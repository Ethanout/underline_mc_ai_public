---
id: t0523
title: "全背包应用物品修饰器"
title_en: "inventory_wide_item_modifier"
layer: technique
source_url: "manual:pasted-text.txt"
source_type: manual
version_min: "26.1"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["loot_table", "slot_range", "item_modifier", "inventory"]
verified_in_game: false
---

## 核心洞见

通过战利品表的 `slot_range` 读取玩家背包槽位，再使用 `/loot replace entity`，可以把同一个物品修饰器批量应用到玩家背包中的物品。

## 代码示例

```mcfunction
/loot replace entity @s container.0 loot {pools:[{rolls:1,entries:[{type:loot_table,value:"namespace:inventory"}]}],functions:[{function:set_name,name:EXAMPLE}]}
```

## 机制原理

主战利品表调用一个负责枚举背包槽位的子战利品表，并在返回物品上统一执行修饰函数。来源指出空槽位需要先插入占位物品再丢弃，否则无法按预期保持槽位映射。

## 注意事项

- 来源未附带关键的 `namespace:inventory` 战利品表，当前条目不足以直接运行。
- `/loot replace entity` 的目标槽位和返回顺序必须在 26.1 中验证。
- 空槽位、不可堆叠物品和超量返回都可能改变背包内容，验证前不要用于真实存档。

