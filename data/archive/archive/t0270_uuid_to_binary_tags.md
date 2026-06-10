---
id: t0270
title: "UUID转二进制标签"
title_en: "uuid_to_binary_tags"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202602/5/content"
source_type: "feature_article"
source_issue: "202602"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["实体定位", "二进制编码", "标签系统", "UUID"]
verified_in_game: false
---

## 核心洞见

通过将生物的唯一索引号转换为二进制位并存储为标签，可以在玩家受伤时快速定位到攻击者生物，而不需要遍历所有实体。

## 代码示例

```mcfunction
scoreboard players add $FlagIndex Global 1
scoreboard players operation $FlagIndex Global %= $2^15 Const
execute if score $FlagIndex Global matches 0 run scoreboard players add $FlagIndex Global 1
scoreboard players operation @s MobUUID = $FlagIndex Global
scoreboard players operation $CloneFlagIndex Temporary = $FlagIndex Global
scoreboard players operation $CloneFlagIndex Temporary *= $2^16 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag0.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag0.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag1.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag1.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag2.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag2.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag3.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag3.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag4.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag4.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag5.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag5.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag6.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag6.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag7.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag7.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag8.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag8.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag9.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag9.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag10.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag10.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag11.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag11.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag12.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag12.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag13.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag13.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag14.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag14.1
scoreboard players operation $CloneFlagIndex Temporary *= $2 Const
execute if score $CloneFlagIndex Temporary matches 00.. run tag @s add FindFlag15.0
execute if score $CloneFlagIndex Temporary matches ..-1 run tag @s add FindFlag15.1
scoreboard players reset $CloneFlagIndex Temporary
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用全局计分板维护一个递增的索引号（最大2^16），每个生物创建时获取当前索引作为其UUID。然后将这个十进制索引转换为16位二进制数，通过不断左移（乘以2）并检测符号位（matches 00..或..-1）来逐位判断0或1，为生物添加形如FindFlag{位}.{值}的标签。当玩家被攻击触发entity_hurt_player进度时，奖励函数以玩家为执行者，可以通过执行者附近的生物标签来匹配攻击者——因为攻击者生物身上带有其UUID的二进制位标签，而玩家受伤时攻击者就在附近，通过标签筛选即可唯一确定攻击者。这利用了计分板操作和标签系统的组合，实现了在无实体选择器参数的情况下定位特定实体的能力。

## 注意事项

- 索引号最大值为2^16，超过后需要重置，否则UUID会重复
- 标签数量较多（16位二进制需要32个标签），可能影响性能
- 需要确保生物创建时索引号不会冲突，且全局计分板需要持久化
- 常见误解：开发者通常认为检测生物攻击只能通过监听伤害事件或使用射线检测，或者认为无法在entity_hurt_player触发器中获取攻击者实体。
