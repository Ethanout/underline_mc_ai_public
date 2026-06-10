---
id: t0245
title: "触发器做自定义命令"
title_en: "trigger_objective_custom_command"
layer: technique
source_url: "https://datapack.wiki/wiki/nbt-scoreboards/scoreboards"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.13"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["scoreboard", "trigger", "custom_command", "ui"]
verified_in_game: false
---

## 核心洞见

利用 trigger 记分板目标，非 OP 玩家也能通过 /trigger 命令与数据包交互，实现类似自定义命令的 UI。

## 代码示例

```mcfunction
scoreboard objectives add option trigger
scoreboard players enable @a option
# 玩家可以执行：
# /trigger option  (设置分数为1)
# /trigger option set 5
# /trigger option add 3
# 重置禁用：
# scoreboard players reset @a option
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

trigger 类型的记分板目标允许任何玩家（无论 OP 状态）使用 /trigger 命令修改自己的分数。通过 enable 子命令为玩家启用目标后，玩家可以执行 /trigger <objective> [add|set] <value>。数据包可以检测分数变化并执行相应逻辑，从而创建简单的菜单或选项系统。这避免了赋予玩家 OP 权限的安全风险，同时提供了玩家与数据包交互的入口。

## 注意事项

- 玩家使用 trigger 后目标自动禁用，需重新 enable 才能再次使用
- trigger 只能修改自己的分数，不能操作其他玩家
- 需要配合其他命令（如 execute if score）来响应分数变化
- 常见误解：开发者可能认为只有 OP 玩家才能执行自定义命令，或需要复杂的聊天解析系统。
