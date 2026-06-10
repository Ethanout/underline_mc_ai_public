---
id: t0238
title: "JSON基础"
title_en: "json_basics_for_datapacks"
layer: technique
source_url: "https://datapack.wiki/wiki/info/json"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.13"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["json", "data-format", "datapack-basics"]
verified_in_game: false
---

## 核心洞见

JSON是Minecraft数据包中用于存储结构化数据的标准格式，其键值对结构是理解谓词、标签和样式文本的基础。

## 代码示例

```mcfunction
{
  "name": "Aron Aronson",
  "age": 83,
  "alive": true,
  "family_members": ["James Aronson", "Catherine Aronson"],
  "login_details": {
    "email": "aron.aronson@gmail.com",
    "password": "MyNameIsAron12345"
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

JSON（JavaScript Object Notation）是一种轻量级数据交换格式，基于键值对存储数据。在Minecraft数据包中，JSON文件（如谓词、标签）和.mcmeta文件都使用此格式。其核心机制是：每个JSON对象由花括号{}包裹，内部包含多个键值对，键必须是双引号字符串，值可以是字符串、整数、浮点数、布尔值、列表或嵌套字典。列表用方括号[]表示有序集合，字典用花括号表示无序键值对集合。JSON路径（如root.name）用于定位嵌套结构中的特定值，但数据包中更常用NBT路径。理解JSON的数据类型和嵌套规则是编写有效数据包文件的前提。

## 注意事项

- 键必须用双引号包裹，不能省略
- 字符串值必须用双引号，数字和布尔值不能加引号
- 列表索引从0开始，容易混淆
- 嵌套字典的路径分隔符是点号，但不同语言可能有不同语法
- 常见误解：开发者可能认为JSON只是简单的文本文件，而忽略了其严格的数据类型规则（如字符串必须用引号、键必须用双引号）和嵌套结构。
