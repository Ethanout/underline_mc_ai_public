---
id: t0255
title: 动态调整游戏刻速率
title_en: Dynamic Tick Rate Adjustment
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["tick", "rate", "slow-motion"]
verified_in_game: false
---

## 核心洞见

通过 `/tick rate` 可以实时改变游戏刻速率，用于创建慢动作效果或降低服务器负载。

## 代码示例

```mcfunction
# 设置游戏刻速率为5刻/秒（慢动作）
/tick rate 5
# 恢复默认速率
/tick rate 20
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

`/tick rate <rate>` 设置每秒游戏刻数（默认20），数值越小游戏逻辑越慢，可用于调试或特殊效果。

## 注意事项

- 常见误解：开发者认为游戏刻速率是固定的20刻/秒，无法动态调整。
