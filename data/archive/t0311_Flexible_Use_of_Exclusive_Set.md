---
id: t0311
title: 附魔互斥集的灵活使用
title_en: Flexible Use of Exclusive Set
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-enchantment/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["enchantment", "exclusive", "tag", "incompatible"]
verified_in_game: false
---

## 核心洞见

exclusive_set 字段可以接受单个附魔ID、标签或数组，允许通过标签批量定义互斥关系，而无需为每个附魔单独设置。

## 代码示例

```mcfunction
# 示例：使用标签定义互斥集
{
  "exclusive_set": "#minecraft:exclusive_set/damage"
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

exclusive_set 字段可以引用一个附魔标签（如 #minecraft:exclusive_set/damage），该标签包含所有互斥的附魔。当物品已有标签中的任一附魔时，无法再添加该附魔。这简化了互斥关系的维护。

## 注意事项

- 常见误解：开发者可能认为互斥只能通过单个附魔ID逐一指定，而不知道可以使用标签（如 #minecraft:exclusive_set/damage）来管理一组互斥附魔。
