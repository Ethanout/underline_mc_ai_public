---
id: t0187
title: 隐藏逻辑进度
title_en: Hidden Logic-Only Advancement
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-advancement/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["advancement", "hidden", "logic"]
verified_in_game: false
---

## 核心洞见

进度可以没有 display 字段，仅作为逻辑节点用于触发奖励或作为其他进度的父节点，对玩家完全不可见。

## 代码示例

```mcfunction
{
  "criteria": {
    "check": {
      "trigger": "minecraft:impossible"
    }
  },
  "rewards": {
    "function": "namespace:secret_trigger"
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

在进度 JSON 中不包含 display 对象，该进度就不会出现在玩家的进度界面中，但所有条件检测和奖励机制仍然有效。

## 注意事项

- 常见误解：开发者常以为进度必须有显示信息，但省略 display 字段即可创建纯逻辑进度，用于后台触发函数或作为条件检查。
