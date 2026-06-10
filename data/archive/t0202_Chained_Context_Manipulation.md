---
id: t0202
title: 执行上下文链式组合
title_en: Chained Context Manipulation
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["execute", "context", "chain", "position", "rotation"]
verified_in_game: false
---

## 核心洞见

通过连续使用多个修饰子命令（如 as、at、positioned、rotated），可以精确控制命令的执行者、位置、旋转和维度，实现复杂的上下文切换，而不仅仅是简单的 as 和 at 组合。

## 代码示例

```mcfunction
execute as @e[type=sheep] at @s positioned ~ ~1 ~ run setblock ~ ~ ~ minecraft:wool
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

每个修饰子命令（如 as、at、positioned、rotated）都会修改执行上下文的特定部分，并且可以按顺序链式调用。例如，`execute as @e[type=sheep] at @s positioned ~ ~1 ~` 会先设置执行者为所有羊，然后将其位置设为羊的位置，再向上偏移1格，最终命令在羊上方1格处执行。

## 注意事项

- 常见误解：开发者常认为 execute 只能设置执行者和位置，实际上可以链式组合多个修饰子命令，每个子命令都会覆盖或叠加之前的上下文，形成高度定制化的执行环境。
