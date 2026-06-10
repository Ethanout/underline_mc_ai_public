---
id: t0471
title: "计分板定时器"
title_en: "scoreboard_timer"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/blockdelay"
source_type: "mcc_wiki"
source_issue: "questions/blockdelay"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["scoreboard", "timer", "delay", "fake_player"]
verified_in_game: false
---

## 核心洞见

使用 dummy 计分板配合 `execute if score` 或 `store success score`，可以实现精确到 tick 的延时，支持玩家独立计时和全局计时。

## 代码示例

```mcfunction
# 初始化
scoreboard objectives add timer dummy

# 每 tick 执行的命令（循环命令方块/tick函数）
scoreboard players add @a timer 1

# 对每个玩家：当 timer 达到100时执行命令并重置
execute as @a[scores={timer=100}] run say This command has 5 seconds delay.
scoreboard players reset @a[scores={timer=100..}] timer

# 全局 fake player 计时器
scoreboard players add $FakePlayer timer 1
execute if score $FakePlayer timer matches 120 run say This command has 6 seconds delay.
execute if score $FakePlayer timer matches 120.. run scoreboard players reset $FakePlayer timer

# 使用 store success score 实现单命令计时+重置（仅Java版）
execute as @a[scores={timer=101..}] store success score @s timer run say This command has 5 seconds delay.
execute if score $FakePlayer timer matches 121.. store success score $FakePlayer timer run say This command has 6 seconds delay.

# 动态延时：设置目标值并与玩家比较
scoreboard players set #delay timer 300
execute as @a if score @s timer >= #delay timer store success score @s timer run say Custom delay command.
```

## 文件结构

（待补充）

## 用法

构建完数据包即可在游戏内测试效果。需要有一个循环命令方块或 tick 函数来每 tick 增加计分板值，然后通过 `execute if score` 检测达到目标值的实体/假玩家来执行命令。

## 使用场景

['需要为每个玩家独立计时（如冷却时间、技能CD）', '需要全局定时器（如每10秒执行一次全局事件）', '需要动态可配置的延时（通过设置假玩家分数作为目标值）']

## 机制原理

创建一个 `dummy` 类型的计分板目标，每 tick 对所有目标实体（如 `@a`）或假玩家（如 `$FakePlayer`）的分数加 1。当分数达到预设值时，通过 `execute if score` 检测并执行命令，然后重置分数。使用 `store success score` 技巧可以将命令执行和分数重置合并为一条命令：命令执行成功时 `store success` 会将返回值（1）写入分数，从而覆盖原分数实现重置。假玩家（fake player）是计分板中不存在的玩家名，用于存储全局变量，不会影响真实玩家。

## 注意事项

- 使用 `store success score` 时，如果命令因条件不满足而未执行，分数不会被重置，可能导致计时不精确
- 假玩家名称建议以 `#` 或 `$` 开头，避免与真实玩家冲突
- 每 tick 增加分数的方式在大量实体时可能造成性能开销
- 此方法在 Java 1.13+ 和 Bedrock 版均适用（但 `store success score` 仅 Java 版可用）
