---
id: t0344
title: "隐形物品数据槽"
title_en: "invisible_item_data_slot"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202601/b/content"
source_type: "feature_article"
source_issue: "202601"
version_min: "1.20.5"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["物品槽位", "玩家数据", "custom_data", "物品修饰器"]
verified_in_game: false
---

## 核心洞见

利用 armor.body 或 armor.saddle 槽位放置隐形物品存储玩家数据，可离线访问且支持物品修饰器操作。

## 代码示例

```mcfunction
# 在 load 函数中初始化
scoreboard objectives add data dummy

# 给予玩家数据物品（在玩家加入时）
item replace entity @s armor.body with minecraft:name_tag[custom_data~{player_data:{score:0,level:1}}]

# 检测数据
execute if items entity @s armor.body *[custom_data~{player_data:{score:{min:100}}}] run say Score >= 100

# 修改数据
item modify entity @s armor.body 1 mypack:add_score

# 物品修饰器示例（mypack:add_score）
{
  "function": "minecraft:set_custom_data",
  "tag": "{player_data:{score:$(new_score)}}"
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

1.20.5+ 版本中，armor.body 和 armor.saddle 槽位可以放置物品，且这些物品不会影响玩家外观或游戏体验。通过 item 命令放置一个带有 custom_data 组件的物品（如命名牌），可以将玩家数据编码在物品的 NBT 中。使用 if items *[custom_data~{}] 可以高效检测数据，item modify 可以修改数据。1.21.2+ 版本中，equippable 组件允许修改物品可放入的槽位，因此可以使用任意物品。这种方案的优势是：数据随玩家实体存在，玩家下线后数据自动保存；可以使用消失诅咒标记临时数据；支持物品修饰器的高级操作（如 bundle_contents 折叠）。与玩家空间方案相比，更适合存储临时或局内数据。

## 注意事项

- 需要开启死亡不掉落（keepInventory）防止数据物品丢失
- 临时数据可使用消失诅咒标记，但需注意清理
- armor.body 槽位在 1.20.5 之前不可用，需使用末影箱等替代方案
- 物品数量有限，不适合存储大量数据
- 常见误解：开发者可能认为玩家数据只能通过记分板或 NBT 存储管理，忽略了物品槽位作为数据容器的可能性。
