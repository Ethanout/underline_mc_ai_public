---
id: t0205
title: facing 子命令的朝向计算
title_en: Facing Subcommand Direction Calculation
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["execute", "facing", "rotation", "direction"]
verified_in_game: false
---

## 核心洞见

facing 子命令可以动态计算朝向某个坐标或实体的旋转角度，无需手动计算 yaw/pitch，常用于创建指向目标的效果或实体生成。

## 代码示例

```mcfunction
execute as @e[type=arrow] at @s facing entity @p eyes run summon minecraft:lightning_bolt ^ ^ ^1
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

`execute facing <pos>` 或 `execute facing entity <targets> (eyes|feet)` 会计算从当前执行位置到目标位置的方向向量，并设置执行上下文的旋转。这可以用于生成指向目标的箭、调整玩家视角或放置朝向特定方向的方块。

## 注意事项

- 常见误解：开发者常认为设置旋转必须手动指定 yaw/pitch 数值，实际上 facing 可以自动计算朝向，且支持实体和坐标两种模式。
