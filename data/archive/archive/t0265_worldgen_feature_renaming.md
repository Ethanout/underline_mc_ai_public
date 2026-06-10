---
id: t0265
title: "世界生成特征重命名"
title_en: "worldgen_feature_renaming"
layer: technique
source_url: "https://datapack.wiki/wiki/info/breaking-changes"
source_type: "datapack_wiki"
source_issue: ""
version_min: "26.1"
version_max: ""
wiki_covers_this: true
confidence: low
tags: ["worldgen", "breaking_change", "feature", "configuration"]
verified_in_game: false
---

## 核心洞见

26.1 版本中，多个世界生成特征被重命名并增加了新的必填配置字段，旧的特征名称和配置将失效。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Mojang 在 26.1 版本中对世界生成系统进行了重构，将多个配置特征重命名并增加了新的必填字段，以提高灵活性和一致性。具体变化包括：`forest_rock` 重命名为 `block_blob`，新增必填的 `can_place_on` 方块谓词字段；`ice_spike` 重命名为 `spike`，新增必填的 `state` 方块状态提供器和 `can_place_on`、`can_replace` 方块谓词字段；`huge_red_mushroom` 和 `huge_brown_mushroom` 新增必填的 `can_place_on` 字段。`tree` 特征中，`force_dirt` 和 `dirt_provider` 参数被替换为 `below_trunk_provider` 基于规则的方块状态提供器。`disk` 特征下的 `state_provider` 现在必须是方块状态提供器，需要添加 `type: minecraft:rule_based_state_provider`。此外，`flower`、`flower_no_bonemeal` 和 `random_patch` 特征类型被移除，改用 `count` 和 `random_offset` 放置修饰符的组合。这些变化要求所有自定义世界生成的数据包必须更新特征定义。

## 注意事项

- 使用旧特征名称（如 `forest_rock`）会导致世界生成失败
- 未添加新的必填字段（如 `can_place_on`）会导致特征无法生成
- `tree` 特征中未将 `force_dirt` 替换为 `below_trunk_provider` 会导致配置错误
- `disk` 特征中未将 `state_provider` 改为基于规则的提供器会导致解析错误
- 使用已移除的 `flower` 等特征类型需要迁移到新的放置修饰符系统
- 常见误解：开发者可能认为 `forest_rock`、`ice_spike` 等特征名称在新版本中仍然有效，或者认为这些特征的配置字段是可选的。
