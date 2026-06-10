---
id: t0347
title: "静体冻结优化"
title_en: "static_entity_optimization"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202510/0/content"
source_type: "feature_article"
source_issue: "202510"
version_min: "1.19.4"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["性能优化", "实体冻结", "运动学", "火焰图"]
verified_in_game: false
---

## 核心洞见

通过检测并冻结静止的展示实体，可以大幅减少不必要的计算开销，提升性能。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术通过检测实体的位置和旋转变化来判断是否静止。当实体在连续多个tick内没有发生任何变化时，将其标记为'冻结'状态，跳过运动学、碰撞检测等计算。只有当外部输入（如遥控指令）或物理事件（如碰撞）发生时，才解除冻结。这种优化基于Minecraft的实体更新机制：被冻结的实体不会触发运动学计算，但保留其NBT数据。通过火焰图验证，这种优化可以显著降低CPU占用，特别是在大量静态设备（如固定机枪、红石灯）的场景中。

## 注意事项

- 冻结判断的阈值需要精心调整，避免误判微动实体
- 冻结实体在解除冻结时需要正确恢复所有状态
- 某些物理效果（如重力）在冻结期间需要特殊处理
- 常见误解：开发者通常对所有实体每tick都进行完整的运动学计算，即使实体已经静止不动，造成性能浪费。
