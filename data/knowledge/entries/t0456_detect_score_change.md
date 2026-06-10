---
id: t0456
title: "分数变化检测"
title_en: "detect_score_change"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/changeofscore"
source_type: "mcc_wiki"
source_issue: "questions/changeofscore"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["scoreboard", "detection", "comparison", "tick"]
verified_in_game: false
---

## 核心洞见

通过存储上一刻的分数值并与当前值比较，可以非破坏性地检测分数变化及其增减方向。

## 代码示例

```mcfunction
# 破坏性方法：检测分数变化后立即重置
# 适用于可写目标（如 dummy），不适用于只读目标（如 health）
execute as @a[scores={deaths=1..}] run say I died :(
scoreboard players reset @a[scores={dead=1..}] deaths

# 非破坏性方法：使用第二个 dummy 目标存储上一刻的值
# 假设已在实体上运行，有 deaths 目标和 tmp 目标
execute unless score @s tmp = @s deaths run say My score has changed in the last tick!
scoreboard players operation @s tmp = @s deaths

# 非破坏性方法：检测增减方向（以 health 为例）
# 需要 health 和 health.tmp 两个目标
execute as @a unless score @s health = @s health.tmp run say My health has changed!
execute as @a if score @s health < @s health.tmp run say My health has decreased!
execute as @a if score @s health > @s health.tmp run say My health has increased!
execute as @a run scoreboard players operation @s health.tmp = @s health
```

## 文件结构

（待补充）

## 用法

破坏性方法：在 tick 函数或命令方块中运行检测命令，分数变化后自动触发效果并重置。非破坏性方法：在 tick 函数中运行比较和更新命令，每次 tick 都会检测变化。

## 使用场景

['检测玩家死亡（破坏性方法，重置死亡分数）', '检测玩家生命值变化（非破坏性方法，因为 health 是只读目标）', '检测玩家饥饿值、经验值等只读分数的变化方向（增加或减少）']

## 机制原理

破坏性方法利用 scoreboard players reset 将分数归零，使得下一次变化时分数再次变为非零值，从而触发检测。这种方法简单高效，但会丢失分数历史值。非破坏性方法通过创建一个额外的 dummy 目标（如 tmp）来存储上一 tick 的分数值，然后使用 execute unless score 比较当前值与存储值是否相等。如果不相等，说明分数发生了变化。通过 if score < 和 if score > 还可以判断变化方向（增加或减少）。最后通过 scoreboard players operation 将当前值复制到存储目标中，为下一 tick 的比较做准备。这种方法不修改原始分数，适用于只读目标（如 health、hunger）或需要保留分数值的场景。

## 注意事项

- 破坏性方法不适用于只读目标（如 Health、Hunger），因为这些目标无法被修改
- 非破坏性方法需要额外的 dummy 目标来存储上一刻的值
- 非破坏性方法需要在每个 tick 都运行更新命令，否则比较会失效
- 两种方法在 Java 和 Bedrock 版本中均适用
