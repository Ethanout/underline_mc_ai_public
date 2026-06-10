---
id: t0388
title: "命令方块时间提取"
title_en: "command_block_time_via_output"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202510/5/content"
source_type: "feature_article"
source_issue: "202510"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["command_block", "time_detection", "string_parsing", "world_close_detection"]
verified_in_game: false
---

## 核心洞见

命令方块的输出值包含执行时的现实时间（精确到秒），通过字符串切片和宏可以将其转存到计分板，用于检测世界关闭到重新打开的时长。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

当命令方块执行任意命令时，其输出（如聊天栏或命令方块GUI）会显示一个时间戳，格式为[HH:MM:SS]，精确到秒。通过使用/execute store result或/data get命令，可以获取命令方块的输出字符串，然后利用宏或字符串处理函数（如/scoreboard players set）提取时间部分。关键原理：命令方块输出是字符串，但Minecraft的宏系统支持字符串切片（如$(output:1:8)），可以提取时间子串。与朴素实现（如使用/stopwatch）相比，此方法不依赖新版本特性，且能检测世界关闭期间的时间（因为命令方块时间基于系统时钟）。但需要注意，该方式会改变世界（放置命令方块），且精度仅为秒。

## 注意事项

- 命令方块必须被放置并激活，会对世界产生永久性改变
- 时间精度仅为秒，无法用于毫秒级检测
- 输出格式可能因语言或版本不同而变化，需适配
- 世界关闭超过24小时时，时间戳无法区分日期，会导致误差
- 常见误解：开发者通常认为命令方块输出只包含命令结果，但实际输出中包含了时间戳信息，可以用于时间检测。
