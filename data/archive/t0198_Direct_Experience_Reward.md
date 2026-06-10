---
id: t0198
title: 直接经验奖励
title_en: Direct Experience Reward
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-advancement/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["advancement", "rewards", "experience"]
verified_in_game: false
---

## 核心洞见

经验奖励是直接添加到玩家经验条中的数值，而不是生成经验球，这避免了经验球拾取延迟和实体开销。

## 代码示例

```mcfunction
{
  "rewards": {
    "experience": 100
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

在 advancement 的 rewards 中设置 experience 字段，玩家达成进度时会立即获得指定数量的经验值，无需拾取过程。

## 注意事项

- 常见误解：开发者可能认为经验奖励会像击杀生物一样生成经验球，需要玩家拾取。
