---
id: t0208
title: 触发器目标启用机制
title_en: Trigger Objective Enable Mechanism
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["trigger", "player-input", "scoreboard"]
verified_in_game: false
---

## 核心洞见

触发器目标必须通过 `/scoreboard players enable` 显式启用后玩家才能使用 `/trigger` 命令，这提供了一种安全的玩家输入机制，无需给予命令权限。

## 代码示例

```mcfunction
scoreboard objectives add quest dummy
scoreboard objectives modify quest trigger
scoreboard players enable @p quest
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

创建触发器目标后，其初始状态为禁用。通过 `/scoreboard players enable` 命令为特定玩家启用该目标，之后该玩家才能使用 `/trigger` 命令修改自己的分数。启用是一次性的，每次使用 `/trigger` 后目标会再次禁用，需要重新启用。

## 注意事项

- 常见误解：开发者常误以为触发器目标创建后玩家就能直接使用 `/trigger` 命令，实际上需要先启用。
