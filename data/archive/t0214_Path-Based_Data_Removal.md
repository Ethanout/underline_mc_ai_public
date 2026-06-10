---
id: t0214
title: 数据移除的路径删除
title_en: Path-Based Data Removal
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["data", "nbt", "data-remove", "cleanup"]
verified_in_game: false
---

## 核心洞见

`data remove` 命令可以精确删除 NBT 数据中的指定路径，而不是替换整个 NBT 或使用复杂的 `data modify` 来清空字段。

## 代码示例

```mcfunction
data remove entity @s Inventory[0]
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

`data remove` 命令直接删除指定路径的 NBT 节点，包括其所有子节点。这比设置空值更干净，且不会留下空列表或空复合标签。

## 注意事项

- 常见误解：开发者常认为要删除 NBT 中的某个字段，必须用 `data merge` 覆盖整个 NBT 或使用 `data modify` 设置为空值，但这样会保留空字段。
