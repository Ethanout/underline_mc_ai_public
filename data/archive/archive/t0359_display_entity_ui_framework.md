---
id: t0359
title: "展示实体UI框架"
title_en: "display_entity_ui_framework"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202506/0/content"
source_type: "feature_article"
source_issue: "202506"
version_min: "1.19.4"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["display_entity", "ui_framework", "event_system", "animation", "layout"]
verified_in_game: false
---

## 核心洞见

展示实体可以构建完整的动态UI系统，支持事件、动画和布局，其灵活性超越容器GUI。

## 代码示例

```mcfunction
# 写入UI布局数据
data modify floating_ui:input data set value {"type":"panel","size":[5f,5f],"child":[{"type":"button","y":0.3,"size":[2.5f,2.5f],"item":{"id":"apple"}}]}
# 显示UI
function floating_ui:.player_new_ui

# 关闭UID为0的UI
execute as @e[tag=floating_ui_root] if score @s floating_ui.uid matches 0 run function floating_ui:_dispose_ui

# 注册控件模板
data modify storage floating_ui:data custom.test set value {"content":{"type":"panel","name":"test","size":[5f,5f],"child":[{"type":"textblock","text":"default"}]},"params":{"text":"child[0].text"}}
data modify storage floating_ui:input data set value {"type":"test","params":[{"key":"text","value":"Hello FloatingUI"}]}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Floating UI 利用 Minecraft 1.19.4 引入的展示实体（item_display, text_display）作为UI元素。每个控件对应一个展示实体，通过SNBT格式定义布局数据。核心机制包括：1) 使用物品展示实体(item_display)渲染按钮、面板等控件，文本展示实体(text_display)渲染文本；2) 通过射线检测（基于小豆数学库）计算玩家准星与控件的交点，实现鼠标悬停和点击事件；3) 利用展示实体的插值功能实现动画（如缩放、移动）；4) 使用标记实体(marker)存储控件的元数据（如UUID、名称、标签），实现控件查找和事件路由。UI的根实体存储所有子控件的UUID列表，通过name或tag属性实现O(1)或O(n)的控件访问。事件系统通过函数标签触发，执行者设为控件实体，玩家通过floating_ui_owner标签访问。

## 注意事项

- UI的UID在每次调用.player_new_ui时会被覆盖，必须及时保存
- 文本控件由marker和文本展示实体两个实体组成，需要通过marker访问文本实体
- 动画中的start和end事件不能用于触发动画本身，只能用于其他副作用
- 常见误解：开发者可能认为展示实体只能用于静态展示，无法实现可交互、动态解析的UI系统。
