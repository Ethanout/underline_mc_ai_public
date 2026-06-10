---
id: t0348
title: "TPS检测"
title_en: "tps_detection_via_debug"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202508/6/content"
source_type: "feature_article"
source_issue: "202508"
version_min: "1.14.4"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["tps", "debug", "schedule", "performance", "monitoring"]
verified_in_game: false
---

## 核心洞见

利用 /debug stop 命令的输出和 /schedule 定时执行，可以在数据包中实现实时 TPS 检测，无需外部工具。

## 代码示例

```mcfunction
# load.mcfunction
scoreboard objectives add tps_detection dummy
#1.20.3+
execute store result score target_tps tps_detection run tick query
#1.20.3-
#scoreboard players set target_tps tps_detection 20
#1.15+
schedule function tps-detection:update_tps 20 replace
#1.15- 1.14.4+
#schedule function tps-detection:update_tps 20
debug start

# update_tps.mcfunction
#1.15+
schedule function tps-detection:update_tps 20 replace
#1.15- 1.14.4+
#schedule function tps-detection:update_tps 20
execute store result score tps tps_detection run debug stop
#display
title @a title ["TPS:",{"score":{"name":"tps","objective":"tps_detection"}},"/",{"score":{"name":"target_tps","objective":"tps_detection"}}]
debug start
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术基于 Minecraft 的刻分析器机制。`/debug start` 启动一个刻分析会话，记录从启动到停止期间的平均 TPS（每秒游戏刻数）。`/debug stop` 命令会输出该平均 TPS 值，通过 `/execute store result ... run debug stop` 可以将这个值存储到记分板中。为了持续检测，使用 `/schedule function ... 20 replace` 每 20 游戏刻（约 1 秒）执行一次检测函数，函数内先执行 `/debug stop` 获取 TPS，再立即执行 `/debug start` 开始新一轮分析。间隔 20 tick 是经过测试的平衡点：低于 15 tick 会导致误差过大，20 tick 能兼顾速度和准确性。关键限制是 `/debug` 需要权限等级 3，而函数默认权限等级为 2，因此需要 1.14.4-pre4 引入的 `function-permission-level` 配置项将函数权限提升到 3 才能工作。

## 注意事项

- 间隔低于 15 tick 会导致检测误差很大，必须使用 20 tick 或以上
- 需要 1.14.4-pre4 及以上版本，因为需要设置 function-permission-level 为 3 才能让函数执行 /debug 命令
- 1.15 之前的 /schedule 没有 replace 参数，可能产生计划堆积问题
- 1.20.3+ 版本可以用 /tick query 获取目标 TPS，但旧版本需要手动设置目标 TPS 值
- 常见误解：开发者可能认为 TPS 检测需要外部插件或 mod，或者认为 /debug 命令只能手动执行，无法在数据包中自动化。
