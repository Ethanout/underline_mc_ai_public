---
id: t0250
title: 边界警告与缓冲区的精确控制
title_en: Precise Warning and Buffer Control
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["worldborder", "warning", "buffer", "separation"]
verified_in_game: false
---

## 核心洞见

`worldborder warning distance` 和 `worldborder warning time` 可以独立于伤害设置，实现视觉警告与伤害触发的分离。

## 代码示例

```mcfunction
# 设置警告距离为20格，但伤害缓冲为5格，玩家在边界外5-20格内只看到警告不受伤害
worldborder warning distance 20
worldborder damage buffer 5
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

`warning distance` 控制红色警告线的显示距离（默认5格），`warning time` 控制收缩时的警告时间（默认15秒），而 `damage buffer` 控制实际伤害开始的距离（默认5格），三者可独立设置，实现“提前警告但延迟伤害”或“无警告直接伤害”等效果。

## 注意事项

- 常见误解：开发者认为警告距离和时间必须与伤害参数一致，无法单独调整。
