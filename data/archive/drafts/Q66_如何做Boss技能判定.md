---
id: q66-如何做Boss技能判定
layer: pattern
version_min: "1.13"
confidence: high
verified_in_game: false
source: llm_draft
tags: ["boss", "skill", "advancement", "scoreboard", "predicate", "phase", "cooldown"]
generated_by: fill_empty_q.py
---

# 如何做Boss技能判定

## 一、核心挑战

Boss技能判定在数据包开发中的核心挑战是：**如何在原版Minecraft有限的机制下，实现复杂的技能阶段转换、条件检测和冷却管理**。原版没有内置的"技能系统"，需要利用进度、计分板、谓词、实体标签等机制组合实现。

## 二、方案一：基于进度（Advancement）的触发式判定

### 原理

利用进度系统的`inventory_changed`、`player_hurt_entity`、`entity_hurt_player`等触发器，在特定事件发生时自动执行函数。这是最接近"事件驱动"的方案。

### 版本要求

1.16+（进度系统成熟），1.20.5+（支持更丰富的物品检测）

### 完整实现

#### 目录结构
```
data/
  boss/
    advancement/
      skill/phase1.json
      skill/phase2.json
    function/
      skill/
        phase1.mcfunction
        phase2.mcfunction
        check_phase.mcfunction
      boss/
        tick.mcfunction
        init.mcfunction
```

#### 1. 阶段进度定义

`data/boss/advancement/skill/phase1.json`
```json
{
  "criteria": {
    "enter_phase1": {
      "trigger": "minecraft:player_hurt_entity",
      "conditions": {
        "entity": {
          "type": "minecraft:ender_dragon",
          "nbt": "{Tags:[\"boss.phase0\"]}"
        }
      }
    }
  },
  "rewards": {
    "function": "boss:skill/phase1"
  }
}
```

`data/boss/advancement/skill/phase2.json`
```json
{
  "criteria": {
    "enter_phase2": {
      "trigger": "minecraft:player_hurt_entity",
      "conditions": {
        "entity": {
          "type": "minecraft:ender_dragon",
          "nbt": "{Health:100f}"
        }
      }
    }
  },
  "rewards": {
    "function": "boss:skill/phase2"
  }
}
```

#### 2. 阶段切换函数

`data/boss/function/skill/phase1.mcfunction`
```mcfunction
# 移除旧阶段标签
tag @e[type=ender_dragon,tag=boss.phase0] remove boss.phase0
tag @e[type=ender_dragon,tag=boss.phase0] add boss.phase1

# 设置技能冷却计分板
scoreboard players set @e[type=ender_dragon,tag=boss.phase1] boss.skill_cooldown 0

# 触发第一阶段技能
schedule function boss:skill/phase1_attack 1s

# 撤销进度，允许下次触发
advancement revoke @a only boss:skill/phase1
```

`data/boss/function/skill/phase2.mcfunction`
```mcfunction
tag @e[type=ender_dragon,tag=boss.phase1] remove boss.phase1
tag @e[type=ender_dragon,tag=boss.phase1] add boss.phase2

scoreboard players set @e[type=ender_dragon,tag=boss.phase2] boss.skill_cooldown 0

schedule function boss:skill/phase2_attack 1s

advancement revoke @a only boss:skill/phase2
```

#### 3. 技能冷却管理

`data/boss/function/boss/tick.mcfunction`
```mcfunction
# 每tick更新所有Boss的技能冷却
execute as @e[tag=boss.phase1] run scoreboard players add @s boss.skill_cooldown 1

# 冷却达到100tick（5秒）时释放技能
execute as @e[tag=boss.phase1,scores={boss.skill_cooldown=100}] run function boss:skill/phase1_attack
```

### 陷阱与注意事项

1. **进度触发延迟**：进度触发不是即时的，可能有1-2tick延迟。对于需要精确时序的技能，建议使用计分板+谓词组合。
2. **进度撤销问题**：每次触发后必须`advancement revoke`，否则不会再次触发。如果玩家死亡或退出，进度状态可能丢失。
3. **NBT检测性能**：在进度条件中使用`nbt`字段进行高频检测（如每tick检测血量）会导致性能问题。建议仅在阶段转换时使用。
4. **多玩家问题**：进度是每个玩家独立的，如果多个玩家同时攻击Boss，可能导致进度被多次触发。需要在函数中增加去重逻辑。

## 三、方案二：基于计分板（Scoreboard）的轮询式判定

### 原理

在tick函数中，通过计分板记录Boss的各种状态（血量、阶段、技能冷却等），每tick检查条件并执行对应逻辑。这是最灵活但性能开销最大的方案。

### 版本要求

1.13+（计分板系统成熟）

### 完整实现

#### 目录结构
```
data/
  boss/
    function/
      boss/
        tick.mcfunction
        init.mcfunction
        skill/
          check_phase.mcfunction
          phase1_attack.mcfunction
          phase2_attack.mcfunction
          cooldown.mcfunction
    predicates/
      boss_health.json
```

