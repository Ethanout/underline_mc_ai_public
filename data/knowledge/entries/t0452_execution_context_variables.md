---
id: t0452
title: "上下文变量完整机制"
title_en: "execution_context_variables"
layer: concept
source_url: "data/archive/inbox/20260606_140955.md"
source_type: "manual"
source_issue: ""
version_min: "1.14"
version_max: ""
wiki_covers_this: false
confidence: high
tags: ["execute", "上下文", "executor", "position", "anchor", "store", "分支栈", "context"]
verified_in_game: false
---

## 核心洞见

上下文变量是依附于命令执行环境的隐式局部变量，切换成本极低（1~3单位），是传递坐标、执行者等临时数据的最优选择，远优于将数据序列化进 NBT。

## 代码示例

```mcfunction
# 1. 执行者 — 切换 @s 指向的实体
execute as @e[type=pig] run function ns:pig_logic
execute on attacker run say "I was hit!"
summon pig ~ ~ ~ {Tags:["new_pig"]} run function ns:init_pig

# 2. 执行方位 — 细粒度覆盖位置/维度/朝向
execute at @s positioned ~ 100 ~ rotated 180.0 0.0 in the_nether run function ns:do_something
execute facing entity @p feet run tp ^ ^ ^1

# 3. 基准 (Anchor) — 控制局部坐标的起点
execute anchored eyes positioned ^ ^ ^5 run particle flame    # 从眼睛向前5格
execute anchored feet positioned ^ ^ ^5 run particle soul_fire # 从脚底向前5格

# 4. Store 标记 — 返回值指针
# 被调用方（通用函数，不关心结果存哪）：
execute store result score #math_temp <namespace> run ...
return run scoreboard players get #math_temp <namespace>
# 调用方（由 store 决定结果落点）：
execute store result score @s player_score run function <namespace>:math/get_random

# 5. 分支栈 — 多目标展开 + 安全限制
execute as @e[type=zombie] as @e[type=skeleton] run say "Hi"
# 版本适配（1.21.11 前后命名不同）：
# [1.21.10 及之前]
gamerule maxCommandChainLength 65536
gamerule maxCommandForkCount 65536
# [1.21.11 至今]
gamerule max_command_sequence_length 65536
gamerule max_command_forks 65536
```

## 文件结构

（上下文变量是执行环境的内置机制，无需独立文件）

## 用法

构建完数据包即可在游戏内测试效果。

## 使用场景

- 用 `as` + `at` 切换执行环境，实现"以某实体身份在某位置执行逻辑"
- 用 `store` 将函数返回值写回调用方，实现通用工具函数
- 用上下文传递坐标，而不是把坐标序列化成 NBT 再反序列化
- 调整 `max_command_forks` 应对大量实体同时处理的场景

## 机制原理

上下文变量本质上是依附于命令执行环境（Execution Context）的隐式局部变量，随执行环境的建立而创建，随函数调用链的继承而传递，无序列化开销。

**执行者 (Executor)**：`@s` 所指向的物理实体。若执行者在函数流中途被 `kill`，直到当前tick结束前 `@s` 依然保留原实体的上下文属性（UUID、分数）。当实体被kill标记删除后，除了`@s`，`@a`（仅玩家），execute on 系列，`$execute as $(uuid_hex)`之外，其他手段均不可选中。

**执行方位 (Position / Dimension / Rotation)**：`at` 同时重写位置、维度和朝向；`positioned` / `rotated` / `in` / `facing` 是细粒度单独修改某一项。上下文方位会被后续调用的函数自动继承，极度推荐用上下文传递坐标而非转成 NBT。

**基准 (Anchor)**：局部枚举变量，默认 `feet`，决定 `^ ^ ^` 和 `facing` 视线追踪的起点高度。
- 执行 `positioned ^ ^ ^` 时：若当前 anchor 为 `eyes`，先读取 `@s` 眼睛高度 h，将上下文 y 坐标加上 h，然后**强制将 anchor 重置回 `feet`**，最后输出局部坐标计算结果。
- 执行 `positioned ~ ~ ~` 时：**仅将 anchor 重置为 `feet`**，不做任何额外操作，绝对不会对 y 加眼高。

**Store 标记 (Return Pointer)**：`store` 本质是在上下文中压入一个"返回地址指针"。被调用的通用函数只需 `return` 结果，系统顺着上下文指针自动写回调用方指定的位置，实现调用方/被调用方解耦。

**分支栈 (Branching Stack)**：`execute as @e[...]` 等多目标命令会在栈中创建多条执行分支，原版执行顺序为**宽度优先（BFS）**。受两个 gamerule 限制：
- `max_command_sequence_length`（1.21.11 前叫 `maxCommandChainLength`）：单 tick 内最大命令总行数，最小值为 0
- `max_command_forks`（1.21.11 前叫 `maxCommandForkCount`）：单条命令允许展开的最大分支数，最小值为 0

## 注意事项

- `positioned ^ ^ ^` 会重置 anchor，`positioned ~ ~ ~` 也会重置 anchor，两者行为差异微妙
- 执行者被 kill 后上下文仍存活，是难以排查的 bug 来源
- gamerule 命名在 1.21.11 发生了破坏性重命名，需要做版本兼容处理
- 分支栈默认上限较低，大量实体并发处理时需要主动调高 `max_command_forks`
