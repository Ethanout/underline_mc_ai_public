---
id: t0240
title: 使用/loot kill从实体获取战利品而不杀死实体
title_en: Using /loot kill to Get Loot from Entities Without Killing Them
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["loot", "entity manipulation", "non-destructive", "resource generation"]
verified_in_game: false
---

## 核心洞见

/loot kill命令可以获取实体的死亡掉落物，但实体本身不会被杀死，这允许重复获取战利品或用于非破坏性测试。

## 代码示例

```mcfunction
# 从最近的猪灵获取金锭掉落（不杀死它）
loot give @p kill @e[type=piglin,limit=1,sort=nearest]
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

/loot kill <selector> 会模拟指定实体的死亡，生成其战利品表掉落物，但实体不会受到伤害或消失。这可用于从生物（如猪灵、僵尸）中提取稀有掉落物而不影响其存在，或用于创建自定义奖励系统。

## 注意事项

- 常见误解：开发者可能认为只有通过杀死实体才能获得其掉落物，或者认为/loot kill会实际杀死目标实体。