#### 1. 初始化

`data/boss/function/boss/init.mcfunction`
```mcfunction
# 创建计分板
scoreboard objectives add boss.health dummy
scoreboard objectives add boss.phase dummy
scoreboard objectives add boss.skill_cooldown dummy
scoreboard objectives add boss.skill_timer dummy

# 初始化Boss实体
summon ender_dragon ~ ~ ~ {Tags:["boss.main","boss.phase0"]}
```

#### 2. 主Tick循环

`data/boss/function/boss/tick.mcfunction`
```mcfunction
# 更新所有Boss的血量到计分板
execute as @e[tag=boss.main] store result score @s boss.health run data get entity @s Health

# 检查阶段转换
execute as @e[tag=boss.main] run function boss:skill/check_phase

# 更新技能冷却
execute as @e[tag=boss.main] run function boss:skill/cooldown

# 执行技能逻辑
execute as @e[tag=boss.phase1,scores={boss.skill_cooldown=100}] run function boss:skill/phase1_attack
execute as @e[tag=boss.phase2,scores={boss.skill_cooldown=80}] run function boss:skill/phase2_attack
```

#### 3. 阶段检测

`data/boss/function/boss/skill/check_phase.mcfunction`
```mcfunction
# 检查是否进入阶段1（血量低于200）
execute if score @s boss.health matches ..199 if entity @s[tag=boss.phase0] run function boss:skill/enter_phase1

# 检查是否进入阶段2（血量低于100）
execute if score @s boss.health matches ..99 if entity @s[tag=boss.phase1] run function boss:skill/enter_phase2
```

`data/boss/function/boss/skill/enter_phase1.mcfunction`
```mcfunction
tag @s remove boss.phase0
tag @s add boss.phase1
scoreboard players set @s boss.skill_cooldown 0
scoreboard players set @s boss.phase 1

# 通知玩家
tellraw @a {"text":"Boss进入第一阶段！","color":"red"}
```

#### 4. 技能冷却

`data/boss/function/boss/skill/cooldown.mcfunction`
```mcfunction
# 每tick增加冷却
scoreboard players add @s boss.skill_cooldown 1

# 冷却上限100tick（5秒）
execute if score @s boss.skill_cooldown matches 100.. run scoreboard players set @s boss.skill_cooldown 100
```

#### 5. 技能释放

`data/boss/function/boss/skill/phase1_attack.mcfunction`
```mcfunction
# 重置冷却
scoreboard players set @s boss.skill_cooldown 0

# 释放技能：召唤闪电
execute at @s positioned ^ ^ ^10 run summon lightning_bolt

# 播放音效
execute at @s run playsound minecraft:entity.lightning_bolt.thunder master @a

# 设置技能计时器（用于多段技能）
scoreboard players set @s boss.skill_timer 0
```

### 陷阱与注意事项

1. **性能开销**：每tick执行`data get entity`获取血量是相对昂贵的操作。对于大量Boss，建议使用`/scoreboard players set @s boss.health 200`手动管理血量，而不是实时读取。
2. **计分板精度**：计分板只能存储整数，血量是浮点数。使用`store result`会截断小数部分。如果需要精确血量，使用`store success`配合`/data get`的scale参数。
3. **阶段转换边界**：当血量恰好等于边界值时（如100），需要明确是进入阶段2还是留在阶段1。建议使用`..99`和`100..`来避免歧义。
4. **多Boss实例**：如果场景中有多个Boss，每个Boss需要独立的计分板值。使用`@s`选择器确保操作针对当前实体。

## 四、方案三：基于谓词（Predicate）的条件式判定

### 原理

利用谓词系统在`execute if predicate`中检测复杂条件，结合计分板实现高效的技能判定。谓词可以检测实体属性、位置、装备等，比纯计分板更灵活。

### 版本要求

1.15+（谓词系统引入），1.16+（支持`entity_properties`谓词）

### 完整实现

#### 目录结构
```
data/
  boss/
    function/
      boss/
        tick.mcfunction
        skill/
          check_phase.mcfunction
          phase1_attack.mcfunction
    predicates/
      boss/
        phase1.json
        phase2.json
        low_health.json
```

#### 1. 谓词定义

`data/boss/predicates/boss/phase1.json`
```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "type": "minecraft:ender_dragon",
    "nbt": "{Tags:[\"boss.phase1\"]}"
  }
}
```

`data/boss/predicates/boss/low_health.json`
```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "type_specific": {
      "type": "minecraft:mob",
      "health": {
        "max": 100
      }
    }
  }
}
```

#### 2. 主Tick循环

`data/boss/function/boss/tick.mcfunction`
```mcfunction
# 使用谓词检测阶段
execute as @e[tag=boss.main] if predicate boss:boss/phase1 run function boss:skill/phase1_logic

# 使用谓词检测低血量
execute as @e[tag=boss.main] if predicate boss:boss/low_health run function boss:skill/enter_phase2
```

#### 3. 阶段逻辑

