---
id: t0478
title: "Y轴范围检测"
title_en: "target_players_above_below_y_level"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/heighttest"
source_type: "mcc_wiki"
source_issue: "questions/heighttest"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["target-selector", "dy", "predicate", "y-level", "execute-at"]
verified_in_game: false
---

## 核心洞见

使用 dy 选择器时，必须配合 execute at @s 才能正确检测任意位置的玩家，否则 x/z 会默认使用命令执行位置。

## 代码示例

```mcfunction
# 检测 y=200 以上的玩家（正确写法）
execute as @a at @s run say @s[y=200,dy=500]

# 检测 y=-30 以下的玩家（dy 为负值）
execute as @a at @s run say @s[y=-30,dy=-500]

# 使用 predicate 检测 y>=40（Java版，需数据包）
# 文件：data/<namespace>/predicates/above_y40.json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "location": {
      "position": {
        "y": {
          "min": 40
        }
      }
    }
  }
}
```

## 文件结构

- data/<namespace>/functions/check_y.mcfunction
- data/<namespace>/predicates/above_y40.json

## 用法

构建数据包后，运行 /function <namespace>:check_y 即可在聊天栏输出符合条件的玩家名。predicate 文件可在其他函数中通过 /execute if predicate <namespace>:above_y40 调用。

## 使用场景

['检测玩家是否超出世界建筑高度（如 y=320）并执行传送或警告', '检测玩家是否掉入虚空（y<0）并执行重置或伤害', '在自定义小游戏或地图中，根据玩家所在 Y 层触发不同事件']

## 机制原理

在 Minecraft 中，`@a[y=200,dy=500]` 使用 `dx`/`dy`/`dz` 立方体区域选择器。当只指定 `y` 和 `dy` 时，`x` 和 `z` 会默认使用命令执行位置的坐标，而 `dx` 和 `dz` 默认值为 0。这意味着如果不使用 `execute at @s`，选择器会锁定在命令方块或玩家的 x/z 坐标上，导致只有与执行者 x/z 相同的玩家才能被匹配。通过 `execute as @a at @s`，每个玩家都会以自身位置作为参考点，从而正确检测任意位置的玩家。dy 为负值时，检测方向变为向下，即从 y 坐标向下延伸 dy 绝对值的高度。Predicate 方式则直接使用 `entity_properties` 条件中的 `location.position.y` 字段，通过 `min`/`max` 指定 Y 轴范围，无需考虑执行位置问题。

## 注意事项

- dy 检测方式在命令方块中运行时，若不使用 execute at @s，x/z 会锁定为命令方块坐标，导致检测失效
- dy 为负值时，y 参数应设为检测范围的最高点（如 y=-30,dy=-500 检测 -30 以下）
- Predicate 方式仅适用于 Java 版，且 1.20.5 前需要数据包（1.20.5+ 已内置 predicate 支持）
- dx/dy/dz 选择器在 1.13+ 版本中行为一致，无版本差异
