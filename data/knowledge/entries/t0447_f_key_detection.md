---
id: t0447
title: "F键检测·物品标记法"
title_en: "f_key_detection_item_tag"
layer: technique
source_url: ""
source_type: manual
version_min: "1.20.5"
version_max: ""
wiki_covers_this: false
confidence: high
tags: ["input", "fkey", "inventory_changed", "custom_data", "item_modifier"]
verified_in_game: false
---

## 核心洞见

F键不在原版 input 谓词中，但可在 tick 中给主副手物品打上不同 custom_data 标记，再通过 inventory_changed 进度检测标记是否错位，从而间接判定 F键被按下。

## 代码示例

```mcfunction
# load.mcfunction
scoreboard objectives add <namespace> dummy
scoreboard objectives add <namespace>.id dummy
advancement revoke @a only <namespace>:fkey_detect
execute in overworld run forceload add -1 -1 1 1
execute in overworld run function <namespace>:load/item_display
```

```mcfunction
# load/item_display.mcfunction — 创建持久化世界实体（用于物品操作寄存器）
execute if entity a-b-c-d-2 run return 0
execute in overworld run return run summon item_display 0 0 0 {Tags:["<namespace>.persistent"],UUID:uuid("a-b-c-d-2"),view_range:0}
```

```mcfunction
# tick.mcfunction
execute as @a at @s run function <namespace>:player/tick
```

```mcfunction
# player/tick.mcfunction — 每 tick 给主副手打标记
item modify entity @s weapon.mainhand <namespace>:tag_mainhand
item modify entity @s weapon.offhand <namespace>:tag_offhand
```

```json
// item_modifier/fkey/tag_mainhand.json
{"function": "minecraft:set_custom_data", "tag": "{<namespace>:{offhand:0b}}", "conditions": []}
```

```json
// item_modifier/fkey/tag_offhand.json
{"function": "minecraft:set_custom_data", "tag": "{<namespace>:{offhand:1b}}", "conditions": []}
```

```json
// advancement/fkey_detect.json
{"criteria": {"a": {"trigger": "minecraft:inventory_changed"}}, "rewards": {"function": "<namespace>:fkey/check"}}
```

```mcfunction
# fkey/check.mcfunction（实现一，推荐）
function <namespace>:fkey/check/is_swap
execute if items entity @s player.cursor *[custom_data~{<namespace>:{offhand:0b}}|custom_data~{<namespace>:{offhand:1b}}] run function <namespace>:fkey/check/enum/cursor
# 不能在一开始移除，防止逻辑内触发 check
advancement revoke @s only <namespace>:fkey_detect
```

```mcfunction
# fkey/check/is_swap.mcfunction
execute if items entity @s weapon.mainhand *[custom_data~{<namespace>:{offhand:1b}}] run return run function <namespace>:fkey/on_press
execute if items entity @s weapon.offhand *[custom_data~{<namespace>:{offhand:0b}}] run function <namespace>:fkey/on_press
```

```mcfunction
# fkey/check/enum/cursor.mcfunction — 用世界实体寄存器清除 cursor 上的标记
item replace entity a-b-c-d-2 contents from entity @s player.cursor
data remove entity a-b-c-d-2 item.components."minecraft:custom_data".<namespace>.offhand
item replace entity @s player.cursor from entity a-b-c-d-2 contents
```

实现二（更安全，对全背包槽位枚举清标记，性能略高）：check.mcfunction 里对
inventory.0~26、hotbar.0~8、armor.*、weapon.offhand、player.cursor 各槽位逐一检测并清除，每个槽位对应一个 enum/xxx.mcfunction，格式与 cursor 版相同。

## 文件结构

- `data/<namespace>/functions/load.mcfunction` — 初始化计分板、撤销进度、forceload、召唤世界实体
- `data/<namespace>/functions/load/item_display.mcfunction` — 幂等召唤持久化 item_display 世界实体
- `data/<namespace>/functions/tick.mcfunction` — 每 tick 遍历玩家
- `data/<namespace>/functions/player/tick.mcfunction` — 对主副手应用 item_modifier
- `data/<namespace>/item_modifiers/fkey/tag_mainhand.json` — 写入 offhand:0b 标记
- `data/<namespace>/item_modifiers/fkey/tag_offhand.json` — 写入 offhand:1b 标记
- `data/<namespace>/advancements/fkey_detect.json` — inventory_changed 触发器
- `data/<namespace>/functions/fkey/check.mcfunction` — 检测主入口
- `data/<namespace>/functions/fkey/check/is_swap.mcfunction` — 判断标记是否错位
- `data/<namespace>/functions/fkey/check/enum/cursor.mcfunction` — 清除 cursor 标记
- `data/<namespace>/functions/fkey/on_press.mcfunction` — F键触发后的自定义逻辑

## 用法

构建完数据包即可在游戏内测试效果。在 `fkey/on_press.mcfunction` 中填写 F 键按下后的自定义逻辑。

## 使用场景

- 检测玩家按下 F 键以触发自定义动作（切换武器、激活技能等）
- 数据包需要额外输入按键、F 键是最易实现的选项时
- 不适合需要区分"按下"与"长按"的场景（只能检测交换事件）

## 机制原理

F 键的本质效果是触发主副手物品交换。每 tick 通过 item_modifier 给主手写入 `offhand:0b`、副手写入 `offhand:1b`。F键按下后，两件物品位置互换，导致主手持有 `offhand:1b`、副手持有 `offhand:0b`——标记"错位"了。

inventory_changed 进度在任何物品栏变化时触发，奖励函数检测标记位置：
- 主手有 `offhand:1b` → 物品来自副手 → 发生了交换
- 副手有 `offhand:0b` → 物品来自主手 → 发生了交换

检测后必须清除物品上的标记，否则下次 tick 打标记时不会触发 inventory_changed（数据未变化）。清除方式：借助世界实体寄存器（item_display）做三步中转——读出、删除字段、写回。

`advancement revoke` 必须放在检测逻辑之后，防止 check 函数内部的 item 操作再次触发 inventory_changed → 递归触发 check。

## 注意事项

- 创造模式玩家物品副手持后可能无法堆叠回去（custom_data 不同导致无法与原先同类物品合并）
- 实现二比实现一更安全（覆盖全背包清标记），但对每个槽位都要写一个函数文件（可用脚本批量生成）
- load 中必须 `advancement revoke @a` 防止重启后玩家已拥有该进度导致首次无法触发
- 函数名里加点是合法的（如 `enum/inventory.0`）
