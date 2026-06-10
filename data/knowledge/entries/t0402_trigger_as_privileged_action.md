---
id: t0402
title: "Trigger规避权限弹窗"
title_en: "trigger_as_privileged_action"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202506/5/content"
source_type: "feature_article"
source_issue: "202506"
version_min: "1.13"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["trigger", "dialog", "privilege-escalation", "ui-interaction"]
verified_in_game: false
---

## 核心洞见

使用 trigger 计分板可以绕过对话框按钮执行带权限命令时的二次确认弹窗，实现流畅交互

## 代码示例

```mcfunction
"actions":[{"label":"↑","width":50,"action":{"type":"run_command","command":"trigger box_operation set 1"}},{"label":"←","width":50,"action":{"type":"run_command","command":"trigger box_operation set 2"}},{"label":"↓","width":50,"action":{"type":"run_command","command":"trigger box_operation set 3"}},{"label":"→","width":50,"action":{"type":"run_command","command":"trigger box_operation set 4"}}]

execute as @a if score @s box_operation matches 1.. run function x:gameplay/operation
scoreboard players enable @a box_operation

# x/function/gameplay/operation:
execute unless score @s box_success matches 1 if score @s box_operation matches 1 run function x:operation/up
execute unless score @s box_success matches 1 if score @s box_operation matches 2 run function x:operation/left
execute unless score @s box_success matches 1 if score @s box_operation matches 3 run function x:operation/down
execute unless score @s box_success matches 1 if score @s box_operation matches 4 run function x:operation/right
execute if score @s box_operation matches 5 run function x:gameplay/start
function x:gameplay/success
scoreboard players set @s box_operation 0
function x:dialog/level
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Minecraft 中，对话框按钮的 action 类型为 run_command 时，如果命令需要权限（如 /setblock、/data 等），会弹出二次确认弹窗，这在需要频繁操作的小游戏中不可接受。trigger 计分板是一种特殊计分板准则，玩家可以用 /trigger 命令修改其值（无需权限），数据包在 tick 函数中轮询该计分板的值变化来触发实际逻辑。文章将按钮命令设为 /trigger box_operation set <value>，然后在 tick 中检测 @a 的 box_operation 分数，执行对应操作后重置为 0。这样按钮只需执行无权限的 /trigger 命令，实际逻辑由数据包在后台处理，完全避免弹窗。

## 注意事项

- trigger 计分板需要先执行 /scoreboard players enable 才能被玩家触发，否则 /trigger 会失败
- 必须确保 tick 函数中轮询后重置计分板，否则同一操作会被重复执行
- 多个玩家同时操作时，需要按玩家分别处理，避免混淆
- 常见误解：开发者可能认为对话框按钮只能直接执行命令，但带权限的命令会触发二次确认弹窗，破坏游戏体验
