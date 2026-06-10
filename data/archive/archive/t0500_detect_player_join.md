---
id: t0500
title: "检测玩家加入"
title_en: "detect_player_join"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/playerjoin"
source_type: "mcc_wiki"
source_issue: "questions/playerjoin"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["player_detection", "join_event", "scoreboard", "advancement", "tag"]
verified_in_game: false
---

## 核心洞见

利用 tag 检测首次加入，利用 leave_game 计分板检测重新加入，可合并为统一检测系统

## 代码示例

```mcfunction
# 首次加入 - 标签法
execute as @a[tag=!init] run tellraw @a ["",{"selector":"@s"},{"text":" just logged in for the first time!"}]
tag @a[tag=!init] add init

# 首次加入 - 进度法
# advancement example:first_join
{
  "criteria": {
    "requirement": {
      "trigger": "minecraft:tick"
    }
  },
  "rewards": {
    "function": "example:first_join"
  }
}

# function example:first_join
tellraw @a [{"selector":"@s"}," just logged in for the first time!"]

# 重新加入 - Java版
scoreboard objectives add leave minecraft.custom:minecraft.leave_game
execute as @a[scores={leave=1..}] run tellraw @a ["",{"selector":"@s"},{"text":" just came back to us!"}]
scoreboard players reset @a[scores={leave=1..}] leave

# 重新加入 - 基岩版
scoreboard objectives add online dummy
scoreboard players add @a online 1
scoreboard players add .total online 1
scoreboard players operation @a online -= .total online
execute as @a[scores={online=..-1}] run say I relogged!
scoreboard players operation @a online = .total online

# 合并检测 - Java版（方法1）
tag @a[scores={leave=1..}] remove init
execute as @a[tag=!init] run say I relogged!
tag @a[tag=!init] add init
scoreboard players set @a[scores={leave=1..}] leave 0

# 合并检测 - Java版（方法2，精简版）
scoreboard objectives add leave custom:leave_game
execute as @a unless score @s leave = @s leave store success score @s leave run tellraw @a [{"selector":"@s"}," just logged in for the first time!"]
execute as @a unless score @s leave matches 1 store success score @s leave run tellraw @a [{"selector":"@s"}," just came back to us!"]

# 合并检测 - 基岩版
scoreboard objectives add online dummy
scoreboard players add @a online 1
scoreboard players add .total online 1
scoreboard players operation @a online -= .total online
execute as @a[scores={online=..-1}] run say I rejoined
scoreboard players operation @a online = .total online
execute as @a[tag=!init] run say I joined for the first time
tag @a[tag=!init] add init
```

## 文件结构

- data/example/advancements/first_join.json
- data/example/functions/first_join.mcfunction

## 用法

构建完数据包即可在游戏内测试效果。首次加入时自动触发，重新加入时自动触发。标签法直接在命令方块或函数中运行即可。

## 使用场景

['欢迎消息：玩家首次加入或重新加入时发送欢迎信息', '初始化系统：为新玩家设置初始物品、分数、标签等', '玩家统计：记录玩家加入次数、在线时长等数据']

## 机制原理

首次加入检测利用新玩家没有任何数据（标签、分数、进度）的特点。标签法通过检测 `tag=!init` 的玩家（即没有 init 标签的玩家）来识别新玩家，执行操作后立即添加标签，防止重复触发。进度法利用 tick 触发器，每 tick 检查一次，新玩家没有该进度时会自动获得并触发奖励函数。

重新加入检测利用 `minecraft.custom:minecraft.leave_game` 计分板目标，玩家离开游戏时该分数自动增加。由于离线玩家无法被目标选择器选中，只能在玩家重新加入时检测到分数变化（`scores={leave=1..}`），然后重置分数。

合并检测的核心思路是：将首次加入和重新加入统一处理。方法1通过先移除 init 标签再重新添加来合并逻辑。方法2利用 `execute store success` 的特性：`unless score @s leave = @s leave` 对无分数的玩家总是成功（因为比较两个不存在的分数会返回 false，即条件成立），`store success` 将成功值（1）存入分数，所以新玩家分数被设为1；重新加入的玩家分数因离开事件已变为1+，`unless score @s leave matches 1` 条件成立，再次 `store success` 将分数重置为1。

## 注意事项

- 示例中使用 tellraw 命令，在 1.21.5+ 中 tellraw 语法已变更，需要相应更新
- leave_game 方法统计的是退出游戏次数，而非加入服务器次数，因为分数在玩家离开时增加，但离线玩家无法被目标选择器选中
- 基岩版使用 fake player 计分板方法时，如果每 tick 运行，约3年后会因整数溢出失效；改为每秒运行一次则可维持约60年
- 基岩版合并检测方法与其他两种方法本质相同，没有额外变化
