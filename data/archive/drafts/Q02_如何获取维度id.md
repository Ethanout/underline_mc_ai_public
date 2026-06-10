---
id: q02-如何获取维度id
layer: pattern
version_min: "1.16"
confidence: high
verified_in_game: false
source: llm_draft
tags: ["dimension", "world", "location", "predicate", "advancement", "execute", "storage"]
generated_by: fill_empty_q.py
---

# 如何获取维度 ID

## 问题背景

在 Minecraft 数据包开发中，获取玩家或实体当前所在的维度 ID（如 `minecraft:overworld`、`minecraft:the_nether`、`minecraft:the_end`）是一个常见需求。维度 ID 是命名空间 ID 格式的字符串，用于区分不同的世界维度。

**核心挑战**：原版命令系统没有直接的 `get dimension` 命令，需要通过间接方式获取维度信息。

---

## 方案一：使用 `execute in` 配合 `function` 和 `storage`（推荐，1.20.5+）

### 原理

利用 `execute in` 命令可以改变执行上下文的维度，结合 `function` 的 `return run` 机制，将维度信息写入 storage。具体思路是：

1. 创建一个函数，该函数在特定维度中执行时返回不同的值
2. 使用 `execute in` 切换到目标维度，然后调用该函数
3. 函数通过 `return run` 返回一个代表维度的数值
4. 将数值映射回维度 ID

### 完整实现

#### 目录结构
```
data/
  <namespace>/
    function/
      dimension/
        get_dimension_id.mcfunction
        overworld.mcfunction
        nether.mcfunction
        end.mcfunction
        map_id_to_dimension.mcfunction
    storage/
      <namespace>/
        dimension_data.json  (初始化为空)
```

#### 1. 初始化 storage（load 中执行）
```mcfunction
# load.mcfunction
data modify storage <namespace>:dimension_data dimension set value ""
```

#### 2. 获取维度 ID 的核心函数
`data/<namespace>/function/dimension/get_dimension_id.mcfunction`
```mcfunction
# 用法：execute as <entity> at @s run function <namespace>:dimension/get_dimension_id
# 结果写入 storage <namespace>:dimension_data dimension

# 先清除旧数据
data remove storage <namespace>:dimension_data dimension

# 尝试在末地执行，如果成功则返回 2
execute in minecraft:the_end run function <namespace>:dimension/end

# 如果上一步没有返回（即不在末地），尝试在地狱执行
execute if data storage <namespace>:dimension_data dimension run return fail
execute in minecraft:the_nether run function <namespace>:dimension/nether

# 如果上一步没有返回（即不在地狱），则默认是主世界
execute if data storage <namespace>:dimension_data dimension run return fail
data modify storage <namespace>:dimension_data dimension set value "minecraft:overworld"
```

`data/<namespace>/function/dimension/end.mcfunction`
```mcfunction
# 如果当前维度是末地，则设置维度 ID 并返回
data modify storage <namespace>:dimension_data dimension set value "minecraft:the_end"
return 1
```

`data/<namespace>/function/dimension/nether.mcfunction`
```mcfunction
# 如果当前维度是地狱，则设置维度 ID 并返回
data modify storage <namespace>:dimension_data dimension set value "minecraft:the_nether"
return 1
```

#### 3. 使用示例
```mcfunction
# 检测玩家是否在主世界
execute as @a at @s run function <namespace>:dimension/get_dimension_id
execute if data storage <namespace>:dimension_data dimension{"minecraft:overworld"} run say 玩家在主世界
```

### 陷阱与注意事项

1. **版本要求**：`return` 命令在 1.20.5 中引入，此方案仅适用于 1.20.5+
2. **性能开销**：每次调用需要执行 2-3 次 `execute in` 切换维度，开销较低但频繁调用（如每 tick）可能影响性能
3. **多线程问题**：如果多个实体同时调用此函数，storage 数据可能被覆盖。建议在单线程上下文中使用（如 `execute as @a at @s run function` 是顺序执行的）
4. **自定义维度**：此方案仅支持原版三个维度。如需支持自定义维度，需要扩展 `get_dimension_id.mcfunction` 中的判断逻辑

