---
id: t0243
title: 玩家分散与队伍分组
title_en: Player Spreading with Team Grouping
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["spreadplayers", "team", "grouping", "multiplayer"]
verified_in_game: false
---

## 核心洞见

通过设置 respectTeams 为 true，可以将同一队伍的玩家分散到同一位置，而不同队伍的玩家分散到不同位置，实现队伍分组分散。

## 代码示例

```mcfunction
spreadplayers 0 0 5 20 true @a
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

当 respectTeams 为 true 时，命令会按队伍分组，同一队伍的玩家会被分散到同一个随机位置，不同队伍的玩家则分散到不同位置。这利用了队伍机制来改变分散行为。

## 注意事项

- 常见误解：开发者可能认为 spreadplayers 只能将每个目标分散到不同位置，无法实现队伍内聚集。
