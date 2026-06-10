---
id: t0375
title: "Galgame对话框系统"
title_en: "galgame_dialog_system"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202507/0/content"
source_type: "feature_article"
source_issue: "202507"
version_min: "1.21.5"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["data pack", "galgame", "dialog system", "event system", "storage"]
verified_in_game: false
---

## 核心洞见

利用数据包存储和函数调度，可以在原版Minecraft中实现完整的Galgame对话框系统，支持文本、立绘、选项、跳转等交互。

## 代码示例

```mcfunction
data modify storage minecraft:skapi.dbox reg.event.foo set value {"main":[{"type":"text","character":"NULL","text":"「嘛......要说也的确是好久没来了」"},{"type":"text","character":"roka","text":"「这就直接去志那都庄了？」"},{"type":"text","character":"NULL","text":"「是这个打算」"},{"type":"text","character":"roka","text":"「那我也一起走比较好吧，因为好久不见，再聊会吧」"}]}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该系统通过数据包中的存储（storage）来管理事件列表，每个事件列表是一个复合标签，包含多个事件（如文本、立绘、选项等）。播放时，通过函数递归调用和计时器（如延迟事件）控制事件顺序。文本事件使用打字动画（逐字显示），等待玩家按下空格键继续。立绘事件通过修改实体（如盔甲架或展示框）的NBT数据来加载、修改或移除立绘。选项事件通过检测玩家输入（W/S切换，空格确认）实现分支跳转。所有事件通过`function skdbox:dialog`启动，并支持多人并行使用。关键机制是事件列表的ID唯一性，以及通过`data modify`命令动态修改存储内容，实现流程控制（跳转、条件检查）。

## 注意事项

- 事件列表ID必须唯一，否则会覆盖或冲突
- 同一角色立绘不能同时加载多次，需要先移除再加载
- 选项数量过多时会导致显示重叠，需要调整间距设置
- 命令每行必须以反斜杠结尾，编辑时需批量处理
- 常见误解：开发者可能认为Minecraft数据包只能做简单的命令序列，无法实现复杂的交互式叙事系统，需要模组或插件支持。
