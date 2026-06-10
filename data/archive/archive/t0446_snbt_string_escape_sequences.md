---
id: t0446
title: "SNBT字符串转义"
title_en: "snbt_string_escape_sequences"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202504/5/content"
source_type: "feature_article"
source_issue: "202504"
version_min: "1.21.5"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["snbt", "string", "escape-sequence", "unicode", "formatting"]
verified_in_game: false
---

## 核心洞见

SNBT字符串支持丰富的转义序列，包括Unicode、命名Unicode字符和格式字符，可在数据包中实现特殊文本效果

## 代码示例

```mcfunction
give @s stone[lore=['\u00a7a你好']]
tellraw @s '\na\nb'
tellraw @s '\N{Snowman}'
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

SNBT字符串转义序列包括：\b(退格)、\s(空格)、\t(制表符)、\n(换行)、\f(换页)、\r(回车)、\'(单引号)、\"(双引号)、\\(反斜杠)、\r(回车)、\x(2位十六进制)、\u(4位十六进制)、\U(8位十六进制)、\N{name}(命名Unicode序列)。其中\u00a7会被转义为格式字符§，可用于物品描述中的颜色代码（如§a渲染绿色）。\N{Snowman}可输出命名Unicode字符☃。字符串支持单引号和双引号两种引号方式，在一种引号内可直接使用另一种引号而无需转义。

## 注意事项

- \u00a7转义为§后需要配合后续字符才能实现颜色效果，单独使用无效
- 命名Unicode序列的名称必须满足正则表达式[-a-zA-Z0-9 ]+，否则无效
- 在tellraw等命令中使用未加引号的中文字符串会导致解析错误
- 常见误解：开发者可能认为SNBT字符串只支持基本的转义如\n和\"，或者认为Unicode只能通过\uXXXX形式输入
