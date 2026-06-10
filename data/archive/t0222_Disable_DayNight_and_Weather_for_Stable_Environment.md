---
id: t0222
title: 禁用昼夜与天气循环以稳定环境
title_en: Disable Day/Night and Weather for Stable Environment
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["environment", "stability", "game-design"]
verified_in_game: false
---

## 核心洞见

同时设置 doDaylightCycle 和 doWeatherCycle 为 false 可以完全固定时间和天气，避免环境变化干扰数据包逻辑。

## 代码示例

```mcfunction
gamerule doDaylightCycle false
gamerule doWeatherCycle false
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

这两个规则分别控制时间和天气是否自动变化。设为 false 后，时间和天气完全由命令控制，适合需要恒定环境（如小游戏、展示）的场景。

## 注意事项

- 常见误解：开发者可能只设置 time set 或 weather clear，但循环仍在后台运行，导致意外变化。
