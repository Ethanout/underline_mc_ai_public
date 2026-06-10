---
id: t0464
title: "多区域玩家检测"
title_en: "multi_area_player_detection"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/areas"
source_type: "mcc_wiki"
source_issue: "questions/areas"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["player_detection", "area_check", "gamemode_switch", "tag_system", "predicate", "marker_entity"]
verified_in_game: false
---

## 核心洞见

通过标签或谓词组合多个区域检测，避免玩家在多个区域间被错误切换游戏模式。

## 代码示例

```mcfunction
```mcfunction
# Command blocks / tick function
tag @a remove inArea
tag @a[x=0,y=0,z=0,distance=..X] add inArea
tag @a[x=100,y=64,z=100,dx=70,dy=16,dz=28] add inArea
....
gamemode adventure @a[tag=inArea]
gamemode survival @a[tag=!inArea]
```

```mcfunction
# 优化版本，避免不必要的游戏模式切换
gamemode adventure @a[tag=inArea,gamemode=!adventure]
gamemode survival @a[tag=!inArea,gamemode=!survival]
```

```mcfunction
# Anchor entities 方法 - 召唤标记实体
summon marker <pos> {Tags:["adventure_area"]}

# Command blocks / tick function
execute as @a[gamemode=survival] at @s if entity @e[type=marker,tag=adventure_area,distance=..X,limit=1] run gamemode adventure
execute as @a[gamemode=adventure] at @s unless entity @e[type=marker,tag=adventure_area,distance=..X,limit=1] run gamemode survival
```

```mcfunction
# Block layer 方法 - 检测玩家脚下的方块层（1.20.5+）
execute as @a at @s if predicate {condition:"entity_properties",entity:"this",predicate:{flags:{is_sneaking:false}}} if block ~ -63 ~ minecraft:red_concrete run say You have been found!
```

```json
// Predicates 方法 - 检查多个立方体区域
{
  "condition": "minecraft:any_of",
  "terms": [
    {
      "condition": "minecraft:location_check",
      "predicate": {
        "position": {
          "x": {
            "min": 10,
            "max": 20
          },
          "y": {
            "min": 64,
            "max": 70
          },
          "z": {
            "min": 30,
            "max": 40
          }
        }
      }
    },
    {
      "condition": "minecraft:location_check",
      "predicate": {
        "position": {
          "x": {
            "min": 60,
            "max": 85
          },
          "y": {
            "min": -20,
            "max": 10
          },
          "z": {
            "min": 10,
            "max": 80
          }
        }
      }
    },
    {
      "condition": "minecraft:location_check",
      "predicate": {
        "position": {
          "x": {
            "min": -80,
            "max": -20
          },
          "y": {
            "min": 125,
            "max": 155
          },
          "z": {
            "min": 55,
            "max": 78
          }
        }
      }
    }
  ]
}
```
```

## 文件结构

- data/<namespace>/functions/tick.mcfunction
- data/<namespace>/predicates/area_check.json

## 用法

构建完数据包即可在游戏内测试效果。对于硬编码位置和锚点实体方法，将命令放入 tick 函数或命令方块中持续运行；对于谓词方法，在 tick 函数中通过 `execute if predicate <namespace>:area_check` 调用。

## 使用场景

['在服务器中设置多个安全区（如出生点、商店区），玩家进入自动切换为冒险模式，离开恢复生存模式', '检测玩家是否进入特定形状的复杂区域（如不规则地形上的建筑区域）', '需要同时检测多个不重叠的球形、立方体或圆柱形区域时']

## 机制原理

朴素方法直接使用 `@a[x=0,y=0,z=0,distance=..X]` 和 `@a[x=0,y=0,z=0,distance=X..]` 分别设置游戏模式，但当有多个区域时，玩家在一个区域内会被另一个区域的 `distance=X..` 条件匹配到，导致模式被错误覆盖。

硬编码位置方法通过标签系统解决：先清除所有玩家的 `inArea` 标签，然后对每个区域分别添加标签，最后根据标签统一设置游戏模式。这样每个区域独立检测，互不干扰。

锚点实体方法利用 marker 实体作为区域中心点，通过 `execute if entity @e[type=marker,tag=adventure_area,distance=..X]` 检测玩家是否在任意一个标记点附近。这种方法适合大量球形区域，只需在目标位置放置标记实体即可。

Block layer 方法在地图下方（Y=-63）放置特定方块层，通过 `if block ~ -63 ~ <block>` 检测玩家脚下的方块类型，适合任意不规则形状的区域。

谓词方法使用 `minecraft:any_of`（1.20+）或 `minecraft:alternative`（1.14-1.19.4）条件组合多个 `minecraft:location_check`，每个 location_check 定义一个立方体区域的范围（x、y、z 的 min/max）。这种方法无需命令方块或函数循环，直接在谓词中定义所有区域，代码更简洁。

## 注意事项

- 硬编码位置方法中，每个区域需要单独一行命令，区域数量多时命令会很长
- 锚点实体方法在 1.17+ 推荐使用 marker 实体，1.17 之前可用 armor_stand 或 area_effect_cloud
- Block layer 方法需要在地图下方放置方块层，可能影响世界生成或需要额外维护
- 谓词方法中的 `minecraft:alternative` 在 1.20+ 被 `minecraft:any_of` 替代，旧版本需使用 alternative
- 优化版本添加 `gamemode=!adventure` 和 `gamemode=!survival` 条件可避免不必要的游戏模式切换，减少聊天栏输出
- Bedrock 版需将选择器参数改为 Bedrock 语法：`distance=..X` → `r=X`，`distance=X..Y` → `r=Y,rm=X`，`distance=X..` → `rm=X`
