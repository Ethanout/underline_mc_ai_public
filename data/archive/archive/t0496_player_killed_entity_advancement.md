---
id: t0496
title: "击杀检测"
title_en: "player_killed_entity_advancement"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/playerkills"
source_type: "mcc_wiki"
source_issue: "questions/playerkills"
version_min: "1.13"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["advancement", "entity_kill", "detection", "nbt_filter"]
verified_in_game: false
---

## 核心洞见

利用 advancement 的 player_killed_entity 触发器可以检测玩家击杀特定 NBT 的实体，而 scoreboard 无法做到

## 代码示例

```mcfunction
{
  "criteria": {
    "requirement": {
      "trigger": "minecraft:player_killed_entity",
      "conditions": {
        "entity": {
          "type": "minecraft:pig",
          "nbt": "{Tags:[\"example\"]}"
        }
      }
    }
  },
  "rewards": {
    "function": "example:kill_entity"
  }
}
```

## 文件结构

- data/example/advancements/kill_pig.json
- data/example/functions/kill_entity.mcfunction

## 用法

构建完数据包后，当玩家击杀符合条件的实体时，会自动触发 advancement 并执行奖励函数。无需手动调用。

## 使用场景

['需要检测玩家击杀带有特定标签的实体（如自定义Boss）', '需要检测玩家击杀特定类型的实体并执行后续逻辑（如统计、奖励）', '需要区分击杀不同 NBT 的同类实体（如不同变种的猪）']

## 机制原理

Minecraft 的 advancement 系统提供了 `player_killed_entity` 触发器，它可以在玩家击杀实体时触发，并且支持在 `conditions` 中检查实体的 `type` 和 `nbt`。这与 scoreboard 的 `minecraft.killed:minecraft.<entity>` 标准不同，scoreboard 只能统计击杀数量，无法区分实体的 NBT 数据（如标签）。通过 advancement 的 `rewards.function` 字段，可以在触发时自动执行一个函数，从而实现自定义逻辑。该机制的核心在于 advancement 触发器提供了比 scoreboard 更细粒度的条件过滤能力。

## 注意事项

- 此方法仅适用于 Java Edition
- advancement 触发器无法检测击杀实体的 NBT 数据中的某些动态变化（如计分板分数），只能检测静态 NBT（如 Tags）
- 如果不需要检测 NBT，可以省略 `nbt` 字段，只保留 `type` 字段
- 奖励函数会在击杀发生时以玩家身份执行（执行者为玩家）
