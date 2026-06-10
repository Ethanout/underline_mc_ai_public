---
id: t0262
title: predicate 参数：使用自定义谓词
title_en: "predicate Parameter: Using Custom Predicates"
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["target-selector", "predicate", "custom-condition", "data-pack"]
verified_in_game: false
---

## 核心洞见

predicate 可以引用数据包中的谓词文件（JSON），实现复杂的条件筛选，如检查生物群系、方块状态、实体属性等，比 nbt 更灵活。

## 代码示例

```mcfunction
# 选择满足自定义谓词 'my_pack:is_in_forest' 的玩家
tellraw @a[predicate=my_pack:is_in_forest] {"text":"在森林中"}
# 多个谓词 AND 条件
tellraw @a[predicate=my_pack:is_in_forest,my_pack:has_iron_armor] {"text":"森林中的铁甲玩家"}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

predicate 参数接受一个或多个谓词路径（如 'example:check_biome'），实体必须满足所有谓词条件。谓词文件位于 data/<命名空间>/predicates/ 下，支持多种条件类型。

## 注意事项

- 常见误解：很多人以为只能用 nbt 或 scores 做复杂筛选，但 predicate 可以复用且支持条件组合。
