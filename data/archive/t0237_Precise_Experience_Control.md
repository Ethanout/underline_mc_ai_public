---
id: t0237
title: 经验值精确控制
title_en: Precise Experience Control
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["experience", "player", "progress"]
verified_in_game: false
---

## 核心洞见

通过指定 levels 或 points 参数，可以精确控制玩家获得或设置的经验值，而不仅仅是等级，这在需要精细调整玩家进度时非常有用。

## 代码示例

```mcfunction
experience add @p 100 points
experience set @p 0 levels
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

使用 /experience add 或 set 命令时，通过第三个参数指定 levels 或 points，可以分别操作等级或经验点数。points 参数允许以整数形式增加或设置经验值，从而实现比等级更精细的控制。

## 注意事项

- 常见误解：开发者常认为 /xp 只能操作等级，而忽略了 points 参数可以操作经验点数，导致无法实现精确的经验值调整。
