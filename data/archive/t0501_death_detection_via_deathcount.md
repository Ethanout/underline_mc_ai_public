---
id: t0501
title: "死亡计数检测"
title_en: "death_detection_via_deathcount"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/playerdeaths"
source_type: "mcc_wiki"
source_issue: "questions/playerdeaths"
version_min: "1.0"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["death detection", "scoreboard", "player event"]
verified_in_game: false
---

## 核心洞见

利用 deathCount 或 custom:time_since_death 分数变化即可简单可靠地检测玩家死亡或重生事件

## 代码示例

```mcfunction
# In chat / load function
scoreboard objectives add death deathCount

# Command blocks / tick function
execute as @a[scores={death=1..}] run say Death!
scoreboard players reset @a death

# Setup
scoreboard objectives add respawn custom:time_since_death

# Command blocks / tick function
execute as @a[scores={respawn=1}] run say I just respawned!
```

## 文件结构

（待补充）

## 用法

在加载函数或聊天中创建计分板目标，然后在 tick 函数或命令方块中执行检测命令。deathCount 检测死亡，time_since_death=1 检测重生。

## 使用场景

['需要简单检测玩家死亡事件（如播放死亡音效、广播消息）', '需要检测玩家重生事件（如重置状态、给予初始物品）', '不适用于需要在死亡位置执行命令的场景（因为 deathCount 在重生后更新）']

## 机制原理

deathCount 计分板目标会记录玩家死亡次数，当玩家死亡时该分数增加。通过 `scores={death=1..}` 选择器可以捕获分数≥1的玩家，即刚死亡的玩家。重置分数后，下次死亡会再次触发。类似地，`custom:time_since_death` 统计在死亡画面期间保持为0，点击重生后开始递增，因此 `scores={respawn=1}` 可以检测到刚重生的玩家。这两个计分板目标都是原版 Minecraft 内置的统计标准，无需额外数据包即可使用。

## 注意事项

- deathCount 检测在玩家重生后才会更新，因此无法在死亡位置执行命令
- time_since_death=1 检测重生时，需要确保 tick 函数在玩家重生后的第一个 tick 执行
- 适用于所有 Java Edition 版本
