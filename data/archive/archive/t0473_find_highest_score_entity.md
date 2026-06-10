---
id: t0473
title: "最高分实体查找"
title_en: "find_highest_score_entity"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/highestscore"
source_type: "mcc_wiki"
source_issue: "questions/highestscore"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["scoreboard", "entity-selection", "comparison"]
verified_in_game: false
---

## 核心洞见

利用 scoreboard players operation 的 > 和 < 运算符，通过一个假玩家作为极值锚点，可以在一行命令内找出所有在线玩家中分数最高或最低的实体。

## 代码示例

```mcfunction
# 设置假玩家 #max 的分数为最小可能值（-2147483648）
scoreboard players set #max score -2147483648

# 对所有玩家执行：将 #max 的分数更新为当前玩家分数与 #max 中的较大者
execute as @a run scoreboard players operation #max score > @s score

# 找出分数等于 #max 的玩家（即最高分玩家）
execute as @a if score @s score = #max score run I have the highest score!

# 最低分版本：
# 设置假玩家 #min 的分数为最大可能值（2147483648）
scoreboard players set #min score 2147483648

# 对所有玩家执行：将 #min 的分数更新为当前玩家分数与 #min 中的较小者
execute as @a run scoreboard players operation #min score < @s score

# 找出分数等于 #min 的玩家（即最低分玩家）
execute as @a if score @s score = #min score run I have the lowest score!
```

## 文件结构

（待补充）

## 用法

在数据包中任意函数内按顺序执行这三条命令即可。无需额外文件结构，可直接在命令方块或函数中运行。

## 使用场景

['需要找出分数最高的玩家并给予奖励或触发事件', '需要找出分数最低的玩家进行惩罚或特殊处理', '在迷你游戏中确定排名第一或最后一名的玩家']

## 机制原理

scoreboard players operation 的 > 运算符会将左侧分数设置为左侧和右侧中的较大值（即 max 操作）。通过先将一个假玩家 #max 的分数初始化为最小可能值 -2147483648（32位有符号整数最小值），然后对所有目标实体执行 > 操作，每次迭代都会将 #max 更新为当前遇到的最高分数。最终 #max 的分数就是所有实体中的最高分。最后通过 if score 比较找出分数等于 #max 的实体即可。最低分同理，使用 < 运算符（min 操作）和最大可能值 2147483648。

## 注意事项

- 此方法仅适用于在线玩家或已加载的实体，不适用于离线玩家或未加载的实体
- 假玩家 #max 和 #min 的分数会被修改，如果需要在其他地方使用需注意冲突
- 如果有多个玩家并列最高/最低分，所有并列玩家都会被选中
