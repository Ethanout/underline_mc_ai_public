---
id: t0491
title: "UUID死亡检测"
title_en: "uuid_based_death_detection"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/mobdeaths"
source_type: "mcc_wiki"
source_issue: "questions/mobdeaths"
version_min: "1.20.2"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["death_detection", "uuid", "macro", "storage", "nbt_check"]
verified_in_game: false
---

## 核心洞见

通过将生物的 UUID 转换为十六进制格式并存储在 storage 中，使用宏函数直接通过 UUID 访问生物数据，实现最精确的死亡检测。

## 代码示例

```mcfunction
```mcfunction
# function example:load
function example:loops/1s

# function example:loops/1s
schedule function example:loops/1s 1s
execute as @e[tag=death_check,tag=!init] run function example:death_check/init
data modify storage example:macro death_check set from storage example:database death_check
function example:death_check/check with storage example:macro death_check[-1]

# function example:death_check/init
function gu:convert with entity @s
data remove storage example:data this
data modify storage example:data this.UUID set from storage gu:main out
data modify storage example:database death_check append from storage example:data this
data modify entity @s PersistenceRequired set value true
tag @s add init

# function example:death_check/check
$execute as $(UUID) unless data entity @s {DeathTime:0s} at @s run function example:death_check/death_event {UUID:$(UUID)}
$data remove storage example:macro death_check[{UUID:$(UUID)}]
function example:death_check/check with storage example:macro death_check[-1]

# function example:death_check/death_event
$data remove storage example:database death_check[{UUID:$(UUID)}]
say This mob is dying!
particle minecraft:soul_fire_flame ~ ~1 ~ 0.5 1 0.5 0.01 100
```
```

## 文件结构

- data/example/functions/load.mcfunction
- data/example/functions/loops/1s.mcfunction
- data/example/functions/death_check/init.mcfunction
- data/example/functions/death_check/check.mcfunction
- data/example/functions/death_check/death_event.mcfunction
- data/gu/functions/convert.mcfunction

## 用法

构建完数据包并安装 UUID 转换器库后，为需要检测死亡的生物添加 `death_check` 标签。数据包会自动初始化这些生物（记录 UUID 并设置 PersistenceRequired），然后每秒循环检查所有记录的 UUID 对应的生物是否死亡。当检测到死亡时，会执行 `example:death_check/death_event` 函数。

## 使用场景

['需要最高精度的死亡检测，且不依赖玩家击杀', '需要精确知道哪个具体生物死亡（通过 UUID 唯一标识）', '需要在生物死亡时执行复杂的自定义事件（如粒子效果、声音、命令链）']

## 机制原理

Minecraft 中每个实体都有一个唯一的 UUID，但 `/data get` 命令只能以整数列表形式获取 UUID，而 `/execute as` 命令需要十六进制格式的 UUID。通过 UUID 转换器库（如 gu），可以将整数列表形式的 UUID 转换为十六进制字符串。将这些 UUID 存储在 storage 中，然后使用宏函数（$ 语法）将 UUID 插入到 `execute as $(UUID)` 命令中，从而直接通过 UUID 选中目标实体。然后使用 `unless data entity @s {DeathTime:0s}` 检查该实体的 DeathTime 是否不为 0，即可判断是否死亡。由于直接通过 UUID 访问，不受目标选择器限制，即使生物处于死亡动画中也能检测到。

## 注意事项

- 此方法无法检测生物消失（despawn），因此需要为生物设置 `PersistenceRequired:true` 以防止自然消失
- 需要额外安装 UUID 转换器库（如 gibbsly/gu）
- 实现复杂度高，需要理解宏函数和 storage 操作
- 大量 UUID 的循环检查可能导致卡顿，建议使用检测延迟
- 检测到死亡后必须立即从 storage 中移除该 UUID，否则后续循环会持续尝试访问已死亡的实体，导致性能问题
- 此方法在 1.20.2+ 版本中可用
