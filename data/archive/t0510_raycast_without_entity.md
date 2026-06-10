---
id: t0510
title: "无实体射线检测"
title_en: "raycast_without_entity"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/raycast"
source_type: "mcc_wiki"
source_issue: "questions/raycast"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["raycast", "entityless", "local-coordinates", "execution-context"]
verified_in_game: false
---

## 核心洞见

利用 anchored eyes + positioned ^ ^ ^ + anchored feet 的上下文保留特性，可以在不生成实体的单 tick 内完成射线检测

## 代码示例

```mcfunction
# function example:start_ray
scoreboard players set @s ray_steps 50
scoreboard players set @s ray_success 0
function example:ray

# function example:ray
execute unless block ~ ~ ~ minecraft:air run function example:hit_block
scoreboard players remove @s ray_steps 1
execute if score @s ray_steps matches 1.. if score @s ray_success matches 0 positioned ^ ^ ^0.1 run function example:ray

# function example:hit_block
scoreboard players set @s ray_success 1
setblock ~ ~ ~ stone
```

## 文件结构

- data/example/functions/start_ray.mcfunction
- data/example/functions/ray.mcfunction
- data/example/functions/hit_block.mcfunction

## 用法

以任意实体（如玩家）的身份执行 `function example:start_ray` 即可触发射线检测。射线从执行者眼部出发，沿视线方向每 0.1 格步进一次，直到碰到非空气方块或达到最大步数（50步=5格）。命中后会在命中位置放置石头。

## 使用场景

['检测玩家视线指向的方块（如交互、瞄准系统）', '在单 tick 内快速判断视线路径上是否有特定方块', '不适合需要跨多 tick 持续追踪的射线（如激光动画），应改用实体法']

## 机制原理

该技术的核心是利用 Minecraft 命令执行上下文（execution context）的保留特性。首先通过 `execute as <shooter> at @s anchored eyes` 将执行位置提升到眼睛高度，然后使用 `positioned ^ ^ ^` 将位置锚定到局部坐标原点（即眼睛位置），紧接着 `anchored feet` 将锚点移回脚部。由于 Minecraft 在 `positioned` 之后会保留当前绝对位置，而 `anchored feet` 只是改变后续 `^` 坐标的参考系，因此执行位置被固定在眼睛高度，但后续的 `^ ^ ^` 移动以脚部为参考系。这样每次步进 `positioned ^ ^ ^0.1` 时，实际移动的是眼睛位置沿视线方向前进 0.1 格，而不会因为锚点重新计算眼睛高度导致位置偏移。步进循环通过递归调用函数实现，每次步进前检查当前方块是否为目标方块（如非空气），命中则执行命中函数并设置成功标志，同时通过计分板控制最大步数防止无限循环。

## 注意事项

- 步长 0.1 格是精度与性能的折中，可根据需要调整
- 最大步数（50步=5格）对应玩家默认交互距离，可根据场景修改
- 该方法仅能在单 tick 内完成，不能跨 tick 持续追踪
- `anchored feet` 在较新版本中可能不应使用（原文表述需核实）
- 1.20.2+ 可使用 `return` 简化逻辑，无需 `ray_success` 计分板
