---
id: t0508
title: "谓词比较分数"
title_en: "score_comparison_via_predicate"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/scorecompare"
source_type: "mcc_wiki"
source_issue: "questions/scorecompare"
version_min: "1.15"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["predicate", "scoreboard", "comparison", "entity_scores"]
verified_in_game: false
---

## 核心洞见

使用 predicate 的 entity_scores 条件，通过 min/max 和 inverted 组合，可以实现分数之间的大于、小于、等于比较，而不仅仅是与固定值比较。

## 代码示例

```mcfunction
```json
# execute if score @s kills >= @s deaths
{
  "condition": "minecraft:entity_scores",
  "entity": "this",
   "scores": {
     "kills": {
      "min": {
        "type": "minecraft:score",
        "target": "this",
        "score": "deaths"
      }
    }
  }
}
```
```json
# execute if score @s kills > @s deaths
[
  {
    "condition": "minecraft:entity_scores",
    "entity": "this",
    "scores": {
      "kills": {
        "min": {
          "type": "minecraft:score",
          "target": "this",
          "score": "deaths"
        }
      }
    }
  },
  {
    "condition": "minecraft:inverted",
    "term": {
      "condition": "minecraft:entity_scores",
      "entity": "this",
      "scores": {
        "kills": {
          "max": {
            "type": "minecraft:score",
            "target": "this",
            "score": "deaths"
          }
        }
      }
    }
  }
]
```
```json
# execute if score @s kills = @s deaths
{
  "condition": "minecraft:entity_scores",
  "entity": "this",
  "scores": {
    "kills": {
      "min": {
        "type": "minecraft:score",
        "target": "this",
        "score": "deaths"
      },
      "max": {
        "type": "minecraft:score",
        "target": "this",
        "score": "deaths"
      }
    }
  }
}
```
```

## 文件结构

- data/<namespace>/predicates/compare_kills_deaths.json

## 用法

构建完数据包后，在需要触发条件的地方（如 loot table、advancement 的 predicate 引用）引用此 predicate 文件。例如在 advancement 的 criteria 中或作为 execute if predicate 的参数使用。

## 使用场景

['在 advancement 或 loot table 中，需要根据实体两个分数之间的关系（如 kills >= deaths）来决定是否触发奖励或事件。', '在需要避免使用 function 循环或 scoreboard operation 的纯声明式数据包设计中，用 predicate 实现分数比较。', '当需要比较非整数或 storage 中的值时（1.20.5+），predicate 的 value_check 支持更精确的比较。']

## 机制原理

predicate 的 `minecraft:entity_scores` 条件允许检查指定实体的某个分数是否在某个范围内。该范围（range）的 `min` 和 `max` 字段可以接受一个 `minecraft:score` 类型的值，即引用另一个实体的另一个分数。通过将 `min` 设置为另一个分数，可以实现 `>=` 比较；将 `max` 设置为另一个分数，可以实现 `<=` 比较。对于严格大于（`>`），需要组合两个条件：先检查 `>=`，再通过 `minecraft:inverted` 反转 `<=` 条件，从而排除相等的情况。对于严格等于（`=`），将 `min` 和 `max` 都设置为同一个分数即可。这种方法的非直觉之处在于，predicate 通常用于与固定值比较，但通过嵌套引用分数，可以实现实体间分数的动态比较，而无需使用 scoreboard operation 临时修改分数。

## 注意事项

- 此方法仅适用于 predicate 中 `entity` 为 `this` 的场景（如 loot table 中的 killed entity），无法直接比较任意两个实体（如 @s 和 @p）的分数。
- 对于 1.20.5+，也可以使用 `minecraft:value_check` 配合 storage 进行更精确的非整数比较。
- predicate 中的分数比较不支持直接使用 >、< 等运算符，只能通过 min/max 和 inverted 组合实现。
- 此技术从 1.15 开始可用。
