---
id: t0476
title: "谓词检测任意槽位物品"
title_en: "predicate_detect_item_any_slot"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/detectitem"
source_type: "mcc_wiki"
source_issue: "questions/detectitem"
version_min: "1.20.5"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["predicate", "item detection", "slot detection", "1.20.5"]
verified_in_game: false
---

## 核心洞见

1.20.5+ 的谓词（predicate）可检测任意槽位（不仅是装备槽），且支持内联使用，无需数据包文件。

## 代码示例

```mcfunction
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "slots": {
      "weapon.mainhand": {
        "items": "minecraft:stick",
        "count": {
          "min": 1
        },
        "predicates": {
          "minecraft:custom_data": {"awesome_stick": true}
        }
      }
    }
  }
}

# 内联使用（无需数据包）
execute if predicate {condition: 'minecraft:weather_check', raining: true} run say Is raining
```

## 文件结构

- data/<namespace>/predicates/<predicate_name>.json

## 用法

将谓词文件放入数据包后，可在目标选择器、`execute if predicate`、战利品表和进度中引用。内联谓词可直接在命令中使用。

## 使用场景

['在数据包中创建可复用的物品检测条件，用于进度、战利品表或自定义机制。', '需要检测非装备槽位（如副手、盔甲栏、容器）中的物品时，使用 `slots` 字段替代旧的 `equipment` 字段。', '在命令方块中快速使用简单谓词（如天气检测），无需创建数据包文件。']

## 机制原理

1.20.5 更新了谓词系统：1) `slots` 字段替代了 `equipment`，支持检测任意槽位（如 `weapon.mainhand`、`armor.chest`、`container.*`）；2) `items` 字段接受单个物品、物品标签或物品列表；3) `predicates` 字段支持组件子谓词（如 `minecraft:custom_data`）；4) 谓词可内联在 `execute if predicate` 命令中，无需数据包文件。这使得物品检测更灵活、更易用。

## 注意事项

- 若在谓词中不检测物品 ID 而只检测 NBT 数据，需同时检测物品数量（count），以规避 MC-229882 漏洞。
- 内联谓词仅支持简单条件，复杂逻辑仍需创建数据包文件。
- 此功能仅适用于 1.20.5 及以上版本。
