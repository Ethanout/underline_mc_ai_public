---
id: t0322
title: 自定义函数调用效果
title_en: Custom Function Call Effect
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-enchantment/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["enchantment", "function_call", "custom_logic", "extensibility"]
verified_in_game: false
---

## 核心洞见

run_function 效果允许在附魔触发时执行任意数据包函数，这为扩展附魔行为提供了无限可能，超越了内置效果类型。

## 代码示例

```mcfunction
{
  "type": "minecraft:run_function",
  "function": "my_pack:enchantments/lightning_strike"
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

run_function 效果接受一个函数路径（如 'namespace:path'），当附魔触发时，游戏会执行该函数。这允许在函数中实现任何命令逻辑，包括条件判断、循环、与其他系统交互等，从而扩展附魔功能。

## 注意事项

- 常见误解：开发者可能认为附魔效果仅限于内置类型，而不知道可以通过 run_function 调用自定义逻辑。
