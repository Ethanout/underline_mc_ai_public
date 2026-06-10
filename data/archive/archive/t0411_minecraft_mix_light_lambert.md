---
id: t0411
title: "Lambert光照混合"
title_en: "minecraft_mix_light_lambert"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202511/2/content"
source_type: "feature_article"
source_issue: "202511"
version_min: "1.21.8"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["core_shader", "lighting", "lambert", "entity"]
verified_in_game: false
---

## 核心洞见

Minecraft使用简化的Lambert漫反射模型，通过两束定向光和环境光混合计算实体光照，且光照强度被钳制在[0,1]导致无高光。

## 代码示例

```mcfunction
glsl
vec4 minecraft_mix_light(vec3 lightDir0, vec3 lightDir1, vec3 normal, vec4 color) {
    float light0 = max(0.0, dot(lightDir0, normal));
    float light1 = max(0.0, dot(lightDir1, normal));
    float lightAccum = min(1.0, (light0 + light1) * MINECRAFT_LIGHT_POWER + MINECRAFT_AMBIENT_LIGHT);
    return vec4(color.rgb * lightAccum, color.a);
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

minecraft_mix_light函数基于Lambert余弦定律：漫反射强度与光线方向和法线夹角的余弦成正比。通过dot(lightDir, normal)计算余弦值（输入为单位向量）。游戏使用两束定向光（Light0_Direction和Light1_Direction）模拟环境照明，加上环境光MINECRAFT_AMBIENT_LIGHT。最终光照强度为(light0+light1)*MINECRAFT_LIGHT_POWER + MINECRAFT_AMBIENT_LIGHT，并钳制到[0,1]。由于没有镜面反射项，且强度上限为1.0，渲染结果不会比纹理原始颜色更亮。

## 注意事项

- 光照强度被钳制在1.0，无法表现高光或过亮效果
- 仅使用两束定向光，无法模拟复杂环境光照
- 法线必须为单位向量，否则点乘结果不表示余弦值
- 常见误解：开发者可能认为Minecraft使用复杂的光照模型（如Phong或Blinn-Phong），或认为光照强度可以超过1.0产生高光。
