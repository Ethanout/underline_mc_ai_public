---
id: t0469
title: "函数条件执行"
title_en: "conditional_execution_with_functions"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/functionconditions"
source_type: "mcc_wiki"
source_issue: "questions/functionconditions"
version_min: "1.12"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["conditional", "execute", "scoreboard", "function", "selector"]
verified_in_game: false
---

## 核心洞见

通过 execute if entity 或 execute store success 将选择器匹配或命令成功状态转化为条件，实现分支执行。

## 代码示例

```mcfunction
# 1.13+ 版本：条件基于选择器是否匹配
# 直接使用 execute if entity 前缀
# 注意 limit=1 用于性能优化
execute if entity @a[tag=TeamChange,limit=1] run say test
execute if entity @a[tag=TeamChange,limit=1] run function code:team_change
execute unless entity @a[tag=!Ready,limit=1] run function code:ready

# 1.13+ 版本：条件基于另一个命令是否成功
# 先设置虚拟计分板目标
scoreboard objectives add success_score dummy

# 使用 execute store success 存储命令成功状态到计分板
execute store success #success success_score if block 73 10 31 stone
execute if score #success success_score matches 1 run say Success!!
execute unless score #success success_score matches 1 run say Not success!!

# 1.12 版本：条件基于选择器是否匹配
# 使用 execute 前缀
execute @a[tag=TeamChange,c=1] ~ ~ ~ say test

# 使用 function 的 if/unless 参数
function code:team_change if @a[tag=TeamChange]
function code:ready unless @a[tag=!Ready]

# 1.12 版本：条件基于另一个命令是否成功
# 先设置虚拟计分板目标
scoreboard objectives add success_score dummy

# 为实体设置 SuccessCount 统计
stats entity @e[tag=main] set SuccessCount @s success_score

# 初始化分数
scoreboard players add @e[tag=main] success_score 0

# 执行条件命令
testforblock 73 10 31 stone *
execute @s[score_success_score_min=1] ~ ~ ~ say Stone found!
execute @s[score_success_score=0] ~ ~ ~ say Stone not found!

# 如果不在存储 SuccessCount 的实体上运行函数
execute @e[tag=main] ~ ~ ~ testforblock 73 10 31 stone *
execute @e[tag=main,score_success_score_min=1] ~ ~ ~ say Stone found!
execute @e[tag=main,score_success_score=0] ~ ~ ~ say Stone not found!
```

## 文件结构

- data/<namespace>/functions/<function_name>.mcfunction

## 用法

将上述命令写入 .mcfunction 文件，然后通过 /function <namespace>:<function_name> 调用。对于 1.13+ 版本，也可以直接使用 execute if entity 或 execute store success 前缀在其他命令中。

## 使用场景

['需要根据玩家是否拥有某个标签来执行不同逻辑（如检测玩家是否准备就绪）', '需要根据某个方块是否存在于特定位置来执行分支逻辑（如检测结构是否完整）', '需要根据另一个命令的执行结果来决定是否执行后续命令（如检测命令是否成功）']

## 机制原理

该技术利用 Minecraft 命令系统的条件执行机制。在 1.13+ 版本中，`execute if entity` 直接检查选择器是否匹配到实体，匹配则执行后续命令；`execute store success` 将命令的成功状态（0 或 1）存储到计分板，然后通过 `if score` 或 `unless score` 进行分支判断。在 1.12 版本中，`execute` 前缀和 `function` 的 `if`/`unless` 参数实现类似功能，而 `/stats` 和 `SuccessCount` 统计则用于捕获命令的成功状态。关键点在于将条件判断从命令本身分离出来，使得可以根据条件结果执行不同的命令序列。

## 注意事项

- 1.13+ 版本中，使用 `limit=1` 可以优化性能，让游戏在找到第一个匹配实体后停止搜索
- 1.12 版本中，使用 `/stats` 时要注意命令执行顺序对 `SuccessCount` 的影响：后续失败的命令会覆盖之前成功命令的 `SuccessCount` 值
- 1.12 版本中，`stats entity` 的第二个选择器由第一个选择器找到的实体评估，因此 `@s` 指向的是这些实体自身
- 1.12 版本中，需要确保分数已初始化（非 null），可以通过 `scoreboard players add ... 0` 实现
