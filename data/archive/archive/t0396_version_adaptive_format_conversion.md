---
id: t0396
title: "版本自适应转换"
title_en: "version_adaptive_format_conversion"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202507/6/content"
source_type: "feature_article"
source_issue: "202507"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["版本兼容", "格式转换", "资源包", "数据包"]
verified_in_game: false
---

## 核心洞见

通过维护版本格式映射表和专用的文件格式化器（如 RecipeFormatter、PathFormatter），在构建时根据目标 Minecraft 版本自动转换资源包/数据包中的配方文件和路径格式，实现单源码多版本兼容。

## 代码示例

```mcfunction
// 原文中未提供完整可运行代码，仅展示了类定义片段
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术依赖两个核心组件：1) minecraft_version.json 文件存储各版本对应的资源格式规范（如数据包格式版本号、资源包格式版本号）；2) 专用的格式化器类（RecipeFormatter、PathFormatter）根据目标版本对文件内容进行转换。在 Builder.preprocessContent 方法中，根据文件路径判断文件类型（如是否包含 'recipe'），然后调用对应的格式化器。格式化器内部实现版本特定的转换逻辑，例如配方格式从 1.19 的 JSON 结构变为 1.20 的 JSON 结构，或者路径格式从 'textures/blocks' 变为 'textures/block'。这避免了为每个版本维护重复的模块内容，只需在构建时动态转换。

## 注意事项

- 格式化器必须覆盖所有可能受版本影响的文件类型，遗漏会导致构建产物在目标版本中无法使用
- 版本映射表需要随 Minecraft 更新而持续维护，否则新版本无法支持
- strict 字段为 true 时，如果找不到对应版本模块会报错，需要谨慎配置
- 常见误解：开发者通常认为需要为每个 Minecraft 版本维护独立的资源包分支，或者手动修改文件内容以适配不同版本。
