---
id: t0421
title: "血量百分比计算"
title_en: "scoreboard_health_percentage_calculation"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202505/5/content"
source_type: "feature_article"
source_issue: "202505"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["scoreboard", "execute", "health", "percentage", "easing"]
verified_in_game: false
---

## 核心洞见

通过 scoreboard 和 execute store 命令，可以在原版 Minecraft 中精确计算生物的血量百分比，并实现缓动效果。

## 代码示例

```mcfunction
# load.mcfunction
# 当前血量
scoreboard objectives add skapi.health dummy
# 最大血量
scoreboard objectives add skapi.health_max dummy
# 血量百分比
scoreboard objectives add skapi.health_percent dummy
# 缓动血量百分比
scoreboard objectives add skapi.health_temp dummy
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用 scoreboard 的 dummy 类型存储血量相关数值，并通过 execute store result 命令将 NBT 数据（如 Health 和 MaxHealth）转换为计分板分数。由于 Minecraft 的 Health 和 MaxHealth 是浮点数，但 execute store result 会将其截断为整数，因此需要先乘以 100 来保留两位小数精度。计算百分比时，使用 scoreboard players operation 进行整数乘法和除法：先计算 (Health * 100) / MaxHealth，得到 0-100 的整数百分比。缓动效果通过比较当前缓动百分比和实际百分比实现：如果缓动值小于实际值，则直接设为实际值（快速上升）；如果缓动值大于实际值，则每次减少 3（缓慢下降），模拟血条缓动。

## 注意事项

- Health 和 MaxHealth 是浮点数，直接 execute store result 会丢失小数部分，需要先乘以 100 再计算。
- scoreboard 的除法是整数除法，会向下取整，可能导致百分比计算偏差，需要确保精度。
- 缓动逻辑中，如果缓动值小于实际值，直接设为实际值，这会导致血条瞬间上升，可能不符合某些设计需求。
- 常见误解：开发者通常认为计算百分比需要复杂的数学运算或模组支持，或者认为原版命令无法处理浮点数。
