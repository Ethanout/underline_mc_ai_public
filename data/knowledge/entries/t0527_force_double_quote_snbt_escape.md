---
id: t0527
title: "强制生成双引号转义字符串"
title_en: "force_double_quote_snbt_escape"
layer: technique
source_url: "manual:pasted-text.txt"
source_type: manual
version_min: "26.1"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["snbt", "string", "escaping", "text_component", "macro"]
verified_in_game: false
---

## 核心洞见

26.1 中解析“引用字符串的 NBT 文本组件”会把包裹引号和字符串正文拆进 `extra` 数组。通过先人为插入单引号、再次解析并移除首字符，可以强制得到采用双引号规则转义的字符串。

## 处理流程

```text
原始字符串：
'John "Johnny" Smith'

第一次解析：
{text:"",extra:["'",'John "Johnny" Smith',"'"]}

宏重写 extra[1]，在开头插入单引号：
'\'$(contents)'

第二次解析：
{text:"",extra:['"',"'John \\\"Johnny\\\" Smith",'"']}

提取 extra[1] 并切掉首字符：
'John \\"Johnny\\" Smith'
```

## 机制原理

游戏会根据字符串中首先需要转义的引号选择 SNBT 包裹方式。人为插入单引号会迫使下一次序列化改用双引号包裹，从而使正文中的双引号被反斜杠转义。文本组件解析后的 `extra` 分段提供了无需手工查找边界的中间结构。

## 注意事项

- 这是对 `t0467` 基础转义规则的动态字符串处理扩展。
- 来源未给出完整可运行命令，宏重写与文本组件解析步骤需要补齐。
- 必须测试空字符串、同时包含单双引号和反斜杠的输入。

