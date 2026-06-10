---
id: t0227
title: 标题清除与重置
title_en: Title Clear and Reset
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["title", "clear", "reset", "ui"]
verified_in_game: false
---

## 核心洞见

使用 /title clear 可以立即移除所有玩家的标题显示，而 /title reset 不仅清除标题，还会将时间参数恢复为默认值，避免残留动画影响后续标题。

## 代码示例

```mcfunction
title @a clear
title @a reset
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

/title <targets> clear 立即移除当前显示的标题、副标题和操作栏内容。/title <targets> reset 除了清除显示外，还将淡入、停留、淡出时间重置为默认值（分别为 10、70、20 游戏刻），确保后续标题使用标准动画。

## 注意事项

- 常见误解：开发者可能认为清除标题只需发送空消息，或者重置时间参数需要重新设置。
