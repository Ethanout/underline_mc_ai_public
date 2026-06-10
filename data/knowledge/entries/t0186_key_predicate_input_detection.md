---
id: t0186
title: "WASD shift ctrl space按键检测"
title_en: "key_predicate_input_detection"
layer: technique
source_url: "https://modrinth.com/datapack/wasd-detection"
source_type: manual
version_min: "1.21"
version_max: ""
wiki_covers_this: false
confidence: high
tags: ["predicate", "input", "player", "movement"]
verified_in_game: false
quality: core
---

## 核心洞见

使用 entity_properties 谓词中的 input 字段可以检测玩家的 WASD、跳跃、潜行和疾跑按键状态。

## 代码示例

```mcfunction
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "type_specific": {
      "type": "minecraft:player",
      "input": { "jump": true }
    }
  }
}
```

## 用法

将谓词文件放置于 `data/<namespace>/predicate/` 下，通过 `/execute if predicate` 或目标选择器参数 `predicate=` 调用：

```mcfunction
# 检测玩家是否按下了前进键
execute as @a if predicate example:pressing_w run say 正在前进

# 通过目标选择器筛选按住潜行的玩家
execute as @a[predicate=example:sneaking] run say 正在潜行

# 检测玩家是否正在移动（任意方向）
execute as @a if predicate example:moving run say 正在移动
```

## 使用场景

- **技能系统**：根据玩家按键触发技能，例如按住 Shift + 前进释放冲刺技能。
- **动画控制**：检测玩家输入状态驱动自定义动画，如行走、跳跃动画。
- **移动限制**：配合 `ride` 或传送实现锁定玩家位置，需在每 tick 检测输入并强制回位。
- **交互式NPC**：玩家靠近NPC时按跳跃键触发对话。
- **小游戏**：根据按键状态计分或判断游戏行为，如"不许动"类游戏中检测玩家是否偷偷移动。
- **自定义疾跑**：替代原版疾跑逻辑，自定义疾跑消耗或效果。
- **AFK检测**：持续若干 tick 无任何输入即判定为挂机。

## 机制原理

entity_properties 谓词检查玩家实体的 type_specific 数据，其中 input 对象包含布尔值字段对应各按键。谓词返回 true 当按键被按下。

input 对象的完整字段：

| 字段 | 对应按键 | 说明 |
|------|----------|------|
| `forward` | W | 向前移动 |
| `backward` | S | 向后移动 |
| `left` | A | 向左移动 |
| `right` | D | 向右移动 |
| `jump` | 空格 | 跳跃 |
| `sneak` | Shift | 潜行 |
| `sprint` | Ctrl（双击W） | 疾跑 |

检测移动的组合谓词示例（`data/example/predicate/moving.json`）：

```mcfunction
{
  "condition": "minecraft:any_of",
  "terms": [
    { "condition": "minecraft:entity_properties", "entity": "this", "predicate": { "type_specific": { "type": "minecraft:player", "input": { "forward": true } } } },
    { "condition": "minecraft:entity_properties", "entity": "this", "predicate": { "type_specific": { "type": "minecraft:player", "input": { "backward": true } } } },
    { "condition": "minecraft:entity_properties", "entity": "this", "predicate": { "type_specific": { "type": "minecraft:player", "input": { "left": true } } } },
    { "condition": "minecraft:entity_properties", "entity": "this", "predicate": { "type_specific": { "type": "minecraft:player", "input": { "right": true } } } }
  ]
}
```

多个按键同时检测的写法（同时按住跳跃和潜行）：

```mcfunction
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "type_specific": {
      "type": "minecraft:player",
      "input": {
        "jump": true,
        "sneak": true
      }
    }
  }
}
```

## 注意事项

- input 字段仅在玩家实体上有效，其他实体类型会忽略。
- 按键检测是瞬时状态，需要每 tick 执行谓词才能持续响应。
- 常见误解：不需要额外工具或记分板，原版谓词即可实现。
- 仅检测客户端发送的输入意图，不保证玩家实际发生了位移（例如撞墙时 forward 仍为 true）。
- 此功能自 24w36a（1.21.2 快照）加入，1.21.2 以下版本不可用；1.21 可用的 Modrinth 数据包 "WASD Detection" 使用的是旧版替代方案（基于 flags/movement 子谓词间接推断）。
- `sprint` 检测的是疾跑状态而非 Ctrl 键本身，双击 W 进入疾跑同样触发。
- 在 `execute if predicate` 中，谓词的上下文实体为 `as` 指定的实体，需确保目标为玩家。
