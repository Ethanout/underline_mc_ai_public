---
id: t0328
title: "着色器管线概览"
title_en: "minecraft_shader_pipeline_overview"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202508/1/content"
source_type: "feature_article"
source_issue: "202508"
version_min: "1.17"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["shader", "rendering_pipeline", "core_shader", "post_shader"]
verified_in_game: false
---

## 核心洞见

Minecraft 着色器是资源包中控制渲染过程的程序，但受限于无法直接与数据包通信，只能通过歪门邪道实现效果。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Minecraft 的着色器分为核心着色器（Core Shader）、后处理着色器（Post Shader）和包含着色器（Include Shader）。核心着色器处理网格、纹理等数据，输出可见画面；后处理着色器处理帧缓冲，合成最终输出；包含着色器提供常量和工具函数。渲染管线包括顶点着色器（位置转换）、图元装配（连接顶点为三角形）、几何着色器（不可修改）、光栅化（离散为片元并插值属性）、片元着色器（计算颜色和深度）、测试与混合（深度测试和透明度混合）。关键限制是：顶点着色器输出坐标必须在 (-1.0, -1.0, -1.0) 到 (1.0, 1.0, 1.0) 范围内，超出部分会被剔除；片元着色器只能使用插值后的属性，无法直接访问顶点原始数据。

## 注意事项

- 着色器 API 不稳定，每几个版本就会更改，教程难以维护
- 1.21.5 后移除了着色器对象的 .json 配置文件，不同着色器对象只能使用固定的 .vsh 和 .fsh
- 1.21.2 后后处理管线定义路径从 shaders/post 变为 post_effect
- 常见误解：开发者可能认为着色器可以像普通图形程序一样自由控制输入和输出，但实际上 Minecraft 的着色器只能使用游戏预定义的输入，无法自定义数据源。
