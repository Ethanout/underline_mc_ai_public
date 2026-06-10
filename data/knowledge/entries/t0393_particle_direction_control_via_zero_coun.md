---
id: t0393
title: "零数量定向粒子"
title_en: "particle_direction_control_via_zero_count"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202511/5/content"
source_type: "feature_article"
source_issue: "202511"
version_min: "1.12.2"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["particle", "direction control", "zero count", "execute positioned", "local coordinates"]
verified_in_game: false
---

## 核心洞见

将 /particle 的 count 设为 0 时，粒子的运动方向由 delta 参数决定，且方向始终从世界原点 (0,0,0) 指向 delta 坐标，与粒子生成位置无关。

## 代码示例

```mcfunction
execute at @p positioned ^ ^ ^100000000 run particle minecraft:cloud ^ ^-1 ^-100000000 ^ ^ ^ 0.0000000099 0 force
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

当 /particle 指令的 count 参数设为 0 时，游戏会生成一个粒子，但其运动行为与 count>0 时完全不同。此时 delta 参数不再表示扩散范围的标准差，而是被直接解释为粒子的初始动量方向向量。关键的非直觉行为是：这个方向向量始终以世界原点 (0,0,0) 为基准，即粒子的运动方向是从 (0,0,0) 指向 delta 坐标的方向，与粒子实际生成位置 pos 无关。例如，在 (5,0,5) 处生成粒子，delta 设为 (0,1,0)，粒子会垂直向上运动，而不是从 (5,0,5) 向 (5,1,5) 运动。

为了实现对任意位置粒子的方向控制，可以利用 execute positioned 将指令执行点移动到极远处（如 ^ ^ ^100000000），这样世界原点与实体位置相对于执行点而言几乎重合。然后通过将 pos 设置为与 positioned 相反的偏移（如 ^ ^-1 ^-100000000），使粒子生成在实体附近。同时，delta 使用局部坐标 ^ ^ ^ 表示相对方向，speed 设为极小值（如 0.0000000099）以抵消 delta 中巨大数值带来的速度影响。这样就能让粒子从实体位置向任意指定方向稳定运动。

## 注意事项

- count=0 时粒子方向始终以世界原点为基准，与 pos 无关，不能直接使用 ~ 或 ^ 相对坐标控制方向
- speed 参数会乘以 delta 的模长作为最终速度，当 delta 数值很大时需用极小的 speed 抵消
- 该机制在 1.12.2 及最新快照 25w45a 中均有效，但未来版本可能改变
- 常见误解：开发者通常认为 /particle 只能生成随机弥散的粒子，或认为 count=0 时粒子会从生成位置向 delta 方向移动（如 wiki 所述）。
