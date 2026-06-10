<!-- _trash_id: t0210 | _trash_original: t0210_Score_Operation_Swap_Mode.md | _trash_index: {"file": "techniques/t0210_recursive_raycast.md", "title_zh": "递归射线检测", "title_en": "recursive_raycast", "source_url": "https://datapack.wiki/guide/misc/raycasts", "source_type": "datapack_wiki", "wiki_covers_this": false, "version_min": "1.13", "tags": ["raycast", "recursive_function", "entity_detection", "positioned", "execute"], "verified_in_game": false} -->
---
id: t0210
title: 分数操作交换模式
title_en: Score Operation Swap Mode
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["scoreboard", "operation", "swap"]
verified_in_game: false
---

## 核心洞见

`><` 操作符可以交换两个玩家的分数，而无需临时变量，这是其他操作符无法直接实现的功能。

## 代码示例

```mcfunction
scoreboard players operation @p score >< @r score
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

`/scoreboard players operation` 的 `><` 操作符会直接交换目标玩家和目标目标与源玩家和源目标之间的分数值，一步完成交换，无需额外存储。

## 注意事项

- 常见误解：开发者可能认为分数交换需要借助第三个临时目标或复杂的链式操作。
