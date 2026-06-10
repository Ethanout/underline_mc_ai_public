---
id: t0329
title: "粒子着色器传参"
title_en: "particle_shader_parameter_passing"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202509/7/content"
source_type: "feature_article"
source_issue: "202509"
version_min: "1.20"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["shader", "particle", "parameter_passing", "data_pack", "resource_pack"]
verified_in_game: false
---

## 核心洞见

通过entity_effect粒子的颜色Alpha通道传递自定义参数到顶点着色器，实现数据包对着色器的实时控制

## 代码示例

```mcfunction
#version 150

#moj_import <minecraft:fog.glsl>
#moj_import <minecraft:dynamictransforms.glsl>
#moj_import <minecraft:projection.glsl>
#moj_import <minecraft:globals.glsl>

#define RESOLUTION_FACTOR 500

in vec3 Position;
in vec2 UV0;
in vec4 Color;
in ivec2 UV2;

uniform sampler2D Sampler2;

out float sphericalVertexDistance;
out float cylindricalVertexDistance;
out vec2 texCoord0;
out vec4 vertexColor;

const vec2 quadCorners[4] = vec2[4](
    vec2(1.0, -1.0),
    vec2(1.0, 1.0),
    vec2(-1.0, 1.0),
    vec2(-1.0, -1.0)
);

void main() {
    if (Color.a > 0.113 && Color.a < 0.115) {
        // 初始化裁剪空间位置，位于视图中心
        vec4 clipSpacePos = vec4(0.0, 0.0, -1.0, 1.0);
        // 根据当前顶点索引获取对应的角偏移量
        vec2 cornerOffset = quadCorners[gl_VertexID % 4];
        // 将角偏移量应用到xy坐标上
        clipSpacePos.xy += cornerOffset;
        // 计算用于调整投影的偏移量 (0 到 1),将 (-1,1) 映射到 (1,0)
        vec2 ndcCornerOffset = (vec2(1.0) - cornerOffset) * 0.5;
        // 计算屏幕空间的偏移 (像素单位)
        vec2 screenOffset = ndcCornerOffset / ScreenSize;
        gl_Position = ProjMat * clipSpacePos;
        gl_Position.xy = gl_Position.w * (vec2(1.0) - screenOffset * vec2(RESOLUTION_FACTOR));
    } else {
        gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);
    }
    sphericalVertexDistance = fog_spherical_distance(Position);
    cylindricalVertexDistance = fog_cylindrical_distance(Position);
    texCoord0 = UV0;
    vertexColor = Color * texelFetch(Sampler2, UV2 / 16, 0);
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用Minecraft粒子系统的固有属性传递参数：1) entity_effect粒子支持自定义RGBA颜色，其中Alpha通道在顶点着色器中可通过Color.a访问；2) 在顶点着色器中判断Color.a是否为特定值（如0.114）来区分普通粒子和参数粒子；3) 参数粒子通过修改gl_Position被重定向到屏幕角落的小区域（如500x500像素），避免影响正常渲染；4) 由于浮点精度问题，判断时需使用区间比较（如Color.a > 0.113 && Color.a < 0.115）而非精确相等；5) 粒子顶点着色器中的gl_VertexID可获取顶点索引，用于构建自定义四边形几何体。此方法绕过了Minecraft着色器系统对uniform变量的限制，利用粒子系统作为数据包和着色器之间的通信通道。

## 注意事项

- 浮点精度问题：Color.a不能直接用==判断，必须使用区间比较（如>0.113 && <0.115）
- 粒子颜色受光照影响：vertexColor = Color * texelFetch(Sampler2, UV2 / 16, 0)中的光照采样会改变颜色值
- 粒子片元着色器中的颜色混合和雾气效果会干扰参数传递
- 参数粒子渲染区域过小（如1像素）可能因精度丢失导致绘制失败
- tinted_leaves粒子的Alpha值固定为1.0，不能用于传参，必须使用entity_effect粒子
- 常见误解：开发者通常认为着色器参数只能通过uniform变量传递，需要修改渲染管线或使用复杂的数据结构
