---
id: t0521
title: "数字提供器浮点求和"
title_en: "number_provider_float_sum"
layer: technique
source_url: "manual:pasted-text.txt"
source_type: manual
version_min: "26.1"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["number_provider", "float", "sum", "item_modifier", "storage"]
verified_in_game: false
---

## 核心洞见

26.1+ 的 `sum` 数字提供器可以直接对多个值执行单精度浮点求和，并借助 `custom_model_data.floats` 将结果写入物品后取回 storage，不需要实体传送或云高度换算。

## 代码示例

```mcfunction
# fsum.mcfunction
$item modify block 0 0 0 container.0 {function:"minecraft:set_custom_model_data",floats:{values:[{type:"minecraft:sum",summands:$(in)}],mode:"replace_all"}}
data modify storage fadd out set from block 0 0 0 Items[0].components."minecraft:custom_model_data".floats[0]

# 调用后 out 为约 2.0413f
function fsum {in:[3.1415f,-2.7182f,1.6180f]}
```

## 机制原理

`sum` 提供器在物品修饰器求值期间完成加法，输入会统一转换为 float。结果写进物品的 `custom_model_data.floats`，再由数据命令提取。它支持一次对任意数量的输入求和，并覆盖完整的 float 范围。

## 性能信息

来源中的基准测试每 tick 重复 3000 次操作，报告平均 tick 耗时：baseline 5ms、scoreboard 6ms、数字提供器求和 13ms、云计算 23ms、实体传送 34ms。该结果仅代表测试环境，应重新基准测试后再用于容量规划。

## 注意事项

- 宏参数很方便，但宏展开有额外开销；固定输入位置时可改用 storage 数字提供器。
- 异构数值列表会先转换为 float，可能损失整数或 double 精度。
- 示例依赖一个始终存在且可控的容器及其中的占位物品。

