---
id: t0493
title: "玩家视线谓词"
title_en: "looking_at_predicate_advancement"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/lookat"
source_type: "mcc_wiki"
source_issue: "questions/lookat"
version_min: "1.17"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["predicate", "advancement", "视线检测", "player", "望远镜"]
verified_in_game: false
---

## 核心洞见

Java 版提供 player 类型特定的 looking_at 谓词，可直接检测玩家是否看向某类实体，无需复杂命令

## 代码示例

```mcfunction
# 函数 example:tick
execute as @a[predicate=example:looking_cow] run say Hi, cow!

# 谓词 example:looking_cow
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "type_specific": {
      "type": "minecraft:player",
      "looking_at": {
        "type": "minecraft:cow"
      }
    }
  }
}

# 或使用 advancement 方式（需要望远镜）
# 进度 example:lookat/cow
{
  "criteria": {
    "requirement": {
      "trigger": "minecraft:using_item",
      "conditions": {
        "player": [
          {
            "condition": "minecraft:entity_properties",
            "entity": "this",
            "predicate": {
              "type_specific": {
                "type": "minecraft:player",
                "looking_at": {
                  "type": "minecraft:cow"
                }
              }
            }
          }
        ],
        "item": {
          "items": "minecraft:spyglass"
        }
      }
    }
  },
  "rewards": {
    "function": "example:lookat/cow"
  }
}

# 函数 example:lookat/cow
advancement revoke @s only example:lookat/cow
say I am looking at a cow
```

## 文件结构

- data/example/functions/tick.mcfunction
- data/example/predicates/looking_cow.json
- data/example/advancements/lookat/cow.json
- data/example/functions/lookat/cow.mcfunction

## 用法

构建数据包后，方式一：在 tick 函数中使用 predicate 检测，自动对所有玩家生效；方式二：玩家使用望远镜看向目标实体时自动触发 advancement 奖励函数。

## 使用场景

['检测玩家是否看向特定类型的实体（如所有牛、所有玩家）', '结合望远镜机制实现"瞄准"交互（如望远镜瞄准怪物时显示信息）', '作为 execute 视线检测的简化替代方案，但只能检测实体类型，不能检测具体实例或坐标']

## 机制原理

Java 版为玩家实体类型提供了特殊的 type_specific 谓词，其中包含 looking_at 字段。该字段可以指定一个实体谓词，当玩家视线中正好有符合条件的实体时返回 true。这个机制是 Minecraft 原版用于望远镜成就（如看向苦力怕、末影人、骷髅等）的底层实现。注意该谓词只能检测玩家是否看向某个实体类型，不能检测具体实体实例或方块位置。advancement 方式则额外要求玩家正在使用望远镜，这是原版成就系统的直接复用。

## 注意事项

- looking_at 谓词只能检测实体类型（如 type、tag），不能检测具体实体实例或坐标
- advancement 方式需要玩家使用望远镜才能触发
- 该功能是 Java 版特有，基岩版没有对应的谓词
- 检测精度由游戏内部决定，无法调整视角宽容度
