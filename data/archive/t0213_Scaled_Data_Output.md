---
id: t0213
title: 数据获取的缩放输出
title_en: Scaled Data Output
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["data", "nbt", "data-get", "scaling"]
verified_in_game: false
---

## 核心洞见

`data get` 命令的 `<scale>` 参数可以对数值型 NBT 路径的结果进行缩放，直接输出缩放后的值，省去后续的数学运算。

## 代码示例

```mcfunction
data get entity @s Health 10
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

`data get` 命令的第三个参数 `<scale>` 是一个整数，当路径指向一个数值时，命令会将该数值乘以 `<scale>` 后输出。这适用于快速转换单位或调整精度。

## 注意事项

- 常见误解：开发者通常认为 `data get` 只能原样输出 NBT 值，如果需要缩放（如将分数转换为百分比），必须额外使用 `scoreboard` 或 `execute store` 进行运算。
