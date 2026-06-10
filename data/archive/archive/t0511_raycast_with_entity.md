---
id: t0511
title: "实体射线检测"
title_en: "raycast_with_entity"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/raycast"
source_type: "mcc_wiki"
source_issue: "questions/raycast"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["raycast", "entity-based", "marker-entity", "teleport", "过时"]
verified_in_game: false
---

## 核心洞见

> ⚠️ **此方法已过时，不推荐使用。** 它以函数式思维操作"射线"对象，会产生副作用（实体残留、跨 tick 状态不一致）。现代做法是以"子弹/弹丸"实体为主体，每 tick 由实体自身推进位置并检测碰撞，逻辑更清晰，副作用可控。

通过生成标记实体并逐帧传送实现跨 tick 射线检测。适用于需要持续追踪或无法使用数据包的老版本场景。

## 代码示例

```mcfunction
# function example:start_ray

# summon entity to use as a marker
summon area_effect_cloud ~ ~ ~ {Tags:["ray_marker"]}
# make sure the marker entity is rotated in the same way as the executing entity
tp @e[tag=ray_marker] ~ ~ ~ ~ ~

scoreboard players set @e[tag=ray_marker] ray_steps 50
scoreboard players set @e[tag=ray_marker] ray_success 0
execute as @e[tag=ray_marker] at @s run function example:ray

# function example:ray
execute unless block ~ ~ ~ minecraft:air run function example:hit_block
scoreboard players remove @s ray_steps 1
tp @s ^ ^ ^0.1
execute if score @s ray_steps matches 1.. if score @s ray_success matches 0 at @s run function example:ray
```

## 文件结构

- data/example/functions/start_ray.mcfunction
- data/example/functions/ray.mcfunction
- data/example/functions/hit_block.mcfunction

## 用法

以任意实体（如玩家）的身份执行 `function example:start_ray` 即可触发射线检测。会生成一个 area_effect_cloud 标记实体，沿执行者视线方向每 0.1 格步进一次，直到碰到非空气方块或达到最大步数。命中后会在命中位置放置石头。标记实体在完成后需要手动清理（如在 hit_block 中加 kill 命令）。

## 使用场景

['需要跨多 tick 持续追踪的射线效果（如激光、牵引光束）', '无法使用数据包（仅命令方块）时的射线检测', '需要标记实体来记录命中位置供后续使用的场景']

## 机制原理

与无实体法不同，实体法通过生成一个标记实体（如 area_effect_cloud）来承载射线位置。首先将标记实体的旋转设置为与执行者一致（通过 tp 命令复制旋转角度），然后以标记实体为执行者递归调用射线函数。每次步进时，使用 `tp @s ^ ^ ^0.1` 将标记实体沿其视线方向移动 0.1 格，然后重新以标记实体的位置执行函数。由于实体位置会跨 tick 保留，因此可以在多个游戏 tick 中逐步移动，实现持续追踪效果。每次步进前检查标记实体所在位置的方块，命中则执行命中函数。通过计分板控制最大步数防止无限循环。

## 注意事项

- ⚠️ **不推荐在新项目中使用此方案**，改用以弹丸实体为主体的方式（弹丸每 tick 自己 tp 并检测碰撞，不依赖外部函数递归驱动）
- 必须在使用后清理标记实体（如 kill），否则会造成实体堆积
- 步长 0.1 格是精度与性能的折中
- 实体法比无实体法性能开销更大（实体生成/销毁、tp 操作）
- 在 Bedrock 旧版 execute 中，实体上下移动角度可能被限制在 45° 或 0°（原文表述需核实）
- 推荐使用自定义实体（无 AI、无重力、不可见）作为标记
