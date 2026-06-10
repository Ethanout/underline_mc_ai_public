---
id: t0358
title: "方块坐标取整"
title_en: "block_pos_floor_behavior"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202510/4/content"
source_type: "feature_article"
source_issue: "202510"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["坐标系统", "方块坐标", "向下取整", "相对坐标", "局部坐标"]
verified_in_game: false
---

## 核心洞见

在方块坐标中使用相对坐标或局部坐标时，坐标值会被向下取整（向负无穷），而非四舍五入。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

方块坐标（minecraft:block_pos）要求三个整数参数。当使用相对坐标（~dx ~dy ~dz）或局部坐标（^dx ^dy ^dz）时，系统首先计算绝对坐标值，然后对每个坐标轴执行向下取整（floor），即向负无穷方向取整。例如，命令执行位置为(10.5, 70.2, -9.1)时，相对坐标~ ~ ~计算为(10.5, 70.2, -9.1)，向下取整后变为(10, 70, -10)。注意负数-9.1向下取整为-10（而非-9），这与align子命令的取整方式一致。这种取整行为确保方块坐标始终指向方块的西北下角，因为方块角点位于整数坐标。

## 注意事项

- 负数相对坐标向下取整会向更负方向，而非向零
- 方块坐标的取整发生在相对/局部坐标计算之后
- 局部坐标不能用于二维坐标参数（column_pos和vec2）
- 局部坐标不能与绝对坐标或相对坐标混用
- 常见误解：开发者可能认为在方块坐标中使用相对坐标（如~ ~ ~）会保留小数或四舍五入到最近整数，但实际上它执行向下取整。
