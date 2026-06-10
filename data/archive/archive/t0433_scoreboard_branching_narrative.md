---
id: t0433
title: "计分板分支叙事"
title_en: "scoreboard_branching_narrative"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202507/1/content"
source_type: "feature_article"
source_issue: "202507"
version_min: "1.20"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["scoreboard", "branching", "narrative", "function", "dialog"]
verified_in_game: false
---

## 核心洞见

利用计分板分数作为状态标识，结合 return run 实现函数式分支叙事，支持多段对话、选项跳转和上下翻页，无需复杂的状态机框架。

## 代码示例

```mcfunction
# 主函数示例
execute if score @s dialog_phase matches 1 run return run function icu:npcs/test/1
execute if score @s dialog_phase matches 2 run return run function icu:npcs/test/2
execute if score @s dialog_phase matches 101 run return run function icu:npcs/test/3

# 选项分支函数示例
execute if score @s dialog_choose matches 1 run return run function icu:npcs/test/choose1
execute if score @s dialog_choose matches 2 run return run function icu:npcs/test/choose2
# 设置对话内容...
data modify storage icu:dialog dialog.name set value "§a霞露零"
data modify storage icu:dialog dialog.char set value "xll"
data modify storage icu:dialog dialog.dialog set value "§f还有什么事吗？"
data modify storage icu:dialog dialog.choose1 set value "这是什么"
data modify storage icu:dialog dialog.choose2 set value "没事了"
data modify storage icu:dialog dialog.choose3 set value ""
data modify storage icu:dialog dialog.choose4 set value ""
data modify storage icu:dialog dialog.sound set value "playsound entity.experience_orb.pickup ambient @s ~ ~ ~ 5 1.5"
function icu:dialog/main
tag @s add dialog_not_up
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术使用两个计分板：dialog_phase 控制对话阶段（主流程），dialog_choose 控制选项分支。主函数通过 execute if score matches 检测 dialog_phase 并 return run 对应函数。选项点击时设置 dialog_choose 为 1-4，数据包自动检测并跳转到当前阶段函数，函数内再根据 dialog_choose 跳转到分支函数。分支函数可修改 dialog_phase 以改变后续流程（如跳转到 100 表示选项后的新阶段）。上下翻页通过 dialog_not_up/dialog_not_down 标签控制，点击按钮时增减 dialog_phase。这种设计将叙事逻辑完全分散到独立函数中，每个函数只负责一段对话，通过 return run 实现高效跳转，避免了长函数和嵌套问题。

## 注意事项

- dialog_phase 必须从 1 开始，否则 matches 0 可能意外触发
- 选项跳转后必须手动设置 dialog_phase，否则点击下一步会回到原流程
- dialog_not_up/dialog_not_down 标签需在每次对话函数中正确设置，否则翻页逻辑混乱
- 多个玩家同时对话时计分板会冲突，需使用 @s 或单独计分板目标
- 常见误解：开发者可能认为实现分支叙事需要编写大量 if-else 链或使用外部工具生成命令，或者认为状态管理必须依赖 NBT 存储。
