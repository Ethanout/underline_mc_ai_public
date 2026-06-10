---
id: t0490
title: "乘客实体死亡检测"
title_en: "passenger_entity_death_detection"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/mobdeaths"
source_type: "mcc_wiki"
source_issue: "questions/mobdeaths"
version_min: "1.16"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["death_detection", "passenger", "marker", "nbt_check", "entity_despawn"]
verified_in_game: false
---

## 核心洞见

利用 marker 实体作为乘客，通过检测载具的 DeathTime NBT 来判断生物死亡，即使生物处于死亡动画中无法被目标选择器选中。

## 代码示例

```mcfunction
```mcfunction
# 初始化：召唤带有 marker 乘客的生物
summon husk ~ ~ ~ {Tags:["some_tag"],Passengers:[{id:"minecraft:marker",Tags:["death_detector"]}]}

# 1.19.4+ 使用 /ride 命令为已有生物添加 marker 乘客
summon marker ~ ~ ~ {Tags:["death_detector","set_ride"]}
ride @e[type=marker,tag=death_detector,tag=set_ride,limit=1] mount <mob>
tag @e[type=marker,tag=set_ride] remove set_ride

# 1.16-1.19.3 版本：使用 predicate 检测
# function example:tick
execute as @e[type=marker,tag=death_detector,predicate=example:death_mob] run function example:death_mob
execute as @e[type=marker,tag=death_detector,predicate=example:despawn_mob] run function example:despawn_mob

# function example:death_mob
say Mob is dead!
kill @s

# function example:despawn_mob
say Mob is despawn!
kill @s

# predicate example:death_mob
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "vehicle": {
      "nbt": "{DeathTime:1s}"
    }
  }
}

# predicate example:despawn_mob
{
  "condition": "minecraft:inverted",
  "term": {
    "condition": "minecraft:entity_properties",
    "entity": "this",
    "predicate": {
      "vehicle": {}
    }
  }
}

# 1.19.4+ 版本：使用 execute on vehicle 子命令
# 命令方块
execute as @e[type=marker,tag=death_detector] on vehicle unless data entity @s {DeathTime:0s} run say This mob is dying!
execute as @e[type=marker,tag=death_detector] on vehicle unless data entity @s {DeathTime:0s} on passengers run kill @s

# 数据包优化版本（带延迟）
# function example:load
function example:loops/1s

# function example:loops/1s
schedule function example:loops/1s 1s
execute as @e[type=marker,tag=death_detector] on vehicle unless data entity @s {DeathTime:0s} run function example:death_mob
execute as @e[type=marker,tag=death_detector,predicate=example:despawn_mob] run function example:despawn_mob

# function example:death_mob
say Mob is dead!
execute on passengers run kill @s

# function example:despawn_mob
say Mob is despawn!
kill @s
```
```

## 文件结构

- data/example/functions/tick.mcfunction
- data/example/functions/death_mob.mcfunction
- data/example/functions/despawn_mob.mcfunction
- data/example/predicates/death_mob.json
- data/example/predicates/despawn_mob.json
- data/example/functions/load.mcfunction
- data/example/functions/loops/1s.mcfunction

## 用法

构建完数据包后，需要先为要检测的生物添加一个 marker 实体作为乘客（通过召唤时指定或 /ride 命令）。之后数据包会自动在 tick 或循环中检测 marker 的载具状态，当载具 DeathTime 不为 0 时触发死亡事件，当载具消失时触发消失事件。

## 使用场景

['需要检测特定生物（带有特定标签、分数等）的死亡，且不限于玩家击杀', '需要获取生物死亡时的位置坐标', '需要检测生物因任何原因（包括消失）而消失的事件']

## 机制原理

当生物进入死亡动画后，虽然无法被目标选择器选中，但其作为载具（vehicle）的身份仍然保留，且其 NBT 中的 DeathTime 标签会从 0 开始递增。Marker 实体作为乘客，可以通过 predicate 或 execute on vehicle 子命令访问其载具的 NBT 数据。通过检查 DeathTime 是否不为 0，即可判断生物是否已死亡。对于消失检测，则利用当载具消失后，marker 实体的 vehicle 数据变为空（不存在），通过 predicate 的 inverted 条件检测 vehicle 不存在即可。

## 注意事项

- 此方法不适用于已经拥有乘客的生物
- 1.16-1.19.3 版本只能使用 predicate 方式检测，1.19.4+ 可以使用 execute on vehicle 子命令
- 使用 execute on vehicle 子命令在命令方块中每 tick 检测 NBT 可能导致卡顿，建议使用数据包配合 schedule 函数添加检测延迟
- 生物消失检测（despawn）在 1.19.4+ 版本中可以使用 predicate 方式实现，但 execute on vehicle 方式无法直接检测消失
