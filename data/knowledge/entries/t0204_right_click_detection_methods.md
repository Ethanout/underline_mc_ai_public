---
id: t0204
title: "右键检测方法"
title_en: "right_click_detection_methods"
layer: technique
source_url: "data/archive/drafts/Q01_按键检测.md"
source_type: "manual"
source_issue: ""
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["right_click", "detection", "interaction", "consumable", "using_item", "carrot_on_a_stick", "state_machine"]
verified_in_game: false
---

## 核心洞见

数据包不能直接读取通用的鼠标右键状态，需要把右键转化为可监听的游戏事件。选择方案时应先确定是否允许绑定特定物品，以及需要检测单次点击、持续按住、松开，还是点击特定区域。

- **普通单次点击**：使用胡萝卜钓竿或诡异菌钓竿的 `used:<item>` 计分项，兼容性和性能最好。
- **按下、按住、松开三态检测**：1.21.5+ 推荐使用 `consumable` 组件、`using_item` 进度和计分板状态机。
- **点击特定区域或实体**：1.19.4+ 使用 `interaction` 实体，可区分左键和右键并记录交互目标。

## 方案选择

| 方案 | 版本 | 手持物品依赖 | 可检测状态 | 主要局限 |
|---|---|---|---|---|
| 胡萝卜钓竿计分项 | 1.13+ | 是 | 单次使用 | 胡萝卜钓竿会吸引猪 |
| 诡异菌钓竿计分项 | 1.16+ | 是 | 单次使用 | 会与骑乘炽足兽的原版行为冲突 |
| `interaction` 实体 | 1.19.4+ | 否 | 点击实体/区域 | 需要维护实体，只能检测其交互范围 |
| `consumable` + `using_item` | 1.21.5+ | 是 | 按下、按住、完成、松开 | 需要自定义检测物品和每 tick 状态机 |

## 代码示例

### 单次右键：钓竿计分项

初始化：

```mcfunction
scoreboard objectives add click_rmb used:carrot_on_a_stick
```

每 tick 检测并清零：

```mcfunction
execute as @a[scores={click_rmb=1..}] run function <namespace>:right_click/on_press
scoreboard players set @a click_rmb 0
```

也可以改用 `used:warped_fungus_on_a_stick`，避免与胡萝卜钓竿用途冲突。

### 全状态右键检测：Consumable 布尔移位寄存器

给检测物品添加极长的使用时间，使玩家按住右键时持续触发 `using_item`：

```mcfunction
give @s firework_star[consumable={animation:"none",has_consume_particles:false,consume_seconds:9999,sound:{sound_id:"none"}},custom_data={<namespace>:{right_click_detector:1b}}]
```

初始化计分项和除数：

```mcfunction
scoreboard objectives add <namespace>.state dummy
scoreboard objectives add <namespace> dummy
scoreboard players set 2 <namespace> 2
```

`data/<namespace>/advancement/right_click/using.json`：

```json
{
  "criteria": {
    "a": {
      "trigger": "minecraft:using_item"
    }
  },
  "rewards": {
    "function": "<namespace>:right_click/using"
  }
}
```

奖励函数必须撤销进度，以便下一 tick 再次触发：

```mcfunction
# <namespace>:right_click/using
advancement revoke @s only <namespace>:right_click/using
scoreboard players add @s <namespace>.state 4
```

玩家 tick 函数：

```mcfunction
# 信号每 tick 自动衰减；using_item 持续为其注入脉冲
scoreboard players operation @s <namespace>.state /= 2 <namespace>

execute if score @s <namespace>.state matches 2 run function <namespace>:right_click/on_press
execute if score @s <namespace>.state matches 3 run function <namespace>:right_click/while_hold
execute if score @s <namespace>.state matches 1 run function <namespace>:right_click/on_release
```

这里的分数可以理解为一个布尔列表或移位寄存器。每 tick 除以 `2` 等价于将历史采样右移一位；检测到当前帧正在使用物品时，`add 4` 等价于将高位设为 `1`：

```text
二进制位：[当前帧, 上一帧, 上上帧]
触发时：  state |= 0b100
每 tick： state >>= 1
检测state
```

计分板没有直接的按位 OR 操作。只要注入前的高位确定为 `0`，`scoreboard players add ... 4` 就等价于 `state |= 0b100`。

三位版本的状态含义：

| 状态值 | 含义 |
|---|---|
| `0` | 空闲 |
| `2` | 刚按下 |
| `3` | 按住中 |
| `1` | 刚松开 |

连续按住时的状态转移为：

```text
000 -> [设高位] 100 -> [右移] 010 刚按下
010 -> [设高位] 110 -> [右移] 011 按住中
011 -> [设高位] 111 -> [右移] 011 按住中
011 -> [未触发，仅右移] 001 刚松开 -> 000 空闲
```

信号可能短暂中断时，可以增加寄存器位宽。例如把奖励函数中的 `add 4` 改为 `add 8`，相当于把当前输入写入第四位 `0b1000`，保留更多历史采样作为防抖缓冲。此时按下、按住和松开的判定值也必须按四位状态重新设计，不能继续直接使用三位版本的 `2`、`3`、`1`，而是按下为`add的数>>1`，按住为`非0的其他情况`，松开为`1`。

## 用法

1. 只需要技能、法杖等物品的单次右键事件时，优先使用 `used:<item>` 计分项。
2. 需要蓄力、持续施法或松开触发时，为专用物品添加 `consumable`，并使用 `using_item` 状态机。
3. 需要检测玩家对世界中特定位置的右键时，使用 `interaction` 实体，而不是物品使用事件。
4. 使用进度奖励函数监听事件时，必须在奖励函数中撤销对应进度，否则每位玩家只会触发一次。

## 使用场景

- 法杖、枪械、菜单物品等右键技能
- 长按蓄力、持续施法和松开发射
- 区分按下、按住、松开的输入状态
- 无方块模型的交互区域或自定义实体交互

## 机制原理

`used:<item>` 计分项监听玩家成功使用指定物品的次数，适合离散的单次事件。`using_item` 进度会在玩家持续使用物品期间反复触发；配合 `consumable` 组件可以让原本不能持续使用的物品进入使用状态。

这个方法本质上是用一个整数保存最近数 tick 的布尔输入历史。奖励函数把当前输入写入高位，tick 函数通过除以二完成逻辑右移。位模式从全零变为只有较高位为一时表示按下沿，连续的一表示按住，停止写入后仅剩低位的一表示松开沿。增加高位权重和寄存器位宽，可以保留更长的输入历史并实现防抖。

`interaction` 实体监听的是玩家与指定实体的交互，因此不依赖手持物品，但它检测的是实体交互范围，而不是任意位置的通用右键。完整的跟随实体系统见 `t0519_interaction_entity_click_detector`。

## 注意事项

- 数据包无法直接检测任意情况下的通用右键；所有方案都依赖物品使用或实体交互等可监听事件。
- `consumable` 状态机需要在玩家上下文中每 tick 执行，且检测物品必须能够持续进入使用状态。
- `consume_seconds: 0` 适合瞬时点击；极大的 `consume_seconds` 适合检测按住与松开；指定有限时间则适合检测长按完成。
- 使用 `consume_item` 检测完成事件时，可配合 `use_remainder` 返还检测物品。
- 钓竿方案应注意原版生物吸引和骑乘控制行为。
- `interaction` 实体方案需要处理实体创建、绑定、清理及多人隔离。
