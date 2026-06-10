---
id: t0305
title: "减半法右键检测"
title_en: "halfing_method_right_click_detection"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202601/f/content"
source_type: "feature_article"
source_issue: "202601"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["右键检测", "整数除法", "状态机", "性能优化", "计分板"]
verified_in_game: false
---

## 核心洞见

通过整数除法和加法组合，可以在单个计分板变量中编码右键长按、松开和断触状态，无需额外状态机变量。

## 代码示例

```mcfunction
# example:rmb/using_item
# ...右键运行example:rmb/run的进度

# example:load
scoreboard objectives add rmb_flag dummy
scoreboard objectives add example dummy
scoreboard players set 2 example 2

# example:rmb/run
scoreboard players add @s rmb_flag 4
advancement revoke @s only example:rmb/using_item

# example:tick
execute as @a at @s run function example:rmb/player_tick

# example:rmb/player_tick
scoreboard players operation @s rmb_flag /= 2 example
execute if score @s rmb_flag matches 2 run say 开始长按右键
execute if score @s rmb_flag matches 3 run say 正在长按右键
execute if score @s rmb_flag matches 1 run say 松开右键
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用整数除法（向下取整）的特性，在单个变量中实现状态流转。核心公式为：每次输入信号时变量加4（或6），每个游戏刻变量除以2。由于整数除法中，只有2和3除以2会得到1，其他数字多次除以2后最终会回到2或3。因此，当玩家开始右键时，变量从0开始：0+4=4，4/2=2（开始状态）；2+4=6，6/2=3（长按状态）；持续加4则保持在3；停止输入后，3/2=1（松开状态）；1/2=0（无操作）。加6的方案提供更稳定的断触保护：0+6=6，6/2=3（开始）；3+6=9，9/2=4（长按）；4+6=10，10/2=5（长按）；停止后5/2=2，2/2=1（松开），1/2=0。该机制的关键在于整数除法对2和3的特殊行为，使得状态序列始终以2或3开始、以1结束，中间值可表示持续长按。与朴素实现（使用多个布尔变量或进度检测）相比，减半法仅需一个变量和一次除法运算，性能极高，且通过调整加数即可实现断触保护，无需额外逻辑。

## 注意事项

- 必须预先设置一个值为2的常量计分板（如example=2）作为除数，因为计分板运算不支持直接除以数字
- 加4方案在断触时可能不稳定，建议使用加6方案以获得更好的断触保护
- 状态值依赖于整数除法特性，如果使用浮点数或不同运算顺序会破坏状态机
- 常见误解：开发者通常使用多个计分板变量或进度系统来分别记录右键按下、长按和松开状态，导致逻辑复杂且性能较低。
