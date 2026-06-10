---
id: t0234
title: "对话框JSON格式"
title_en: "dialog_system_json_format"
layer: technique
source_url: "https://datapack.wiki/wiki/files/dialogs"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.21.2"
version_max: ""
wiki_covers_this: true
confidence: low
tags: ["dialog", "ui", "json", "command", "interaction"]
verified_in_game: false
---

## 核心洞见

Minecraft 1.21.2+ 引入了基于 JSON 文件的对话框系统，支持多种交互类型和动态命令执行。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

对话框系统是 Minecraft 1.21.2+ 新增的功能，允许数据包开发者创建弹出式菜单。对话框以 JSON 文件形式存储在 `/data/<namespace>/dialog/` 目录下。系统支持五种类型：确认对话框（两个按钮）、通知对话框（一个按钮）、多操作对话框（多列按钮列表）、对话框列表（按钮打开子对话框）和服务器链接。每个对话框可以包含标题、正文（支持物品显示）和多种输入组件：文本输入、数字滑块、布尔复选框、单选选项。输入组件通过 `key` 字段与动态命令绑定，当用户点击 `dynamic/run_command` 按钮时，输入值会作为宏变量替换到命令中。对话框可以通过 `/dialog show` 命令、暂停界面标签 `minecraft:pause_screen_additions`、快捷操作标签 `minecraft:quick_actions` 或文本组件中的点击事件触发。

## 注意事项

- 玩家需要操作员权限才能执行大多数有用命令，非 OP 玩家可能无法使用动态命令功能
- 暂停界面标签会替换原有的"发送反馈"/"报告漏洞"按钮
- 对话框 JSON 格式复杂，手动编写容易出错，建议使用可视化编辑器
- 常见误解：开发者可能认为对话框只能通过命令直接显示静态内容，或者需要复杂的 UI 系统才能实现交互式表单。
