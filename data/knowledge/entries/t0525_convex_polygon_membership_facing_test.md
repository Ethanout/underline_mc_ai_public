---
id: t0525
title: "朝向检测凸多边形包含关系"
title_en: "convex_polygon_membership_facing_test"
layer: technique
source_url: "manual:pasted-text.txt"
source_type: manual
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["geometry", "convex_polygon", "facing", "local_coordinates", "selector"]
verified_in_game: false
---

## 核心洞见

当一组实体按凸多边形边界正确布置和朝向时，可以从每个边界实体朝目标点建立局部坐标，再用固定距离投影与最近实体检测判断目标是否位于任一边界外侧。

## 代码示例

```mcfunction
at @e facing entity @s feet positioned ^ ^ ^1024.0001 unless entity @e[distance=..1024,limit=1] run return run say 在多边形外
say 在多边形内
```

## 机制原理

该命令让执行上下文依次位于边界实体，朝向待测实体，并沿局部前方向投影约 1024 格。若投影位置附近找不到边界实体，则认为目标跨过了某条边界。所有边界检查均未提前返回时，目标被视为位于凸多边形内。

## 注意事项

- 来源没有说明边界实体必须如何排列、朝向或标记，直接对任意 `@e` 使用会得到错误结果。
- 固定距离 `1024.0001` 隐含尺寸限制和浮点误差假设。
- 仅应视为待验证的几何技巧，不适用于凹多边形。

