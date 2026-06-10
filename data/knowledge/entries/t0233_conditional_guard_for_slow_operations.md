---
id: t0233
title: "条件守卫避免慢操作"
title_en: "conditional_guard_for_slow_operations"
layer: technique
source_url: "https://datapack.wiki/guide/performance/write-optimized-code"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["NBT", "performance", "conditional", "tag"]
verified_in_game: false
---

## 核心洞见

通过标签和条件判断，可以避免对已处理过的实体重复执行 NBT 等慢操作。

## 代码示例

```mcfunction
# tick.mcfunction
execute as @e[type=pig] unless entity @s[tag=disabled_ai] run function example:disable_ai

# example.mcfunction
data modify entity @s NoAI set value true
tag @s add disabled_ai
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

实体/方块的 NBT 操作（包括修改、复制、条件判断）是游戏中最慢的操作之一，应避免每 tick 执行。如果必须执行，可以通过添加标签来标记已处理过的实体，然后使用 unless entity @s[tag=...] 条件来跳过已处理的实体。这样慢操作只会在首次处理时执行一次，后续 tick 条件不满足就不会执行。

## 注意事项

- 标签需要额外管理，确保在适当的时候清除
- 如果实体数量很大，即使条件判断本身也可能带来性能开销
- 常见误解：开发者可能认为每次 tick 对所有实体执行 NBT 操作是正常的，没有意识到 NBT 操作是游戏中最慢的操作之一。
