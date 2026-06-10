---
id: t0413
title: "SVD分解变换"
title_en: "display_entity_svd_decomposition"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202505/2/content"
source_type: "feature_article"
source_issue: "202505"
version_min: "1.19.4"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["display_entity", "SVD", "decomposition", "rotation", "scale"]
verified_in_game: false
---

## 核心洞见

展示实体的 transformation 分解形式通过奇异值分解将任意线性变换拆解为两次旋转和一次缩放，使得复杂变换可以用更直观的旋转和缩放参数表示。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

对于任意 3×3 线性变换矩阵 B，奇异值分解保证存在正交矩阵 U 和 V 以及对角矩阵 Σ，使得 B = UΣV^T。其中 Σ 的对角元素是奇异值，代表缩放因子；U 和 V 是正交矩阵，代表旋转。分解形式的 transformation 字段正是利用这一数学原理：将变换分解为四个步骤——先应用 right_rotation（V^T 对应的旋转），再应用 scale（Σ 对应的缩放），然后应用 left_rotation（U 对应的旋转），最后应用 translation（平移向量 T）。计算 SVD 时，通过求解 B B^T 的特征值和特征向量得到 U 和 Σ，再通过 B^T B 或 B^{-1}UΣ 得到 V。这种分解的几何意义是：任何仿射变换都可以看作先旋转、再缩放、再旋转、最后平移的组合。

## 注意事项

- SVD 分解计算复杂，手动计算容易出错，尤其是特征值和特征向量的求解
- 分解形式中的 right_rotation 和 left_rotation 字段支持轴角式和四元数两种表示，混用可能导致数据格式错误
- 当 B 不可逆时，无法通过 B^{-1}UΣ 直接求 V，需要重新对角化 B^T B
- 常见误解：开发者可能认为展示实体的变换只能通过矩阵形式手动计算，而不知道可以使用分解形式（right_rotation、scale、left_rotation、translation）来更直观地控制旋转和缩放。
