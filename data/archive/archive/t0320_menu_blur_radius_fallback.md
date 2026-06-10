---
id: t0320
title: "模糊半径回退机制"
title_en: "menu_blur_radius_fallback"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202512/5/content"
source_type: "feature_article"
source_issue: "202512"
version_min: "1.21.10"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["着色器", "后处理", "模糊", "全局量"]
verified_in_game: false
---

## 核心洞见

box_blur后处理着色器通过判断Radius是否>=0.5来决定使用传入的Radius值还是回退到MenuBlurRadius全局量，实现菜单模糊与实体轮廓模糊的复用。

## 代码示例

```mcfunction
//box_blur 是一个后处理程序，用于创造模糊效果
#version 330
...
// This shader relies on GL_LINEAR sampling to reduce the amount of texture samples in half.
// Instead of sampling each pixel position with a step of 1 we sample between pixels with a step of 2.
// In the end we sample the last pixel with a half weight, since the amount of pixels to sample is always odd (actualRadius * 2 + 1).
void main() {
    vec2 oneTexel = 1.0 / InSize;
    vec2 sampleStep = oneTexel * BlurDir;
    vec4 blurred = vec4(0.0);
    // 当 Radius 小于 0.5 时，MenuBlurRadius 才会被使用
    // 1.21.10 中只有三个场景调用此程序：
    //     实体外轮廓（Radius 设为 2.0）
    //     蜘蛛视角（Radius 设为 7.0 和 15.0）
    //     打开菜单栏或标题界面时（Radius 设为 0.0）
    float actualRadius = Radius >= 0.5 ? round(Radius) : float(MenuBlurRadius);
    for (float a = -actualRadius + 0.5; a <= actualRadius; a += 2.0) {
        blurred += texture(InSampler, texCoord + sampleStep * a);
    }
    blurred += texture(InSampler, texCoord + sampleStep * actualRadius) / 2.0;
    fragColor = blurred / (actualRadius + 0.5);
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

box_blur后处理程序通过条件判断实现模糊半径的灵活选择：当Radius >= 0.5时使用传入的Radius值（四舍五入取整），否则使用MenuBlurRadius全局量（来自视频设置中的菜单背景模糊程度，取值为[0,10]内的整数）。在1.21.10中，该程序被三个场景调用：实体外轮廓（Radius=2.0）、蜘蛛视角（Radius=7.0和15.0）、打开菜单栏或标题界面时（Radius=0.0）。当Radius=0.0时，条件不满足，自动回退到MenuBlurRadius。着色器利用GL_LINEAR采样减少纹理采样次数，以步长2采样像素之间的位置，最后以半权重采样最后一个像素。

## 注意事项

- MenuBlurRadius仅在Radius<0.5时被使用，其他场景使用传入的Radius
- 模糊半径必须为奇数（actualRadius*2+1），步长为2的采样方式依赖此特性
- GL_LINEAR采样假设，如果纹理采样模式被改变可能导致模糊效果异常
- 常见误解：开发者可能认为MenuBlurRadius在所有模糊场景中都被使用，或认为模糊半径是固定值而非动态选择。
