---
id: t0406
title: "标签合并覆盖"
title_en: "tick_tag_override_merge"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202504/1/content"
source_type: "feature_article"
source_issue: "202504"
version_min: "1.13"
version_max: ""
wiki_covers_this: true
confidence: low
tags: ["tag", "tick", "merge", "override"]
verified_in_game: false
---

## 核心洞见

数据包通过同名标签文件实现函数注册到游戏循环，但实际是合并而非完全覆盖原版标签

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Minecraft数据包加载机制中，当多个数据包包含相同路径的标签文件（如minecraft/tags/function/tick.json）时，游戏会将这些标签的values数组合并，而不是用后加载的覆盖先加载的。这意味着自定义数据包中的tick.json会与Minecraft内置数据包中的tick.json合并，原版tick函数仍然会执行。这个机制类似于资源包中同名文件的覆盖，但数据包标签是合并而非覆盖。合并顺序取决于数据包的加载顺序，通常自定义数据包后加载，其values会追加到原版values之后。

## 注意事项

- 如果使用replace: true字段，则会完全覆盖原版标签，导致原版tick函数丢失
- 多个数据包同时注册tick函数时，执行顺序取决于数据包加载顺序
- 标签文件路径必须完全匹配原版路径（minecraft/tags/function/tick.json）才能触发合并机制
- 常见误解：开发者可能认为创建同名标签文件会完全覆盖原版标签，导致原版tick函数丢失
