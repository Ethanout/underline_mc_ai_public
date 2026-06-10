---
id: t0419
title: "无宏队列遍历"
title_en: "queue_traversal_without_macro"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202511/3/content"
source_type: "feature_article"
source_issue: "202511"
version_min: "1.20.2"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["数据结构", "队列遍历", "data命令", "递归"]
verified_in_game: false
---

## 核心洞见

通过复制队列到辅助列表并循环出队，可以在不使用宏的情况下遍历 NBT 列表队列。

## 代码示例

```mcfunction
$data modify set storage queue:data back set from storage queue:data $(name)
function <operation>
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

队列遍历的核心是逐个处理元素直到队列为空。方法是将原始队列复制到一个辅助列表（备用列表），然后对辅助列表反复执行出队操作（data remove list[0]），每次出队前检查 list[0] 是否存在（execute if data ... list[0]），若存在则处理该元素。由于 data remove 会动态更新列表索引，循环直到列表为空。这种方法避免了宏的复杂性，仅使用基本的 data 命令和函数递归。关键点：复制到辅助列表是为了保护原始数据不被破坏；使用 execute if data 检查 list[0] 是否存在作为循环终止条件。

## 注意事项

- 辅助列表必须与原始队列独立，否则会修改原始数据
- 循环中每次出队后需重新检查 list[0] 是否存在
- 如果队列很大，递归调用可能导致性能问题或函数栈溢出
- 常见误解：开发者可能认为遍历 NBT 列表队列必须使用宏或复杂的递归函数。
