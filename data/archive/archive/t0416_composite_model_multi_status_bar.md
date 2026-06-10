---
id: t0416
title: "复合模型状态栏"
title_en: "composite_model_multi_status_bar"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202504/6/content"
source_type: "feature_article"
source_issue: "202504"
version_min: "1.21.4"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["物品模型", "composite", "custom_model_data", "状态栏", "1.21.4"]
verified_in_game: false
---

## 核心洞见

利用 1.21.4 的 composite 模型映射和复合 custom_model_data，可以将多个独立状态值分别映射到不同子模型，无需合并计算或穷举组合。

## 代码示例

```mcfunction
{
  "model": {
    "type": "composite",
    "models": [
      {
        "type": "range_dispatch",
        "property": "custom_model_data",
        "index": 0,
        "entries": [
          { "model": { "type": "model", "model": "shard:item/energy/1" }, "threshold": 5 },
          { "model": { "type": "model", "model": "shard:item/energy/activate" }, "threshold": 160 }
        ],
        "fallback": { "type": "model", "model": "shard:item/energy/0" }
      },
      {
        "type": "range_dispatch",
        "property": "custom_model_data",
        "index": 2,
        "entries": [
          { "model": { "type": "model", "model": "shard:item/rage/1" }, "threshold": 2.5 },
          { "model": { "type": "model", "model": "shard:item/rage/16" }, "threshold": 40 }
        ],
        "fallback": { "type": "model", "model": "shard:item/rage/0" }
      },
      {
        "type": "range_dispatch",
        "property": "custom_model_data",
        "index": 1,
        "entries": [
          { "model": { "type": "model", "model": "shard:item/score/1" }, "threshold": 1 },
          { "model": { "type": "model", "model": "shard:item/score/5" }, "threshold": 5 }
        ],
        "fallback": { "type": "model", "model": "shard:item/score/0" }
      }
    ]
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

1.21.4 中 custom_model_data 从单一整数变为复合标签，包含 flags（布尔列表）、floats（浮点列表）、strings（字符串列表）。物品模型映射的 range_dispatch、condition、select 类型分别对应这些列表，通过 index 指定使用列表中的第几项。composite 模型类型可以将多个子模型（如多个 range_dispatch）叠加渲染，每个子模型独立响应自己的 cmd 索引。因此，三个计分板值可以分别写入 floats 列表的三个位置，每个 range_dispatch 只关注自己的索引，互不干扰。数据包侧使用 set_custom_model_data 函数（战利品表修饰）直接按 score 填充对应列表项，无需函数计算合并。hand_animation_on_swap 字段可禁用副手物品切换动画。

## 注意事项

- composite 模型中的子模型是叠加渲染，如果子模型有重叠区域且不透明，会遮挡后面的模型，需要设计为半透明或错开位置
- range_dispatch 的 threshold 是浮点数比较，注意计分板整数转浮点后的精度问题
- index 从 0 开始计数，必须与 set_custom_model_data 中 values 列表的顺序严格对应
- 常见误解：开发者通常认为多个状态值必须合并为一个整数 cmd，或需要为每种组合预绘制模型，导致工作量爆炸。
