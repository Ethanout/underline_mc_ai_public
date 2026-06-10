---
id: q96-如何减少每tick检测的东西
layer: pattern
version_min: "1.13"
confidence: high
verified_in_game: false
source: llm_draft
tags: ["performance", "optimization", "tick", "advancement", "selector", "predicate"]
generated_by: fill_empty_q.py
---

# 如何减少每tick检测的东西

## 核心挑战

在 Minecraft 数据包开发中，每 tick（0.05秒）执行的检测是性能开销的主要来源。高频检测（如 `@e[nbt=...]`、`execute if entity` 遍历大量实体、`execute store` 大量读取）会导致服务器 TPS 下降。核心挑战在于：**如何在不丢失功能的前提下，将检测频率从"每tick"降低到"按需触发"或"低频轮询"**。

## 方案一：事件驱动架构（推荐）

### 原理

利用原版进度（advancement）的触发器（trigger）替代主动轮询。当某个事件发生时（如玩家移动、物品栏变化、实体受伤），进度自动触发并执行函数，从而避免每tick检测。

**关键触发器列表**：
- `minecraft:tick` — 每tick触发（不推荐用于减少检测，但可用于计时器）
- `minecraft:inventory_changed` — 物品栏变化时触发
- `minecraft:player_interacted_with_entity` — 玩家与实体交互时触发
- `minecraft:entity_hurt_player` — 玩家受伤时触发
- `minecraft:player_killed_entity` — 玩家击杀实体时触发
- `minecraft:location` — 玩家位置满足谓词时触发（可配置检测间隔）

### 完整实现：用 `location` 触发器替代每tick位置检测

假设需求：检测玩家是否进入某个区域（如半径10格内的圆形区域）。

**传统每tick方案**（性能差）：
```mcfunction
# tick.mcfunction — 每tick执行
execute as @a at @s if entity @s[distance=..10] run function namespace:in_zone
```

**事件驱动方案**（性能优）：

`data/namespace/advancement/enter_zone.json`
```json
{
  "criteria": {
    "enter": {
      "trigger": "minecraft:location",
      "conditions": {
        "player": [
          {
            "condition": "minecraft:entity_properties",
            "entity": "this",
            "predicate": {
              "location": {
                "position": {
                  "x": 0,
                  "y": 0,
                  "z": 0
                }
              },
              "distance": {
                "absolute": {
                  "max": 10
                }
              }
            }
          }
        ]
      }
    }
  },
  "rewards": {
    "function": "namespace:enter_zone"
  }
}
```

`data/namespace/advancement/leave_zone.json`
```json
{
  "criteria": {
    "leave": {
      "trigger": "minecraft:location",
      "conditions": {
        "player": [
          {
            "condition": "minecraft:entity_properties",
            "entity": "this",
            "predicate": {
              "location": {
                "position": {
                  "x": 0,
                  "y": 0,
                  "z": 0
                }
              },
              "distance": {
                "absolute": {
                  "min": 10.001
                }
              }
            }
          }
        ]
      }
    }
  },
  "rewards": {
    "function": "namespace:leave_zone"
  }
}
```

`data/namespace/function/enter_zone.mcfunction`
```mcfunction
# 玩家进入区域
scoreboard players set @s zone 1
# 撤销进度，以便下次触发
advancement revoke @s only namespace:enter_zone
advancement revoke @s only namespace:leave_zone
```

`data/namespace/function/leave_zone.mcfunction`
```mcfunction
# 玩家离开区域
scoreboard players set @s zone 0
advancement revoke @s only namespace:enter_zone
advancement revoke @s only namespace:leave_zone
```

**陷阱**：
1. `location` 触发器的检测间隔是**20 tick（1秒）**，不是每tick。这意味着玩家可能在1秒内进出区域而未被检测到。如果需要更精确的边界检测，需要结合其他机制。
2. 必须手动 `revoke` 进度，否则进度只会触发一次。
3. 如果玩家在加载世界时已经在区域内，进度不会自动触发。需要在 `load` 函数中手动检查一次。

## 方案二：计时器轮询（低频检测）

### 原理

如果事件驱动不可行（例如需要检测实体间的相对位置），可以降低检测频率。使用 `schedule` 命令或 `tick` 进度配合 scoreboard 计数器，实现每 N tick 检测一次。

### 完整实现：每 20 tick 检测一次实体距离

`data/namespace/function/load.mcfunction`
```mcfunction
# 初始化计时器
scoreboard objectives add timer dummy
scoreboard players set #tick_counter timer 0
```

`data/namespace/function/tick.mcfunction`
```mcfunction
# 每tick执行，但只每20tick执行一次检测
scoreboard players add #tick_counter timer 1
execute if score #tick_counter timer matches 20.. run function namespace:check_entities
```

`data/namespace/function/check_entities.mcfunction`
```mcfunction
# 重置计时器
scoreboard players set #tick_counter timer 0

# 执行检测（每20tick = 1秒一次）
execute as @e[type=minecraft:zombie] at @s if entity @p[distance=..5] run function namespace:zombie_near_player
```

