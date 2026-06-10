---
id: t0194
title: "数据驱动生物变种"
title_en: "data-driven_mob_variants"
layer: technique
source_url: "https://datapack.wiki/guide/adding-new-features/mob-variants"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.21.5"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["data-driven", "mob-variant", "resource-pack", "datapack", "1.21.5"]
verified_in_game: false
---

## 核心洞见

Minecraft 1.21.5+ 允许通过数据包和资源包为特定生物添加自定义变种，无需修改游戏代码。

## 代码示例

```mcfunction
{
  "asset_id": "example:entity/cat/example_cat",
  "baby_asset_id": "example:entity/cat/custom_baby_cat",
  "spawn_conditions": [
    {
      "priority": 0
    }
  ]
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术基于 Minecraft 1.21.5 引入的数据驱动生物变种系统。通过在数据包中创建 JSON 定义文件（位于 `data/<namespace>/<mob>_variant/` 目录），指定纹理资源路径（`asset_id`）和生成条件（`spawn_conditions`），并在资源包中提供对应纹理图片，即可实现自定义变种。生成条件支持按优先级（`priority`）和条件类型（如 `minecraft:structure` 或 `minecraft:biome`）控制变种在特定结构或生物群系中生成。系统会随机选择满足条件的变种。关键点在于：变种定义完全由数据驱动，无需修改游戏核心文件；但仅支持特定生物（猫、鸡、牛、青蛙、猪、狼、僵尸鹦鹉螺），不支持马和兔子等。

## 注意事项

- 需要离开并重新加入世界才能生效，仅使用 /reload 命令无效
- 不是所有生物都支持自定义变种，如马和兔子不支持
- 某些生物（如鸡、牛、猪）需要额外指定 model 字段
- 狼需要指定三个纹理（angry、tame、wild）及其幼年版本
- 常见误解：开发者可能认为生物变种只能通过模组或修改游戏代码实现，或者以为所有生物都支持自定义变种。
