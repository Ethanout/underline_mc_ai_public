---
id: t0247
title: 队伍名称标签可见性控制
title_en: Team Nametag Visibility Control
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["team", "nametag", "visibility", "stealth"]
verified_in_game: false
---

## 核心洞见

通过队伍的名称标签可见性设置，可以控制玩家头顶名称标签的显示规则，实现隐藏身份、团队隐身等高级游戏机制。

## 代码示例

```mcfunction
# 设置队伍A的成员名称标签对其他队伍隐藏
team modify teamA nametagVisibility hideForOtherTeams
# 设置队伍B的成员名称标签对同队伍隐藏
team modify teamB nametagVisibility hideForOwnTeam
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

使用 `/team modify <team> nametagVisibility` 命令，可以设置队伍成员名称标签的显示规则。选项包括：always（总是显示）、never（从不显示）、hideForOtherTeams（对其他队伍隐藏）、hideForOwnTeam（对同队伍隐藏）。这个设置会立即生效，影响所有观察该队伍成员的玩家。

## 注意事项

- 常见误解：开发者通常认为名称标签只能全局显示或隐藏，无法根据队伍关系进行条件控制。
