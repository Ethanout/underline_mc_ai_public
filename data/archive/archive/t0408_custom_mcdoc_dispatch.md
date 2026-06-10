---
id: t0408
title: "自定义mcdoc分发"
title_en: "custom_mcdoc_dispatch"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202505/3/content_"
source_type: "feature_article"
source_issue: "202505"
version_min: "1.21"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["spyglass", "mcdoc", "自定义NBT", "代码补全", "数据结构"]
verified_in_game: false
---

## 核心洞见

通过编写自定义 mcdoc 文件并使用 dispatch 指令，可以为自定义 Storage、custom_data 等 NBT 结构提供原版级别的代码补全和纠错。

## 代码示例

```mcfunction
mcdoc
use ::java::util::text::Text

dispatch minecraft:storage["foo:bar"] to myStruct

struct myStruct {
  CustomText: Text
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

mcdoc 是一种描述 Minecraft 数据包和资源包中 JSON/SNBT 结构的规范文件。Spyglass 内置了原版内容的 mcdoc 文件（vanilla-mcdoc），用于提供补全和验证。通过创建自定义 .mcdoc 文件，开发者可以定义自己的数据结构（struct、enum、type 等），并使用 dispatch 指令将这些结构绑定到特定的 Minecraft 项目（如 minecraft:storage）和子项目（如 Storage 的命名空间 ID）。dispatch 的语法为 dispatch 项目[子项目] to 类型，例如 dispatch minecraft:storage["foo:bar"] to myStruct 表示当编辑 Storage foo:bar 下的 NBT 时，Spyglass 会使用 myStruct 的定义进行补全和纠错。这样，自定义 NBT 结构就能获得与原版 NBT 相同的开发体验。关键推导：mcdoc 文件放在数据包根目录的 mcdoc 文件夹下，Spyglass 会自动加载；可以引用其他 mcdoc 文件（包括 vanilla-mcdoc）中的定义，实现复用。

## 注意事项

- mcdoc 文件必须放在数据包根目录的 mcdoc 文件夹下，与 data 文件夹同级
- dispatch 的子项目（如 Storage 的命名空间 ID）必须用双引号括起来，且格式要正确
- 引用其他 mcdoc 文件时需要使用 use 关键字，路径格式为 ::module::submodule::name
- 需要安装 Mcdoc Syntax Highlighting 插件（misodee.vscode-mcdoc）才能获得语法高亮
- 常见误解：开发者认为只有原版 NBT 才能获得 Spyglass 的补全支持，自定义数据结构只能手动记忆或依赖外部文档。
