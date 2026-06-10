---
id: t0308
title: "空间翻折减法"
title_en: "spatial_inversion_subtraction"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202603/5/content"
source_type: "feature_article"
source_issue: "202603"
version_min: "1.19.4"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["macro", "coordinate", "subtraction", "rotation", "vector"]
verified_in_game: false
---

## 核心洞见

利用 rotated 180 和 rotated 0 90 改变局部坐标方向，可以在宏中实现带负数的精确向量减法，避免宏替换负号导致的语法错误

## 代码示例

```mcfunction
# 假设 target_xyz 代表当前位置 B
# prev_xyz 代表上一帧位置 A
positioned 0.0 0.0 0.0 rotated 180 0 run function latch:follower/__tick__/run_at_owner_eyes_tp with storage latch:io temp.vars: $
execute \
positioned ~$(target_x) ~$(target_y) ~$(target_z) \
positioned ~$(target_x) ~$(target_y) ~$(target_z) \
positioned ^$(prev_x) ^ ^$(prev_z) \
rotated 0 90 positioned ^ ^ ^$(prev_y) \
run function latch:follower/tp_here
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用 Minecraft 的局部坐标系统（^ ^ ^）与视角方向绑定的特性。通过 rotated 180 0 将执行者视角水平旋转 180 度，此时局部坐标的 ^X（左）和 ^Z（前）分别对应全局坐标的 -X 和 -Z。因此执行 positioned ^$(prev_x) ^ ^$(prev_z) 时，无论 prev_x 和 prev_z 是正是负，都等价于在全局坐标中减去对应的值。

同理，rotated 0 90 将视角垂直向下 90 度，此时局部坐标的 ^Z（前）对应全局坐标的 -Y，执行 positioned ^ ^ ^$(prev_y) 即减去 prev_y。

整个流程：先通过两次 positioned ~$(target_x) ~$(target_y) ~$(target_z) 实现 2B 的叠加，然后利用空间翻折依次减去 A_x、A_z、A_y，最终得到 2B - A 的精确坐标。

与朴素实现（积分版计算）相比，该技术完全在宏层面完成向量运算，无需额外的存储和计算步骤，代码更简洁且精度更高。

## 注意事项

- 需要确保执行环境在 rotated 180 0 后没有其他旋转干扰
- rotated 0 90 后的 ^Z 方向对应全局 -Y，需要确认垂直方向的正负号约定
- 该方法依赖宏替换，需要确保 prev_x/prev_y/prev_z 变量正确传入
- 常见误解：开发者通常认为宏中无法直接做减法，因为负号与 ~ 结合会产生非法语法（如 ~--50），因此只能使用积分版或 scoreboard 计算
