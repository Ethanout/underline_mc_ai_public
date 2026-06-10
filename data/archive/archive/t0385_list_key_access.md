---
id: t0385
title: "列表键值访问"
title_en: "list_key_access"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202506/4/content"
source_type: "feature_article"
source_issue: "202506"
version_min: "1.20"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["列表", "键值访问", "SNBT", "数据查找"]
verified_in_game: false
---

## 核心洞见

Minecraft的列表支持通过键值对进行元素查找，而不仅限于下标访问，这提供了类似字典的灵活性。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

在Minecraft的SNBT中，列表（[]）不仅支持O(1)的下标访问，还支持通过键值对进行元素查找。例如，列表list:[{name:"a",age:1},{name:"b",age:2}]中，list[{name:"a"}]会返回第一个元素{name:"a",age:1}。这种查找基于键值对的精确匹配，要求键值对唯一指向一个元素。与下标访问不同，键值对查找是O(n)的，因为需要遍历列表。这一特性在最新版本中有效，但旧版本列表有类型限制，可能不支持混合类型。

## 注意事项

- 键值对查找是O(n)的，性能低于下标访问
- 键值对必须唯一指向一个元素，否则行为未定义
- 旧版本列表有类型限制，可能不支持混合类型或键值对查找
- 常见误解：开发者可能认为列表只能通过整数下标访问元素，忽略了键值对匹配的查找方式。
