---
id: t0513
title: "计分板单次触发"
title_en: "one_shot_trigger_with_scoreboard"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/runonce"
source_type: "mcc_wiki"
source_issue: "questions/runonce"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["scoreboard", "edge_detection", "trigger", "player_detection"]
verified_in_game: false
---

## 核心洞见

通过计分板存储上一tick的匹配状态，实现仅当条件从假变为真时执行一次命令

## 代码示例

```mcfunction
# In chat / load function
scoreboard objectives add matched dummy

# Command blocks / tick function
execute as @a[scores={matched=0},x=73,y=10,z=3,distance=..1] run say I just entered the area!
execute as @a store success score @s matched if entity @s[x=73,y=10,z=3,distance=..1]
```

## 文件结构

（待补充）

## 用法

将计分板初始化命令放入加载函数，将两条命令放入tick函数或命令方块循环中。第一条命令检测条件且matched=0时执行动作，第二条命令更新matched值。

## 使用场景

['检测玩家进入特定区域（如出生点、商店）时触发欢迎消息或奖励', '检测玩家切换游戏模式时执行初始化逻辑', '检测天气变化（如开始下雨）时触发全局事件']

## 机制原理

核心思想是使用计分板记录上一tick的匹配状态。第一条命令通过`scores={matched=0}`筛选出上一tick未匹配的玩家，再结合位置等条件检测当前tick是否匹配，若匹配则执行命令。第二条命令使用`execute store success`将条件检测的成功与否写入matched计分板，更新状态供下一tick使用。这样，只有条件从假变为真的那一tick会执行命令，后续tick因matched=1而不再触发。对于全局事件（如天气），使用虚拟玩家`#raining`的计分板实现类似效果。

## 注意事项

- 两条命令的执行顺序至关重要：先执行动作命令（检查matched=0），再更新matched值
- 此方法在Java版有效，Bedrock版需改用`scoreboard players set`方式（原文提供了替代方案）
- 对于全局事件，需使用虚拟玩家（以#开头的名称）的计分板
