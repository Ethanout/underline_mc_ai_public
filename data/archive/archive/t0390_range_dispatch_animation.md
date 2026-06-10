---
id: t0390
title: "映射装弹动画"
title_en: "range_dispatch_animation"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202511/6/content"
source_type: "feature_article"
source_issue: "202511"
version_min: "1.21.4"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["resource_pack", "model_mapping", "animation", "crossbow", "range_dispatch"]
verified_in_game: false
---

## 核心洞见

利用物品模型映射的 range_dispatch 机制，通过 crossbow/pull 数值属性在装填过程中的连续变化，驱动多个预定义模型按阈值切换，实现无需数据包或模组的资源包动画。

## 代码示例

```mcfunction
{
  "type": "minecraft:range_dispatch",
  "entries": [
    {
      "threshold": 0.004,
      "model": {
        "type": "model",
        "model": "weapons:item/gun/display/gun_1"
      }
    },
    ...此处省略代码
    {
      "threshold": 1.000,
      "model": {
        "type": "model",
        "model": "weapons:item/gun/display/gun_250"
      }
    }
  ],
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术基于 Minecraft 1.21.4 引入的 range_dispatch 物品模型映射类型。其核心机制是：游戏每帧（实际每刻更新）计算物品堆叠的指定数值属性（如 crossbow/pull），该属性在弩装填过程中从 0 线性增长到 1。range_dispatch 按 entries 中 threshold 从小到大排序，找到第一个大于等于当前数值的阈值，并应用对应的模型。若数值小于所有阈值，则使用 fallback 模型。因此，通过定义一系列阈值（如 0.004, 0.008, ..., 1.000）并关联不同阶段的模型（如 gun_1, gun_2, ..., gun_250），即可在装填过程中平滑切换模型，形成动画效果。关键推导：crossbow/pull 的计算逻辑为 useDuration / chargeDuration，其中 useDuration 是剩余使用时间，chargeDuration 是总装填时间，因此该值在装填过程中从 0 递增到 1。与朴素实现（每帧手动更新模型）相比，此技术完全依赖游戏内置机制，无需额外代码，但受限于游戏刻更新频率（20 tick/s），动画帧率上限为 20 FPS。

## 注意事项

- 两个关键帧模型之间的结构必须一致，否则插值生成中间模型时可能出错
- 动画帧率受限于游戏刻更新频率（20 tick/s），无法达到更高帧率
- crossbow/pull 仅在弩装填时有效，且需要物品堆叠具有 charged_projectiles 组件且实体存在，否则返回 0
- 常见误解：开发者通常认为装弹动画必须通过数据包修改实体模型或使用模组实现，而不知道仅靠资源包中的模型映射文件即可完成。
