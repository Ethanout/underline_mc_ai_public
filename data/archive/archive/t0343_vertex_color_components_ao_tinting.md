---
id: t0343
title: "顶点颜色组成"
title_en: "vertex_color_components_ao_tinting"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202510/3/content"
source_type: "feature_article"
source_issue: "202510"
version_min: "1.0"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["vertex color", "ambient occlusion", "tinting", "colormap"]
verified_in_game: false
---

## 核心洞见

Minecraft的顶点颜色（Color）包含环境光遮蔽（AO）和生物群系染色（Tinting），两者通过乘法与纹理和光照结合。

## 代码示例

```mcfunction
vec4 color = texture(Sampler0, texCoord0) * vertexColor * minecraft_sample_lightmap(Sampler2, ivec2(texCoord2));
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

顶点颜色（vertexColor）在Minecraft渲染管线中由两部分组成：环境光遮蔽（AO）和染色（Tinting）。AO使方块在连接处变暗，模拟阴影；染色使草、树叶、水等方块根据生物群系改变颜色（通过采样colormap）。这些值在顶点着色器中计算并作为传递变量传入片元着色器。最终片元颜色由纹理颜色、顶点颜色和光照贴图颜色相乘得到：color = texture(Sampler0, texCoord0) * vertexColor * minecraft_sample_lightmap(Sampler2, ivec2(texCoord2))。注意：粒子dust的顶点颜色有偏移，不是精确等于指令参数。

## 注意事项

- 粒子dust的顶点颜色存在浮点数偏移，不能直接用于精确计算
- 染色仅适用于特定方块（如草、树叶），其他方块顶点颜色可能为白色
- 常见误解：开发者可能认为顶点颜色仅用于简单着色，或者忽略AO和染色对最终颜色的影响。
