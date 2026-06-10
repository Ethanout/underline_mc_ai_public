---
id: t0212
title: 数据修改的链式操作
title_en: Chained Data Modification
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["data", "nbt", "data-modify", "data-transfer"]
verified_in_game: false
---

## 核心洞见

通过 `data modify` 的 `from` 子句，可以直接从一个数据源复制数据到另一个数据源，无需中间变量或多次命令，实现高效的数据搬运和重组。

## 代码示例

```mcfunction
data modify block ~ ~ ~ Items append from entity @s Inventory[0]
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

`data modify` 命令的 `from` 子句允许指定源（方块、实体或存储）和路径，直接将源数据复制到目标路径。支持 `append`、`insert`、`merge`、`prepend`、`set` 等操作，可以灵活地组合数据。

## 注意事项

- 常见误解：开发者常认为修改 NBT 数据需要先用 `data get` 读取，再用 `data merge` 写入，或者使用 `execute store` 进行繁琐的逐字段复制。
