---
id: t0515
title: "标签单次触发"
title_en: "one_shot_trigger_with_tag"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/runonce"
source_type: "mcc_wiki"
source_issue: "questions/runonce"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["tag", "edge_detection", "trigger", "player_detection", "cross_platform"]
verified_in_game: false
---

## 核心洞见

通过每tick先清除再添加标签，利用标签的瞬态存在性实现边缘检测，无需计分板且跨版本兼容

## 代码示例

```mcfunction
# Command blocks / tick function
execute as @a[x=73,y=10,z=3,distance=..1,tag=!alreadyMatched] run say I just entered the area!
tag @a[tag=alreadyMatched] remove alreadyMatched
tag @a[x=73,y=10,z=3,distance=..1] add alreadyMatched
```

## 文件结构

（待补充）

## 用法

将三条命令按顺序放入tick函数或命令方块循环中。第一条命令检测当前匹配且上一tick未匹配的玩家并执行动作，后两条命令更新标签状态。

## 使用场景

['需要跨Java版和Bedrock版兼容的边缘检测', '快速实现简单的进入/离开区域检测，无需创建计分板', '临时性检测需求，不想引入计分板或进度系统']

## 机制原理

利用标签的瞬态特性实现边缘检测。每tick执行三条命令：第一条检测当前匹配选择器且没有`alreadyMatched`标签的玩家（即上一tick未匹配），执行动作；第二条清除所有玩家的`alreadyMatched`标签；第三条给当前匹配的玩家添加标签。这样，标签`alreadyMatched`表示玩家在上一tick匹配了选择器。通过`tag=!alreadyMatched`筛选出上一tick未匹配的玩家，结合当前匹配条件，即可检测到条件从假变为真的瞬间。此方法不需要计分板，且原文声称在Bedrock版也有效。

## 注意事项

- 三条命令的执行顺序必须严格保持：先执行动作，再清除标签，最后添加标签
- 标签名称可自定义，但需保持一致
- 此方法在Bedrock版也有效（原文声称）
- 如果同一tick内玩家同时满足进入和离开条件（极低概率），可能产生竞态条件
