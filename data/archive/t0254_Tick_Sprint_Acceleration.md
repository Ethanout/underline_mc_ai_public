---
id: t0254
title: 游戏刻加速冲刺
title_en: Tick Sprint Acceleration
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["tick", "speed", "testing"]
verified_in_game: false
---

## 核心洞见

使用 `/tick sprint` 可以临时加速游戏刻运行，用于快速跳过等待时间或测试长时间运行的效果。

## 代码示例

```mcfunction
# 加速运行100刻（约5秒正常时间）
/tick sprint 100
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

`/tick sprint <time>` 以最大速度运行指定数量的刻（默认20刻/秒），完成后自动恢复原速率。

## 注意事项

- 常见误解：开发者认为只能通过修改游戏规则或使用命令方块循环来加速时间。
