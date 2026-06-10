---
id: t0219
title: 时间查询的三种模式差异
title_en: Three Time Query Modes and Their Differences
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["time", "query", "scoreboard", "day-night-cycle"]
verified_in_game: false
---

## 核心洞见

time query的daytime、gametime、day返回不同时间尺度，玩家常混淆daytime（当天刻数）和gametime（总刻数）的用途。

## 代码示例

```mcfunction
execute if score time <namespace> matches 6000.. run say 已过正午
# 需先执行：scoreboard objectives add <namespace> dummy
# 再执行：execute store result score time <namespace> run time query daytime
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

daytime返回当前时间在一天内的偏移（0=日出，6000=正午，12000=日落，18000=午夜），gametime返回世界总运行刻数（包括睡觉跳过的时间），day返回floor(gametime/24000)。三者用于不同场景的条件判断。

## 注意事项

- 常见误解：玩家可能认为daytime返回世界总时间，或day返回天数（整数），实际daytime是0-24000的当天刻数，gametime是自世界创建的总刻数，day是已过游戏天数（向下取整）。
