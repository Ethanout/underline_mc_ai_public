---
id: t0403
title: "子包分版本加载"
title_en: "overlay_subpack_versioning"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202504/2/content"
source_type: "feature_article"
source_issue: "202504"
version_min: "1.20.2"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["pack.mcmeta", "overlays", "版本兼容", "数据包结构"]
verified_in_game: false
---

## 核心洞见

数据包可以通过 pack.mcmeta 中的 overlays 机制，按游戏版本自动切换子包内容，无需维护多份数据包副本。

## 代码示例

```mcfunction
{
  "pack": {
    "pack_format": 61,
    "description": "子包测试"
  },
  "overlays": {
    "entries": [
      {
        "directory": "1_21",
        "formats": 48
      },
      {
        "directory": "1_20",
        "formats": {
          "min_inclusive": 15,
          "max_inclusive": 26
        }
      }
    ]
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Minecraft 1.20.2 引入了 overlays 机制，允许在 pack.mcmeta 中定义多个子包（overlay entries），每个子包指定一个目录和对应的数据包版本范围（formats）。当数据包被加载到某个版本的存档时，游戏会检查当前数据包版本（由存档的 pack_format 决定）是否匹配某个子包的 formats 范围。如果匹配，该子包目录下的所有文件会以文件为单位覆盖主包中相同路径的文件（即子包优先）。这利用了数据包加载时的文件合并逻辑：主包作为基础，子包作为增量覆盖层。关键推导：formats 可以是一个整数（精确匹配）或一个包含 min_inclusive 和 max_inclusive 的对象（范围匹配），但 overlays 本身从 1.20.2 开始支持，因此 formats 低于 18 的版本不会触发子包，仅加载主包。与朴素实现（复制多份数据包）相比，此技术避免了文件冗余和重复维护；与命令内判断相比，它消除了后台报错（因为不匹配版本的文件根本不会被加载）。

## 注意事项

- 子包目录名不能与主包目录冲突，且必须与 pack.mcmeta 同级，内部包含 data 文件夹
- formats 范围不能包含低于 18 的版本（1.20.2 以下），否则子包不会生效，但主包仍可加载
- 子包覆盖是以文件为单位的，如果主包和子包有相同路径的文件夹但不同文件，不会合并文件夹内的文件，而是整个文件被替换
- 1.21 后文件夹名称变为单数（如 functions -> function），跨版本维护时需注意路径一致性
- 常见误解：开发者通常认为数据包与游戏版本强耦合，需要为每个版本复制并修改整个数据包，或者通过命令内判断数据版本来分支执行。