`data/boss/function/boss/skill/phase1_logic.mcfunction`
```mcfunction
# 使用谓词+计分板组合
execute if score @s boss.skill_cooldown matches 100.. run function boss:skill/phase1_attack

# 每tick增加冷却
scoreboard players add @s boss.skill_cooldown 1
```

### 陷阱与注意事项

1. **谓词缓存**：谓词在同一个tick内会被缓存，多次使用同一个谓词不会重复计算。但不同谓词之间独立计算。
2. **NBT检测限制**：谓词中的`nbt`字段不支持正则表达式，只能精确匹配。对于动态数据（如血量），建议使用`type_specific`的`health`字段。
3. **版本兼容性**：`type_specific`谓词在1.16+才支持`mob`类型。1.15只能使用`entity_properties`的通用字段。
4. **谓词复用**：同一个谓词可以被多个`execute`命令引用，但修改谓词文件后需要重新加载数据包。

## 五、方案对比

| 方案 | 版本要求 | 性能开销 | 灵活性 | 适用场景 |
|------|---------|---------|--------|---------|
| 进度触发式 | 1.16+ | 低（事件驱动） | 低（只能检测预设事件） | 简单的阶段转换、技能触发 |
| 计分板轮询式 | 1.13+ | 中（每tick计算） | 高（可检测任意条件） | 复杂技能系统、多阶段Boss |
| 谓词条件式 | 1.15+ | 中低（谓词缓存） | 中（结合计分板） | 需要复杂条件检测的场景 |

### 推荐组合方案

对于大多数Boss技能系统，推荐**计分板轮询式 + 谓词条件式**组合：

1. 使用计分板管理核心状态（血量、阶段、冷却）
2. 使用谓词检测复杂条件（如特定装备、位置、状态效果）
3. 使用进度处理特殊事件（如玩家死亡、Boss生成）

## 六、完整示例：三阶段Boss技能系统

### 目录结构
```
data/
  boss/
    function/
      load.mcfunction
      tick.mcfunction
      boss/
        init.mcfunction
        spawn.mcfunction
        death.mcfunction
      skill/
        check_phase.mcfunction
        phase1/
          attack.mcfunction
          pattern.mcfunction
        phase2/
          attack.mcfunction
          enrage.mcfunction
        phase3/
          attack.mcfunction
          ultimate.mcfunction
        cooldown.mcfunction
    predicates/
      boss/
        phase1.json
        phase2.json
        phase3.json
        enraged.json
    advancements/
      boss/
        spawn.json
        death.json
```

### 核心函数

`data/boss/function/load.mcfunction`
```mcfunction
scoreboard objectives add boss.health dummy
scoreboard objectives add boss.phase dummy
scoreboard objectives add boss.skill_cooldown dummy
scoreboard objectives add boss.skill_timer dummy
scoreboard objectives add boss.enrage dummy
```

`data/boss/function/tick.mcfunction`
```mcfunction
# 更新所有Boss状态
execute as @e[tag=boss.main] run function boss:skill/check_phase
execute as @e[tag=boss.main] run function boss:skill/cooldown

# 阶段1技能
execute as @e[tag=boss.phase1,scores={boss.skill_cooldown=100}] run function boss:skill/phase1/attack

# 阶段2技能（冷却更快）
execute as @e[tag=boss.phase2,scores={boss.skill_cooldown=80}] run function boss:skill/phase2/attack

# 阶段3技能（冷却更快，有狂暴机制）
execute as @e[tag=boss.phase3,scores={boss.skill_cooldown=60}] run function boss:skill/phase3/attack

# 检查狂暴状态
execute as @e[tag=boss.phase3,scores={boss.enrage=1..}] run function boss:skill/phase3/enrage
```

`data/boss/function/boss/skill/check_phase.mcfunction`
```mcfunction
# 阶段转换逻辑
execute if score @s boss.health matches ..199 if entity @s[tag=boss.phase0] run function boss:skill/enter_phase1
execute if score @s boss.health matches ..99 if entity @s[tag=boss.phase1] run function boss:skill/enter_phase2
execute if score @s boss.health matches ..49 if entity @s[tag=boss.phase2] run function boss:skill/enter_phase3

# 狂暴检测（阶段3血量低于20时）
execute if score @s boss.health matches ..19 if entity @s[tag=boss.phase3] run scoreboard players set @s boss.enrage 1
```

### 陷阱与注意事项（完整版）

1. **阶段转换的原子性**：确保阶段转换函数中同时更新标签和计分板，避免tick循环中检测到不一致状态。
2. **技能冷却的边界条件**：当冷却达到最大值时，需要重置为0而不是继续增加，否则可能导致技能连续释放。
3. **多Boss实例的隔离**：每个Boss使用独立的计分板值，通过`@s`选择器确保操作针对当前实体。
4. **玩家交互的同步**：如果技能需要与玩家交互（如传送、伤害），使用`execute as @a at @s`确保位置正确。
5. **性能优化**：对于大量Boss，考虑使用`/schedule`替代每tick轮询，降低性能开销。