---

## 方案二：使用 `predicate` 和 `location_check`（1.16+，通用方案）

### 原理

利用 `predicate` 中的 `location_check` 条件，可以检测实体是否位于特定维度。通过组合多个 predicate，可以确定当前维度。

### 完整实现

#### 目录结构
```
data/
  <namespace>/
    predicate/
      dimension/
        is_overworld.json
        is_nether.json
        is_end.json
    function/
      dimension/
        get_dimension_id.mcfunction
```

#### 1. 创建维度检测 predicate

`data/<namespace>/predicate/dimension/is_overworld.json`
```json
{
  "condition": "minecraft:location_check",
  "predicate": {
    "dimension": "minecraft:overworld"
  }
}
```

`data/<namespace>/predicate/dimension/is_nether.json`
```json
{
  "condition": "minecraft:location_check",
  "predicate": {
    "dimension": "minecraft:the_nether"
  }
}
```

`data/<namespace>/predicate/dimension/is_end.json`
```json
{
  "condition": "minecraft:location_check",
  "predicate": {
    "dimension": "minecraft:the_end"
  }
}
```

#### 2. 获取维度 ID 的函数

`data/<namespace>/function/dimension/get_dimension_id.mcfunction`
```mcfunction
# 用法：execute as <entity> at @s run function <namespace>:dimension/get_dimension_id
# 结果通过 scoreboard 返回

# 先重置分数
scoreboard players set @s <namespace>.dimension_id -1

# 检测维度
execute if predicate <namespace>:dimension/is_end run scoreboard players set @s <namespace>.dimension_id 2
execute if predicate <namespace>:dimension/is_nether run scoreboard players set @s <namespace>.dimension_id 1
execute if predicate <namespace>:dimension/is_overworld run scoreboard players set @s <namespace>.dimension_id 0
```

#### 3. 初始化 scoreboard（load 中执行）
```mcfunction
# load.mcfunction
scoreboard objectives add <namespace>.dimension_id dummy
```

### 陷阱与注意事项

1. **版本兼容性**：`location_check` predicate 从 1.16 开始支持，适用于所有现代版本
2. **性能开销**：每次调用需要执行 3 次 predicate 检测，开销较低
3. **自定义维度**：需要为每个自定义维度创建对应的 predicate 文件
4. **返回值**：返回的是数值（0=主世界，1=地狱，2=末地），需要额外映射到维度 ID 字符串
5. **选择器限制**：`predicate` 条件不能直接在 `@e` 选择器中使用（1.20.5 之前），需要通过 `execute if predicate` 实现

---

## 方案三：使用 `advancement` 和 `location` trigger（1.16+，事件驱动）

### 原理

利用 `minecraft:location` trigger 的 advancement，当玩家进入特定维度时触发，记录维度信息到 storage。

### 完整实现

#### 目录结构
```
data/
  <namespace>/
    advancement/
      dimension/
        entered_overworld.json
        entered_nether.json
        entered_end.json
    function/
      dimension/
        on_dimension_change.mcfunction
```

#### 1. 创建维度进入 advancement

`data/<namespace>/advancement/dimension/entered_overworld.json`
```json
{
  "criteria": {
    "entered_overworld": {
      "trigger": "minecraft:location",
      "conditions": {
        "player": {
          "location": {
            "dimension": "minecraft:overworld"
          }
        }
      }
    }
  },
  "rewards": {
    "function": "<namespace>:dimension/on_dimension_change"
  }
}
```

