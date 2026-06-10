---
id: t0258
title: "局部方向速度"
title_en: "local_direction_velocity"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202605/5/content"
source_type: "feature_article"
source_issue: "202605"
version_min: "1.21.11"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["motion", "velocity", "local-coordinates", "execute", "scoreboard"]
verified_in_game: false
---

## 核心洞见

通过执行朝向和整数缩放，可以在数据包中精确控制玩家局部坐标系下的速度向量。

## 代码示例

```mcfunction
function motion:apply_arguments
# 假设传入 {x:100, y:100, z:100}
# 内部实现（伪代码，实际为多个命令）：
execute store result entity @s Motion[0] double 0.001 run data get storage motion:input x
execute store result entity @s Motion[1] double 0.001 run data get storage motion:input y
execute store result entity @s Motion[2] double 0.001 run data get storage motion:input z

function motion:apply_scoreboard
# 内部实现（伪代码）：
execute store result entity @s Motion[0] double 0.001 run scoreboard players get @s motion.x
execute store result entity @s Motion[1] double 0.001 run scoreboard players get @s motion.y
execute store result entity @s Motion[2] double 0.001 run scoreboard players get @s motion.z
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用 Minecraft 的 `execute` 命令的 `at` 和 `rotated` 子命令来设置执行朝向，然后通过函数参数或计分板传入速度大小。速度大小以整数形式传入（实际速度的1000倍），在数据包内部通过 `data modify` 或 `execute store` 将整数除以1000后写入 Motion 标签。由于执行朝向决定了局部坐标轴（正左、正上、正前）与世界坐标轴的对应关系，因此可以实现任意朝向下的速度赋予。误差（-0.001~0.001）源于整数除法或浮点数精度。与朴素实现（直接设置 Motion 标签）相比，该技术将速度方向与玩家朝向绑定，无需手动计算旋转矩阵。

## 注意事项

- 速度大小必须为整数且为实际速度的1000倍，否则精度损失或溢出
- 三个方向的速度大小都不可省略，若不需要需设为0
- 执行朝向必须正确设置，否则速度方向错误
- 误差范围在-0.001~0.001，对高精度需求场景可能不适用
- 常见误解：开发者通常认为只能通过直接修改 Motion NBT 标签来设置速度，且难以将速度与玩家朝向解耦。
