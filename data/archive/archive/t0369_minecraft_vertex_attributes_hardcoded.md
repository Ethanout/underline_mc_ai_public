---
id: t0369
title: "顶点属性硬编码"
title_en: "minecraft_vertex_attributes_hardcoded"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202509/3/content"
source_type: "feature_article"
source_issue: "202509"
version_min: "1.21.4"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["shader", "vertex-attributes", "hardcoded", "resource-pack-limitation"]
verified_in_game: false
---

## 核心洞见

Minecraft着色器的顶点属性（Position、Color、UV、UV2、Normal、Padding）是硬编码的，资源包无法额外获取其他顶点属性，且UV坐标是纹理图集坐标而非模型文件定义的原始UV。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Minecraft的顶点着色器只能接收6种预定义的顶点属性：Position（顶点位置，坐标系因对象类型而异）、Color（顶点颜色，包含自动上色和光照信息）、UV/UV0（纹理坐标，但经过图集化处理，是纹理在assets/minecraft/atlases定义的纹理图集中的UV坐标，而非模型文件中的原始UV）、UV2（亮度纹理坐标，范围0-256而非归一化的0-1，横坐标代表方块亮度，纵坐标代表天空亮度）、Normal（单位法向量）、Padding（占位符，仅用于对齐）。这些顶点属性是游戏引擎硬编码的，无法在资源包中新增或修改。这一限制意味着着色器开发者只能利用现有属性进行变换和计算，无法像某些现代渲染引擎那样自由定义顶点属性布局。

## 注意事项

- UV/UV0不是模型文件中的原始UV，而是纹理图集化后的坐标，直接使用会导致纹理映射错误
- UV2的范围是0-256而非0-1，使用时需要手动归一化或进行范围转换
- Padding属性仅用于数据对齐，不包含有效数据，不应在着色器逻辑中使用
- 常见误解：开发者可能认为可以通过资源包自定义新的顶点属性传入着色器，或者认为UV坐标直接对应模型文件中的纹理坐标。
