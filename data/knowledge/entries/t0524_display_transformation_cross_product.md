---
id: t0524
title: "展示实体变换分解计算叉乘"
title_en: "display_transformation_cross_product"
layer: technique
source_url: "manual:pasted-text.txt"
source_type: manual
version_min: "1.19.4"
version_max: ""
wiki_covers_this: false
confidence: high
tags: ["display_entity", "matrix", "cross_product", "transformation", "quaternion"]
verified_in_game: false
---

## 核心洞见

把两个三维向量作为展示实体变换矩阵的前两列，利用游戏对 transformation 矩阵的分解结果，可以从 `left_rotation` 与 `scale` 间接恢复叉积方向和大小。

## 代码示例

```mcfunction
data modify storage io transformation set value [0f,0f,0f,0f, 0f,0f,0f,0f, 0f,0f,0f,0f, 0f,0f,0f,1f]
data modify storage io transformation[0] set from storage io vec[0]
data modify storage io transformation[4] set from storage io vec[1]
data modify storage io transformation[8] set from storage io vec[2]
data modify storage io transformation[1] set from storage io ivec[0]
data modify storage io transformation[5] set from storage io ivec[1]
data modify storage io transformation[9] set from storage io ivec[2]
data modify entity @s transformation set from storage io transformation
data modify storage io transformation set from entity @s transformation
execute store result score #s0 num run data get storage io transformation.scale[0] 1000
execute store result score #s1 num run data get storage io transformation.scale[1] 1000
scoreboard players operation #s0 num *= #s1 num
...
```

读取分解后的 `left_rotation` 记为四元数 `q`，`scale` 记为 `s`：

```text
叉积方向的一个分量表达式：1 - 2 * (qx² + qy²)
叉积大小：s[0] * s[1]
```

## 机制原理

展示实体会把输入矩阵分解为平移、左右旋转和缩放。前两列描述的平面朝向与面积分别对应叉积方向和模长，因此可以借用原版矩阵分解完成部分向量计算。

## 注意事项

- 来源只给出核心关系，没有完整命令和三个方向分量的恢复公式。
- 零向量、平行向量、负缩放与矩阵分解符号选择可能产生异常。
- 必须游戏内验证后才能作为通用叉积实现。

