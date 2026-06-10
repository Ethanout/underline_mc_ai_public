---
id: t0503
title: "基岩版死亡检测"
title_en: "bedrock_death_detection_via_tag"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/playerdeaths"
source_type: "mcc_wiki"
source_issue: "questions/playerdeaths"
version_min: "1.0"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["bedrock", "death detection", "tag", "selector trick"]
verified_in_game: false
---

## 核心洞见

利用 @a 和 @e 选择器对死亡玩家的不同行为，通过标签差值检测基岩版玩家死亡

## 代码示例

```mcfunction
/tag @a add dead
/tag @e[type=player] remove dead
/scoreboard players add @a[tag=dead,tag=!still_dead] deathCount 1
/tag @a add still_dead
/tag @e[type=player] remove still_dead
```

## 文件结构

（待补充）

## 用法

在命令方块或函数中按顺序执行这些命令。需要先创建一个 dummy 类型的计分板 `deathCount`。每次执行时，死亡玩家的 deathCount 会增加1。

## 使用场景

['基岩版中检测玩家死亡事件', '需要统计玩家死亡次数', '不适用于需要精确死亡位置或重生事件的场景']

## 机制原理

基岩版中，`@a` 选择器包含所有玩家（包括死亡状态的），而 `@e[type=player]` 只选择存活的玩家实体。通过先给所有玩家添加 `dead` 标签，然后从存活玩家中移除该标签，剩下的带有 `dead` 标签的玩家就是死亡玩家。再用 `still_dead` 标签避免重复计数：先给所有玩家加 `still_dead`，再从存活玩家中移除，这样死亡玩家同时有 `dead` 和 `!still_dead` 标签，只计一次。这种方法利用了基岩版选择器的行为差异，是原版命令的巧妙变通。

## 注意事项

- 仅适用于基岩版（Bedrock Edition）
- 需要先创建 dummy 计分板 `deathCount`
- 命令必须按指定顺序执行
- 此方法由社区发现，非官方特性
