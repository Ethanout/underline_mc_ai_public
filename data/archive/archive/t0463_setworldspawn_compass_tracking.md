---
id: t0463
title: "世界出生点追踪"
title_en: "setworldspawn_compass_tracking"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/compasstoplayer"
source_type: "mcc_wiki"
source_issue: "questions/compasstoplayer"
version_min: "1.0"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["compass", "world spawn", "setworldspawn", "tracking"]
verified_in_game: false
---

## 核心洞见

通过移动世界出生点（setworldspawn）使所有指南针指向同一目标，但会改变玩家重生位置，需额外处理重生逻辑。

## 代码示例

```mcfunction
execute at @p[<your target player>] run setworldspawn ~ ~ ~
```

## 文件结构

（待补充）

## 用法

在命令方块或函数中执行上述命令，将世界出生点移动到目标玩家位置，所有指南针将指向该位置。

## 使用场景

['简单场景下让所有玩家指向同一目标（如队长位置）', '仅需临时指向，不关心重生点变化时使用', '不适合需要多目标指向或保留重生点的场景']

## 机制原理

原版指南针默认指向世界出生点（world spawn）。通过 setworldspawn 命令可以将世界出生点移动到任意位置，从而让所有指南针指向该位置。此方法简单但全局生效，且会改变玩家死亡后的重生位置（除非玩家已设置个人床重生点）。为避免重生点被移动导致的问题，需要额外检测玩家死亡并传送至正确重生点。

## 注意事项

- 此方法仅能指向一个目标，且全局可见
- 移动世界出生点会影响玩家重生位置，需配合死亡检测（如 Java 版使用 custom:time_since_last_death 计分板）处理重生逻辑
- 跨版本兼容：Java 和 Bedrock 均支持
