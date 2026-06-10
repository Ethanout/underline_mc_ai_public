---
id: t0225
title: 利用玩家睡眠百分比控制昼夜循环
title_en: Use Players Sleeping Percentage for Day/Night Control
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["multiplayer", "gameplay", "custom-mechanics"]
verified_in_game: false
---

## 核心洞见

通过调整 playersSleepingPercentage 可以控制需要多少比例玩家睡觉才能跳过夜晚，设为 0 则单人即可跳过，设为 100 则需要全部玩家。

## 代码示例

```mcfunction
gamerule playersSleepingPercentage 0
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该规则设置需要睡觉的玩家百分比（0-100）才能跳过夜晚。设为 0 时任意一个玩家睡觉即可跳过，设为 100 时需要所有在线玩家都睡觉。可用于自定义多人游戏规则。

## 注意事项

- 常见误解：开发者认为睡眠跳过夜晚的机制是固定的，无法通过数据包调整。
