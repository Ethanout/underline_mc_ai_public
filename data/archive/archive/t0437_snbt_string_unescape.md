---
id: t0437
title: "SNBT字符串反转义"
title_en: "snbt_string_unescape"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202507/3/content"
source_type: "feature_article"
source_issue: "202507"
version_min: "1.21.6"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["SNBT", "字符串处理", "宏", "转义字符", "对话框"]
verified_in_game: false
---

## 核心洞见

通过将字符串拆分为字符列表并计算转义次数，可以在宏拼接中正确处理转义字符

## 代码示例

```mcfunction
# 将用户输入存入字符串
data modify storage foo:bar input set value {input:"$(input)"}

# 拆分为字符列表（简化示例）
# 实际需要遍历每个字符
data modify storage foo:bar chars set value []
# ... 使用data string逐个字符拆分

# 拼接时处理转义
# function dnt:private/concat/get_slash/loop
$data modify storage dnt:ram concat.escape set value "$(escape)$(escape)$(escape)$(escape)\\"
scoreboard players remove $slash_count calc.dnt 1
execute if score $slash_count calc.dnt matches 1.. run function dnt:private/concat/get_slash/loop with storage dnt:ram concat
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

1.21.6-pre2后对话框输入会对特殊字符转义（' → \', " → \", \ → \\, 换行 → \n），导致无法直接通过`data merge`接受用户输入的SNBT。解决方案：先将输入存入字符串字段，然后通过字符拆分和重新拼接来去除不需要的转义（如\n）。关键技巧：将字符串拆分为字符列表后，对每个需要转义的字符（'、"、\）计算需要添加的反斜线数量。由于宏每次执行只能添加一层转义，需要多次迭代。通过`$slash_count`记录剩余转义次数，循环执行直到所有转义完成。最终拼接时，每个特殊字符前添加正确数量的反斜线，得到合法的SNBT字符串。

## 注意事项

- 需要正确处理所有转义字符的组合情况
- 宏嵌套次数有限，需要合理设计循环次数
- 不同版本转义规则可能变化，需测试兼容性
- 常见误解：开发者可能认为直接使用宏拼接字符串可以处理任意SNBT输入，但转义字符会导致语法错误
