---
id: t0334
title: "数据继承合并"
title_en: "inheritance_data_merge"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202509/0/content"
source_type: "feature_article"
source_issue: "202509"
version_min: "1.20.5"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["数据继承", "合并", "变体", "复用"]
verified_in_game: false
---

## 核心洞见

通过 `inheritance` 字段，允许在生成模型时动态覆盖或扩展索引中的默认数据，实现了类似原型继承的数据合并机制。

## 代码示例

```mcfunction
/give @s minecraft:cow_spawn_egg[entity_data={id:"minecraft:marker",Tags:["dc_place"],data:{index:"#YOURINDEX#",inheritance:{item:{id:"apple"}}}}]
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

在标记实体的 `data` 中，除了 `index` 字段外，还可以包含一个 `inheritance` 字段，其结构与索引注册数据相同。当模型生成时，系统会先读取索引中的默认数据，然后将 `inheritance` 中的数据与默认数据合并。合并规则是：`inheritance` 中的字段会覆盖索引中同名的字段，而索引中独有的字段则保留。这种机制允许开发者注册一个基础模型索引，然后通过不同的物品（如刷怪蛋）携带不同的 `inheritance` 数据来生成变体，例如改变显示的物品、调整缩放或覆盖事件。这大大减少了索引注册的数量，提高了复用性。

## 注意事项

- `inheritance` 仅在模型生成时生效，后续修改不会影响已生成的模型
- 合并是浅合并，嵌套的复合标签会被整体替换而非深度合并
- `inheritance` 中的 `type` 字段不能与索引中的 `type` 不同，否则可能导致模型类型冲突
- 常见误解：开发者通常认为模型数据必须完全由索引定义，无法在生成时针对特定物品进行个性化调整，导致需要为每个变体注册独立的索引。