**陷阱**：
1. 计时器使用 `#` 前缀的虚拟玩家，避免与真实玩家混淆。
2. 检测间隔不能太长，否则玩家可能感觉响应延迟。建议根据功能需求调整：玩家交互类 ≤5 tick，环境检测类 ≤20 tick。
3. 如果使用 `schedule` 命令替代 tick 函数，注意 `schedule` 在服务器重载后不会自动恢复，需要在 `load` 中重新设置。

## 方案三：条件过滤 + 选择器优化

### 原理

如果必须每tick检测，可以通过优化选择器和条件来减少检测范围。核心原则：
1. **避免 `nbt=` 选择器**：NBT 匹配需要序列化整个实体的 NBT，性能极差。
2. **使用 `type=` 和 `tag=` 缩小范围**：优先使用实体类型和标签过滤。
3. **使用 `predicate` 替代复杂条件**：谓词在服务端优化更好。
4. **使用 `execute if` 链式过滤**：先过滤范围大的条件，再过滤范围小的。

### 完整实现：检测附近有特定标签的玩家

**低效方案**：
```mcfunction
# 每tick执行 — 性能差
execute as @e[type=minecraft:zombie] at @s if entity @p[nbt={Tags:["tracked"]},distance=..10] run ...
```

**优化方案**：
```mcfunction
# 每tick执行 — 性能优
# 1. 先过滤实体类型
# 2. 再过滤距离（使用选择器参数，比nbt快）
# 3. 最后用predicate检查标签（如果标签是动态的）
execute as @e[type=minecraft:zombie] at @s if entity @p[tag=tracked,distance=..10] run ...
```

如果标签是动态的（无法用选择器参数），使用 predicate：

`data/namespace/predicate/has_tracked_tag.json`
```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "nbt": "{Tags:[\"tracked\"]}"
  }
}
```

```mcfunction
execute as @e[type=minecraft:zombie] at @s if predicate namespace:has_tracked_tag run ...
```

**陷阱**：
1. `nbt=` 选择器参数在 1.20.5+ 中仍然存在，但性能问题未解决。尽量使用 `tag=` 或 `predicate` 替代。
2. `execute if predicate` 比 `execute if entity @s[nbt=...]` 性能更好，因为 predicate 可以预编译。
3. 选择器参数 `distance=` 和 `tag=` 是索引的，性能远优于 `nbt=`。

## 方案四：实体标记 + 分片检测

### 原理

当需要检测大量实体时（如 1000+ 个掉落物），可以将实体分成多个组，每tick只检测一组。使用 scoreboard 或 tag 标记组号，循环检测。

### 完整实现：每tick检测 1/5 的掉落物

`data/namespace/function/load.mcfunction`
```mcfunction
scoreboard objectives add shard dummy
```

`data/namespace/function/tick.mcfunction`
```mcfunction
# 每tick检测一个分片
scoreboard players add #shard_index shard 1
execute if score #shard_index shard matches 5.. run scoreboard players set #shard_index shard 0

# 只检测当前分片的掉落物
execute as @e[type=minecraft:item,scores={shard=0..}] if score @s shard = #shard_index shard run function namespace:check_item
```

`data/namespace/function/init_shards.mcfunction`
```mcfunction
# 在实体生成时分配分片（在生成函数中调用）
scoreboard players random @s shard 0 4
```

**陷阱**：
1. 分片检测会导致响应延迟：每个实体最多每 5 tick 被检测一次（0.25秒延迟）。
2. 需要确保新生成的实体被分配了分片，否则永远不会被检测。
3. 分片数量需要根据实体总数和性能要求调整：实体越多，分片越多。

## 方案对比

| 方案 | 版本要求 | 性能 | 延迟 | 适用场景 |
|------|---------|------|------|---------|
| 事件驱动 | 1.13+ | 极低（仅事件触发时执行） | 取决于触发器间隔（location为1秒） | 玩家交互、位置变化、物品栏变化 |
| 计时器轮询 | 1.13+ | 低（每N tick执行一次） | N tick（可配置） | 环境检测、实体AI、周期性任务 |
| 条件过滤优化 | 1.13+ | 中（仍每tick执行，但开销降低） | 0 tick | 必须每tick检测的核心逻辑 |
| 分片检测 | 1.13+ | 低（每tick只检测部分实体） | 分片数 × 1 tick | 大量实体（100+）的批量检测 |

## 综合建议

1. **优先使用事件驱动**：对于玩家相关的事件（移动、交互、物品栏变化），使用 advancement 触发器替代轮询。
2. **其次使用计时器轮询**：对于不需要实时响应的功能（如环境检测、资源再生），降低检测频率。
3. **最后优化必须的每tick检测**：使用选择器优化、predicate、分片等技术减少单次检测开销。
4. **避免 `nbt=` 选择器**：这是性能杀手，尽量用 `tag=`、`type=`、`predicate` 替代。
5. **使用 `execute if` 链式过滤**：先过滤范围大的条件，再过滤范围小的。