`data/<namespace>/advancement/dimension/entered_nether.json`
```json
{
  "criteria": {
    "entered_nether": {
      "trigger": "minecraft:location",
      "conditions": {
        "player": {
          "location": {
            "dimension": "minecraft:the_nether"
          }
        }
      }
    }
  },
  "rewards": {
    "function": "<namespace>:dimension/on_dimension_change"
  }
}
```

`data/<namespace>/advancement/dimension/entered_end.json`
```json
{
  "criteria": {
    "entered_end": {
      "trigger": "minecraft:location",
      "conditions": {
        "player": {
          "location": {
            "dimension": "minecraft:the_end"
          }
        }
      }
    }
  },
  "rewards": {
    "function": "<namespace>:dimension/on_dimension_change"
  }
}
```

#### 2. 维度变化处理函数

`data/<namespace>/function/dimension/on_dimension_change.mcfunction`
```mcfunction
# 检测当前维度并更新 storage
execute if predicate <namespace>:dimension/is_overworld run data modify storage <namespace>:dimension_data player_dimension set value "minecraft:overworld"
execute if predicate <namespace>:dimension/is_nether run data modify storage <namespace>:dimension_data player_dimension set value "minecraft:the_nether"
execute if predicate <namespace>:dimension/is_end run data modify storage <namespace>:dimension_data player_dimension set value "minecraft:the_end"

# 撤销 advancement，以便下次触发
advancement revoke @s only <namespace>:dimension/entered_overworld
advancement revoke @s only <namespace>:dimension/entered_nether
advancement revoke @s only <namespace>:dimension/entered_end
```

#### 3. 初始化（load 中执行）
```mcfunction
# load.mcfunction
data modify storage <namespace>:dimension_data player_dimension set value ""
```

### 陷阱与注意事项

1. **事件驱动**：此方案仅在玩家进入维度时更新信息，不是实时查询。如果需要实时获取维度，需要结合其他方案
2. **版本要求**：`minecraft:location` trigger 从 1.16 开始支持
3. **性能开销**：事件驱动，开销极低（仅在维度变化时执行）
4. **多玩家支持**：storage 只能存储一个值，需要为每个玩家单独存储（如使用 scoreboard 或每个玩家的 storage）
5. **初始状态**：玩家首次加入时不会触发 advancement，需要在 load 中初始化所有在线玩家的维度

---

## 方案对比

| 方案 | 版本要求 | 性能开销 | 实时性 | 自定义维度支持 | 复杂度 |
|------|---------|---------|--------|---------------|--------|
| 方案一：execute in + return | 1.20.5+ | 低 | 实时 | 需扩展 | 中 |
| 方案二：predicate + location_check | 1.16+ | 低 | 实时 | 需扩展 | 低 |
| 方案三：advancement + location trigger | 1.16+ | 极低（事件驱动） | 非实时 | 需扩展 | 中 |

### 推荐场景

- **需要实时获取维度 ID**：方案一（1.20.5+）或方案二（1.16+）
- **仅需在维度变化时响应**：方案三
- **需要支持 1.16-1.20.4**：方案二
- **需要返回字符串维度 ID**：方案一（直接返回字符串）或方案二（需要额外映射）

---

## 补充：获取维度 ID 的完整字符串（1.20.5+，使用 `data get`）

### 原理

从 1.20.5 开始，可以通过 `data get entity` 获取实体的 `Dimension` 字段，该字段直接返回维度 ID 字符串。

### 实现

```mcfunction
# 获取玩家维度 ID 并存入 storage
execute as @a run data modify storage <namespace>:dimension_data player_dimension set from entity @s Dimension

# 输出到聊天
tellraw @a [{"text":"当前维度: "},{"storage":"<namespace>:dimension_data","nbt":"player_dimension"}]
```

### 陷阱

1. **版本要求**：仅 1.20.5+，因为 `Dimension` 字段在 1.20.5 中改为直接存储命名空间 ID 字符串
2. **性能**：直接读取 NBT，开销极低
3. **多玩家**：storage 只能存储一个值，需要为每个玩家单独处理

---
