---
id: t0269
title: 使用 features 字段启用实验性内容
title_en: Enabling Experimental Content with features Field
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-datapack/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["pack.mcmeta", "实验性内容", "数据包配置"]
verified_in_game: false
---

## 核心洞见

在 pack.mcmeta 中添加 features 字段可以启用实验性游戏内容（如 1.21 更新），但数据包必须在创建世界时添加，否则实验性内容不会生效。

## 代码示例

```mcfunction
{
  "pack": {
    "description": "Experimental Pack",
    "min_format": [101, 1],
    "max_format": [101, 1]
  },
  "features": {
    "enabled": ["minecraft:update_1_21"]
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

pack.mcmeta 支持一个可选的 features 对象，其中包含一个 enabled 数组，列出要启用的实验性特性（如 "minecraft:update_1_21"）。当数据包包含此字段时，它必须在创建新世界时被添加，否则实验性内容不会生效。这允许数据包利用尚未正式发布的游戏功能。

## 注意事项

- 常见误解：开发者可能认为在 pack.mcmeta 中声明 features 后，数据包可以随时启用实验性内容，而不知道这需要在世界创建时添加。
