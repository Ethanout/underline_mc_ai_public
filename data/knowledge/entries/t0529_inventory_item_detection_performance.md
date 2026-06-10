---
id: t0529
title: "背包物品检测性能取舍"
title_en: "inventory_item_detection_performance"
layer: concept
source_url: "manual:pasted-text.txt"
source_type: manual
version_min: "1.20.5"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["performance", "execute_if_items", "clear", "inventory", "benchmark"]
verified_in_game: false
---

## 核心洞见

检测玩家背包是否存在某物品时，逐槽位 `execute if items` 与 `clear <item> 0` 总体性能接近，但两者的最坏情况不同：前者在所有条件均失败时最慢，后者在 `player.crafting` 合成格存在物品时可能显著变慢。

## 来源中的测试结论

- 穷举 `execute if items` 不会修改玩家背包，安全性没有问题。
- `execute if items` 在较早命中时较快，库存为空或完全不命中时需要跑完全部判断。
- `clear 0` 在常规情况下性能稳定，通常略快。
- 当玩家合成格中存在物品时，来源观察到 `clear 0` 消耗可能接近增加十倍。

## 使用建议

- 目标通常容易命中，且可以按命中概率排列槽位时，可选择 `execute if items`。
- 需要简洁通用检测且能接受合成格最坏情况时，可选择 `clear 0`。
- 高频检测前应使用目标服务器版本和典型背包状态重新基准测试。

