---
id: t0217
title: 无限时长效果
title_en: Infinite Duration Effect
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["effect", "duration", "infinite"]
verified_in_game: false
---

## 核心洞见

使用 `infinite` 关键字代替数字时长，可以赋予永久持续的效果，无需循环命令维持。

## 代码示例

```mcfunction
effect give @a minecraft:speed infinite 1 true
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

在 `/effect give` 命令中，将 `<duration>` 参数设为 `infinite`，效果将永久持续，直到被清除或覆盖。这避免了循环刷新效果的复杂性。

## 注意事项

- 常见误解：开发者可能认为必须指定一个很大的数字（如 999999）来模拟无限时长，但这样仍会过期且占用资源。
