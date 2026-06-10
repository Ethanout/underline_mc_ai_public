---
id: t0331
title: "文本展示实体动画框架"
title_en: "text_display_animation_framework"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202510/7/content"
source_type: "feature_article"
source_issue: "202510"
version_min: "1.21.6"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["text_display", "animation", "datapack", "entity_manipulation", "scoreboard_control"]
verified_in_game: false
---

## 核心洞见

通过将每个字符拆分为独立的 text_display 展示实体并利用记分板控制动画时序，可以在纯原版数据包中实现复杂的逐字动画效果。

## 代码示例

```mcfunction
execute anchored eyes positioned ^ ^ ^2 facing entity @s eyes run function textanimation:slidedown/preload {text:'[{text:"H",color:"white"},{text:"e",color:"white"},{text:"l",color:"white"},{text:"l",color:"white"},{text:"o",color:"white"}]',time:170,scale:1,sound:0,speed:100}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用 Minecraft 1.19.4+ 引入的 text_display 展示实体，每个字符作为一个独立的展示实体，通过函数递归或循环在同一游戏刻内生成。核心机制是：1) 将文本字符串拆分为每个字符的文本组件数组，每个字符可以独立设置颜色、样式；2) 生成一个不可见的 text_display 作为基准点，然后在其左侧偏移 (字符数/2)*0.23 格开始逐个生成字符实体，每个字符向右偏移 0.23 格（约一个字宽）；3) 每个字符实体存储动画类型标签和记分板值，通过记分板值决定动画启动顺序；4) 动画通过修改展示实体的 transformation（位移、缩放）和透明度（通过数据标签中的 interpolation 实现平滑过渡）来实现滑动、扩散、翻页等效果；5) 动画完成后将透明度渐变为 0 并移除实体。关键的非直觉点在于：使用 marker 实体作为动画起始位置锚点，利用记分板值作为动画状态机控制每个字符的动画阶段，以及通过函数递归在同一 tick 内批量生成实体避免时序问题。

## 注意事项

- 每个文字对应一个展示实体，传入过长文本会造成大量卡顿
- 每个模板都有特定的组件参数，缺失参数会导致函数执行失败
- 自定义音效必须在对应动画的 sounds.mcfunction 文件中定义，否则无法播放
- 不同动画的声音相互独立，需要在各自的 sounds 文件中添加
- 常见误解：开发者通常认为 Minecraft 原版数据包只能通过 title 命令实现简单的淡入淡出或打字机效果，无法实现逐字滑动、翻页、扩散等复杂动画。
