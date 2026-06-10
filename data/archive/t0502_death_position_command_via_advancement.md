---
id: t0502
title: "死亡位置执行命令"
title_en: "death_position_command_via_advancement"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/playerdeaths"
source_type: "mcc_wiki"
source_issue: "questions/playerdeaths"
version_min: "1.15"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["death detection", "advancement", "death position", "event trigger"]
verified_in_game: false
---

## 核心洞见

利用 entity_hurt_player 触发器在玩家死亡瞬间（重生前）执行函数，可在死亡位置执行命令

## 代码示例

```mcfunction
{
  "criteria": {
    "requirement": {
      "trigger": "minecraft:entity_hurt_player",
      "conditions": {
        "player": [
          {
            "condition": "minecraft:entity_properties",
            "entity": "this",
            "predicate": {
              "nbt": "{Health:0f}"
            }
          }
        ]
      }
    }
  },
  "rewards": {
    "function": "example:death"
  }
}
```
```mcfunction
# function example:death
advancement revoke @s only example:death
summon zombie ~ ~ ~ {PersistenceRequired:true,CanPickUpLoot:true}
```

## 文件结构

- data/example/advancements/death.json
- data/example/functions/death.mcfunction

## 用法

构建数据包后，玩家死亡时自动触发 advancement，执行奖励函数。函数中需先撤销 advancement 以防止重复触发。

## 使用场景

['需要在玩家死亡位置执行命令（如生成怪物、掉落物品、放置方块）', '需要在玩家死亡瞬间执行逻辑，而不是重生后', '不适用于需要检测重生事件的场景']

## 机制原理

`minecraft:entity_hurt_player` 触发器是基于事件的，不依赖 tick 调度。当玩家受到伤害且生命值变为0时，该触发器在玩家重生之前执行。通过 NBT 条件 `{Health:0f}` 确保只在玩家死亡时触发（而非任何受伤）。由于执行时机在重生前，此时玩家仍处于死亡位置，因此 `~ ~ ~` 相对坐标指向死亡位置。函数中必须撤销 advancement 以防止每次 tick 重复触发。这种方法比使用 `LastDeathLocation` NBT 数据更简洁高效。

## 注意事项

- 需要数据包支持，不能仅用命令方块
- 必须撤销 advancement，否则每次 tick 都会触发（因为条件持续满足）
- `entity_hurt_player` 触发器在 1.15+ 可用
- 如果 gamerule `doImmediateRespawn` 为 true，玩家会立即重生，但此方法仍能在重生前执行（原文表述需核实）
