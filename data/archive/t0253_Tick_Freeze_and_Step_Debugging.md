---
id: t0253
title: 游戏刻冻结与单步调试
title_en: Tick Freeze and Step Debugging
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["debug", "tick", "single-step"]
verified_in_game: false
---

## 核心洞见

通过冻结游戏刻并逐步执行，可以精确控制游戏逻辑的每一步，用于调试复杂机制或观察瞬间状态变化。

## 代码示例

```mcfunction
# 冻结游戏
/tick freeze
# 单步执行1刻
/tick step 1
# 继续执行
/tick unfreeze
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

`/tick freeze` 暂停所有游戏刻更新，但玩家仍可移动和交互；`/tick step` 执行指定数量的刻后自动暂停，允许逐步观察逻辑执行。

## 注意事项

- 常见误解：开发者通常认为游戏刻无法暂停或单步执行，只能通过降低速率来模拟。
