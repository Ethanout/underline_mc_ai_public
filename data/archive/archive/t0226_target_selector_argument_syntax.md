---
id: t0226
title: "选择器参数语法"
title_en: "target_selector_argument_syntax"
layer: technique
source_url: "https://datapack.wiki/wiki/concepts/target-selectors"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.13"
version_max: ""
wiki_covers_this: true
confidence: low
tags: ["target-selector", "command-syntax", "filtering"]
verified_in_game: false
---

## 核心洞见

目标选择器通过方括号内的键值对参数实现精确过滤，支持范围语法和取反操作。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

目标选择器（如@e、@a）后跟方括号内的参数列表，参数以逗号分隔，格式为`<参数名>=<值>`或`<参数名>:<值>`。参数值支持范围语法（如`..10`表示小于等于10，`5..10`表示5到10之间），以及取反操作（如`type=!minecraft:creeper`表示非苦力怕）。这些参数在命令执行时由游戏引擎解析，根据实体属性（类型、名称、距离等）进行过滤，只返回符合条件的实体。与直觉不同，参数可以组合使用，实现多条件过滤。

## 注意事项

- 参数值中的字符串（如name）不能是JSON文本，只能是纯字符串
- @e只选择已加载区块中的实体，未加载的实体不会被选中
- 某些参数（如type）只适用于特定基础选择器（@e、@s、@n）
- 常见误解：开发者可能认为目标选择器只能选择所有实体或玩家，无法进行精细过滤。
