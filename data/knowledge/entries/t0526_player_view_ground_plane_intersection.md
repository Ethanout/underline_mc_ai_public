---
id: t0526
title: "玩家视线与水平面交点"
title_en: "player_view_ground_plane_intersection"
layer: technique
source_url: "manual:pasted-text.txt"
source_type: manual
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["ray", "plane_intersection", "local_coordinates", "execution_context"]
verified_in_game: false
---

## 核心洞见

通过连续改写命令执行上下文的位置、朝向和局部坐标，可以不使用显式算术，近似求出玩家视线与 `y=0` 水平面的交点。

## 代码示例

```mcfunction
execute as @a at @s positioned 0 0 0 positioned ^ ^ ^-1056 rotated ~180 ~ positioned ^ ^ ^992 facing 0 0 0 positioned as @s positioned ^ ^32768 ^ positioned ~ 0 ~ facing entity @s eyes positioned as @s positioned ^ ^1024 ^ positioned ~ 0 ~ run particle minecraft:end_rod ~ ~ ~ 0 0 0 0 0 force
```

## 机制原理

命令利用局部坐标投影和多次 `facing` 构造与玩家视线相关的相似三角形，再把中间位置压到 `y=0`，最终将执行位置移动到交点附近。

## 注意事项

- 该单行命令缺少推导说明，目前只能作为待验证技巧保存。
- 玩家视线平行于水平面、朝上或交点极远时可能失效。
- 常数 `1056`、`992`、`32768`、`1024` 的精度和距离范围需要测试。

