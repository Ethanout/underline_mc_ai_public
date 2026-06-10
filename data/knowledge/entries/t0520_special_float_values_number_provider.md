---
id: t0520
title: "数字提供器生成特殊浮点值"
title_en: "special_float_values_from_number_provider"
layer: technique
source_url: "manual:pasted-text.txt"
source_type: manual
version_min: "26.1"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["number_provider", "float", "infinity", "nan", "item_modifier"]
verified_in_game: false
---

## 核心洞见

`set_custom_model_data` 的浮点数字提供器会把双精度输入转换为单精度浮点数。超出单精度范围的 `1e39d` 和 `-1e39d` 会转换为 `Infinityf` 和 `-Infinityf`，两者相加则产生 `NaNf`。

## 代码示例

```mcfunction
setblock 0 319 0 chest{Items:[{id:egg}]}

item modify block 0 319 0 container.0 {function:set_custom_model_data,floats:{values:[1e39d,-1e39d,{type:sum,summands:[1e39d,-1e39d]}],mode:replace_all}}

data modify storage data infnan set from block 0 319 0 Items[0].components."minecraft:custom_model_data".floats
```

## 机制原理

单精度浮点数无法表示 `1e39d`，类型转换时发生溢出并得到正负无穷。IEEE 754 中，正无穷与负无穷相加的结果为 NaN。物品修饰器先把结果写入物品组件，再由 `/data modify` 提取到 storage，使原本无法直接写出的特殊数值进入数据包数据流。

## 注意事项

- 依赖 26.1+ 的数字提供器和物品组件行为。
- 特殊浮点值在后续命令中的序列化、比较与运算行为需要逐项验证。
- 示例中的固定容器坐标应替换为数据包自己的安全工作区。

