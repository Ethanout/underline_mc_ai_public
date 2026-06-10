---
id: t0317
title: 查表值类型
title_en: Lookup Table Value Type
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-enchantment/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["enchantment", "value type", "lookup", "level-dependent"]
verified_in_game: false
---

## 核心洞见

lookup 值类型允许根据附魔等级索引一个预定义的数值数组，实现非连续、非公式化的数值映射，并支持 fallback 值。

## 代码示例

```mcfunction
# 示例：等级1=1.0，等级2=2.5，等级3=5.0，其他等级=1.0
{
  "type": "minecraft:lookup",
  "values": [1.0, 2.5, 5.0],
  "fallback": 1.0
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

lookup 值类型接受一个 values 数组和一个 fallback 值。当附魔等级为 i 时，返回 values[i-1]（如果存在），否则返回 fallback。这允许为每个等级单独指定数值，而不受公式限制。

## 注意事项

- 常见误解：开发者可能认为附魔效果只能通过数学公式计算，而不知道可以直接使用查表方式定义每个等级的具体数值，适用于不规则或手动设计的数值曲线。
