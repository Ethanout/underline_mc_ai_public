---
id: t0230
title: 精准条件控制
title_en: Precise Criterion Control
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["advancement", "criterion", "fine-grained", "grant", "revoke"]
verified_in_game: false
---

## 核心洞见

通过 `only` 子命令可以单独授予或撤销某个进度的特定条件，而不是整个进度，这允许对玩家进度进行细粒度控制。

## 代码示例

```mcfunction
advancement grant @p only minecraft:story/mine_diamond
advancement revoke @p only minecraft:story/mine_diamond diamond
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

`advancement grant ... only <advancement> [<criterion>]` 允许指定进度内的一个具体条件（criterion），如果省略条件，则授予该进度下的所有条件。同样，`revoke` 也可以精确撤销单个条件。这通过直接操作玩家的进度数据实现，无需修改进度文件。

## 注意事项

- 常见误解：开发者可能认为 `advancement` 命令只能操作整个进度，无法单独控制进度内的单个条件。
