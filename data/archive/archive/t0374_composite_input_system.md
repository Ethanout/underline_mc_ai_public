---
id: t0374
title: "复合输入系统"
title_en: "composite_input_system"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202508/4/content"
source_type: "feature_article"
source_issue: "202508"
version_min: "25w32a"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["复合输入", "文本组件", "交互界面", "宏特性"]
verified_in_game: false
---

## 核心洞见

通过对话框实现复杂文本组件的复合输入，解决纯命令输入中引号嵌套和宏特性的限制。

## 代码示例

```mcfunction
function _:_cplx_typing
# 呼出界面
# 插入文本：字面义
# 插入文本组件：可插入悬浮事件、NBT组件、彩色文本等
# 插入物品：字面义，如有输入则覆盖纹理贴图路径（sprite）
# 删除：如有输入则删除指定序号元素，否则删除最后一个
# 快速展示：将物品信息以特定格式展示到对话框，不调用已输入文本
# 发送：发送文本，若输入为'#'则不重置已输入文本
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术设计了一个交互式界面，允许玩家通过对话框逐步构建包含多种组件（如文本、物品图标、悬浮事件、NBT组件）的复杂文本。核心机制是：1) 使用`function`命令呼出界面，通过`tellraw`或`scoreboard`实现交互按钮；2) 利用storage存储中间状态，每次输入追加到列表；3) 通过宏特性处理引号嵌套问题（但存在bug）。与直觉不同，这不是一次性生成完整命令，而是分步构建，允许插入、删除、覆盖元素。特殊之处在于：插入物品时可用输入覆盖纹理路径（sprite），快速展示功能直接输出而不影响已输入文本。

## 注意事项

- 宏特性和引号嵌套可能导致语法错误，需重新打开页面
- 插入文本组件时若不符合语法会报错，无错误提示
- 快速展示功能不调用已输入文本，可能造成预期外的输出
- 常见误解：开发者通常认为复杂文本组件只能通过硬编码命令或外部工具生成，无法在游戏内动态组合。
