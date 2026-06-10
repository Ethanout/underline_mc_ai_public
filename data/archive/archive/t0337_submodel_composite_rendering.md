---
id: t0337
title: "子模型复合渲染"
title_en: "submodel_composite_rendering"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202509/2/content"
source_type: "feature_article"
source_issue: "202509"
version_min: "1.19.4"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["display_entity", "submodel", "composite_rendering", "transformation"]
verified_in_game: false
---

## 核心洞见

通过展示实体的父子层级和旋转变换，绕过单轴旋转限制实现复杂模型动画。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Minecraft 1.19.4+ 的展示实体（item_display）支持完整的变换矩阵（transformation），包括平移、旋转、缩放。NatureCraft 的复合模型（submodels）允许将一个复杂模型拆解为多个子模型，每个子模型作为独立的展示实体，通过`common`字段设置各自的变换属性（如旋转轴、角度、位置偏移）。这些子模型可以挂载到主模型上，形成层级结构。由于每个子模型可以独立进行任意轴旋转，组合起来就能实现多轴复合旋转效果，例如机械臂的关节运动。这与朴素实现（使用单个模型文件）不同，后者受限于模型格式（如Blockbench）的单轴旋转限制。通过实体层级变换，实际上实现了类似骨骼动画的效果。

## 注意事项

- 子模型过多可能导致实体数量激增，影响性能
- 子模型之间的变换需要精确计算偏移量，否则会出现视觉错位
- 复合模型的碰撞箱和交互箱需要手动协调，不会自动合并
- 常见误解：开发者认为原版展示实体只能进行单轴旋转，无法实现多轴复合旋转或复杂动画效果。
