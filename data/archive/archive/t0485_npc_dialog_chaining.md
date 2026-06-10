---
id: t0485
title: "NPC对话链"
title_en: "npc_dialog_chaining"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/npc"
source_type: "mcc_wiki"
source_issue: "questions/npc"
version_min: "1.16.0"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["npc", "dialogue", "bedrock", "command", "interaction"]
verified_in_game: false
---

## 核心洞见

通过隐藏NPC和/dialogue命令，可以在基岩版中实现NPC对话的多级分支，突破单个NPC对话的限制。

## 代码示例

```mcfunction
# 第一个NPC（玩家交互的NPC），对话为“Do you want a challenge?”
# 按钮模式，文本为“Yes”
dialogue open @e[tag=npc.confirm,type=npc] @initiator

# 按钮模式，文本为“No”
# 空操作，因为按下任何按钮时，NPC对话都会关闭。

# 第二个NPC（隐藏在地下），标签为npc.confirm，对话为“Are you sure?”
# 按钮模式，文本为“Yes”
execute at @initiator run summon zombie
say here is your challenge

# 按钮模式，文本为“No”
# 空操作，因为按下任何按钮时，NPC对话都会关闭。
```

## 文件结构

（待补充）

## 用法

构建完数据包即可在游戏内测试效果。需要手动创建两个NPC：第一个NPC（玩家可见）设置对话和按钮，第二个NPC（隐藏）设置后续对话和命令，并通过/dialogue命令链接。

## 使用场景

['创建多分支对话的NPC任务系统，如询问玩家是否接受挑战', '实现复杂的NPC交互流程，如商店、任务选择等', '当单个NPC对话字符数限制（307字符）不足时，通过链式对话扩展内容']

## 机制原理

基岩版NPC的对话系统默认只支持单个NPC的固定对话和命令。通过/dialogue命令，可以在一个NPC的按钮动作中打开另一个NPC的对话界面，实现对话链。关键点是：第二个NPC需要隐藏（如在地下）并带有唯一标签（如npc.confirm），以便/dialogue命令通过目标选择器定位。当玩家点击第一个NPC的按钮时，/dialogue命令会打开第二个NPC的对话，显示新的选项和命令。每个NPC的对话独立，但通过命令串联，形成多级分支。注意：@initiator变量用于引用与NPC交互的玩家，命令以NPC为执行者和位置运行。

## 注意事项

- 此技术仅适用于基岩版（Bedrock Edition），不适用于Java版
- NPC对话字符数上限为307字符
- 对话中不能使用目标选择器（如@p会显示为文本而非玩家名）
- 命令以NPC为执行者和位置运行，使用@initiator引用交互玩家
- 隐藏NPC需要确保玩家无法看到或意外交互，建议埋在地下或使用屏障
- 每个NPC需要不同的标签来唯一标识，避免/dialogue命令定位错误
