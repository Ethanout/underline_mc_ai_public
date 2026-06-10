---
id: t0514
title: "进度单次触发"
title_en: "one_shot_trigger_with_advancement"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/runonce"
source_type: "mcc_wiki"
source_issue: "questions/runonce"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["advancement", "predicate", "edge_detection", "trigger", "player_detection"]
verified_in_game: false
---

## 核心洞见

利用进度系统的location触发器每秒自动检测一次，配合反转谓词实现进入/离开区域的单次触发，减少高频检测开销

## 代码示例

```mcfunction
```json
# predicate example:at_spawn
{
  "condition": "minecraft:location_check",
  "predicate": {
    "position": {
      "x": {
        "min": -100,
        "max": 100
      },
      "z": {
        "min": 200,
        "max": 400
      }
    }
  }
}

# advancement example:spawn/enter
{
  "criteria": {
    "requirement": {
      "trigger": "minecraft:location",
      "conditions": {
        "player": [
          {
            "condition": "minecraft:reference",
            "name": "example:at_spawn"
          }
        ]
      }
    }
  },
  "rewards": {
    "function": "example:spawn/enter"
  }
}
```
```mcfunction
# function example:spawn/enter
advancement revoke @s only example:spawn/leave
tellraw @s "Welcome to spawn!"
```

```json
# advancement example:spawn/leave
{
  "criteria": {
    "requirement": {
      "trigger": "minecraft:location",
      "conditions": {
        "player": [
          {
            "condition": "minecraft:inverted",
            "term": {
              "condition": "minecraft:reference",
              "name": "example:at_spawn"
            }
          }
        ]
      }
    }
  },
  "rewards": {
    "function": "example:spawn/leave"
  }
}
```
```mcfunction
# function example:spawn/leave
advancement revoke @s only example:spawn/enter
tellraw @s "You leave spawn!"
```
```

## 文件结构

- data/example/predicates/at_spawn.json
- data/example/advancements/spawn/enter.json
- data/example/advancements/spawn/leave.json
- data/example/functions/spawn/enter.mcfunction
- data/example/functions/spawn/leave.mcfunction

## 用法

构建数据包后自动生效。当玩家进入/离开指定区域时，对应的进度奖励函数会自动执行，无需额外调用。

## 使用场景

['检测玩家进入/离开特定区域（如出生点、领地边界）时触发事件', '需要低频率检测（每秒一次）以减少服务器负载的场景', '配合其他进度触发器实现更复杂的边缘检测逻辑']

## 机制原理

利用进度系统的`minecraft:location`触发器，该触发器每秒自动检测一次玩家位置。创建两个进度：一个使用谓词引用检测玩家在区域内（enter），另一个使用`inverted`条件反转谓词检测玩家不在区域内（leave）。当玩家进入区域时，enter进度触发，执行奖励函数，并在函数中撤销leave进度，防止重复触发。当玩家离开区域时同理。这种方法的优势在于检测频率固定为每秒一次，比每tick检测（每秒20次）更节省性能，适合玩家数量多的服务器。

## 注意事项

- `minecraft:location`触发器每秒只检测一次，不是每tick检测
- 谓词中省略Y轴检查时，玩家在任何高度都会匹配
- 需要为每个检测区域创建独立的谓词和两个进度文件
- 此方法仅适用于Java版（原文未明确说明，但location触发器在Bedrock中行为不同）
