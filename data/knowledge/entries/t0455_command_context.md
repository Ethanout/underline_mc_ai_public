---
id: t0455
title: "命令上下文"
title_en: "command_context"
layer: concept
source_url: "https://zh.minecraft.wiki/w/命令上下文"
source_type: "manual"
source_issue: ""
version_min: "1.13"
version_max: ""
wiki_covers_this: true
confidence: high
tags: ["命令上下文", "execute", "function", "执行位置", "执行锚点", "静态参数", "动态参数"]
verified_in_game: false
---

## 核心洞见

命令上下文是命令执行时的环境变量集合，包含 6 个核心参数。`function` 调用时会**继承**调用处的上下文，这是 `@s`、`~ ~ ~`、`^ ^ ^` 在函数内能正常工作的基础。

## 代码示例

```mcfunction
# 函数继承调用处上下文——进入 ns:process_cow 后 @s 始终指向那头牛
execute as @e[type=cow] at @s run function ns:process_cow

# tick/load 函数标签的默认上下文（执行者实体为空）：
# @s 无效，~ ~ ~ 以世界出生点为原点
# 所以 tick 函数里要操作玩家，必须先切换执行者
execute as @a at @s run function ns:player_tick

# Java 版：at 设置的位置是静态快照
# 哪怕 process_sheep 内部用 /tp 移动了羊，
# 后续 ~ ~ ~ 的原点不会随之改变
execute as @e[type=sheep] at @s run function ns:process_sheep

# 执行锚点影响 ^ ^ ^ 的原点
execute anchored eyes run function ns:from_eyes
# 此时 ^ ^ ^ 的原点在眼睛高度
# 但 positioned ^ ^ ^ 之后锚点自动重置为 feet
execute anchored eyes positioned ^ ^ ^ run function ns:foo
# foo 内的 ^ ^ ^ 原点已回到脚部（feet）
```

## 文件结构

（概念性知识，适用于所有 .mcfunction，无特定文件结构）

## 用法

理解性概念，无调用方式。实际写函数时的两个核心用途：
- 以某实体执行一批命令 → `execute as @e[...] at @s run function ns:foo`，`foo` 内直接用 `@s`，无需重复选择器
- `tick` / `load` 函数标签内无执行者实体，需先 `execute as @a at @s run ...` 切换

## 使用场景

- 理解 `@s` 为什么在函数内有效：函数继承调用者的执行者
- 无实体射线检测（entityless raycast）能成立的原因：函数间位置和朝向不丢失
- 排查"命令方块和函数行为不一致"：命令方块无执行者实体、朝向固定 (0,0)
- 理解 `schedule` 不继承上下文：计划的函数以服务端默认上下文执行

## 机制原理

**6 个核心参数**：

| 参数 | 作用 | 受哪些子命令影响 |
|------|------|----------------|
| 执行者 | `@s` 指向谁 | `as`、`on`、`summon` |
| 执行位置 | `~ ~ ~` 的原点 | `at`、`positioned`、`align`、`in` |
| 执行朝向 | `^ ^ ^` 的朝向，`~ ~` 相对旋转 | `at`、`rotated`、`facing` |
| 执行维度 | 坐标在哪个维度 | `at`、`in` |
| 执行锚点 | `^ ^ ^` 原点在脚还是眼（仅 Java 版） | `anchored` |
| 执行输出反馈 | 接收命令的成功/结果值 | `store`（一般不需关注） |

**函数继承规则**：`/function` 执行函数时，函数内所有命令继承调用处的全部上下文参数（输出反馈除外）。

**Java 版 vs 基岩版关键差异——静态 vs 动态**：
- Java 版：上下文参数是**静态快照**。`at @e[type=sheep]` 确定位置后，即使函数内部移动了那只羊，后续 `~ ~ ~` 的原点不变
- 基岩版：`at`、`positioned as`、`rotated as` 设置的参数是**动态**的，实时从实体获取，函数中途移动实体会影响后续 `~ ~ ~`

**执行锚点（Java 版专有）**：
- 默认为 `feet`（脚部），`^ ^ ^` 原点在执行位置本身
- `anchored eyes` 将 `^ ^ ^` 原点抬到执行者眼部（执行位置 Y + 眼高，玩家约 +1.62）
- `positioned <坐标>` 会**自动重置锚点为 feet**——这是 raycast 双锚点写法的底层原因：`anchored eyes positioned ^ ^ ^ anchored feet` 中第二个 `anchored feet` 在新版本中实际上是多余的，`positioned` 已经帮你重置了

**各来源默认上下文**：

| 来源 | 执行者实体 | 执行位置 | 执行朝向 |
|------|-----------|---------|---------|
| 服务器控制台 | 无 | 世界出生点 | (0,0) |
| tick/load 函数标签 | 无 | 世界出生点 | (0,0) |
| 玩家聊天栏 | 玩家 | 玩家位置 | 玩家朝向 |
| 命令方块 | 无 | 方块正中心 | 方块朝向(Java) / (0,0)(BE) |
| 进度奖励函数 | 触发进度的玩家 | 玩家位置 | 玩家朝向 |

## 注意事项

- `schedule` 计划的函数**不继承**调用时的上下文，以服务端默认上下文执行（无执行者、位置在世界出生点）
- Java 版函数内命令权限等级上限为 2，即使 `/function` 以更高权限执行也无效
- 基岩版：若动态参数依赖的实体已消失，执行位置默认 `(0,0,0)`，执行维度为空，可能导致 `/schedule` 的函数执行失败
- 执行锚点仅影响 `^ ^ ^`、`execute facing` 和 `/tp ... facing` 的计算起点，不影响 `~ ~ ~`
