---
id: t0454
title: "F键检测·前后帧存储法"
title_en: "f_key_detection_frame_diff"
layer: technique
source_url: ""
source_type: manual
version_min: "1.20.5"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["input", "fkey", "inventory_changed", "storage", "macro", "frame_diff"]
verified_in_game: false
---

## 核心洞见

通过在 Storage 中保存上一帧的主副手 NBT，当 inventory_changed 触发时对比"当前副手 vs 历史主手"与"当前主手 vs 历史副手"，若完全一致则判定为 F 键交换——核心优化在于用 Storage 内部操作（5~8单位）代替反复读取玩家实体 NBT（~160单位）。

## 代码示例

```mcfunction
# load.mcfunction
scoreboard objectives add <namespace> dummy
scoreboard objectives add <namespace>.id dummy
execute in overworld run forceload add -1 -1 1 1
execute in overworld run function <namespace>:load/item_display
```

```mcfunction
# load/item_display.mcfunction
execute if entity a-b-c-d-2 run return 0
execute in overworld run return run summon item_display 0 0 0 {Tags:["<namespace>.persistent"],UUID:uuid("a-b-c-d-2"),view_range:0}
```

```json
// advancement/fkey_detect.json
{"criteria": {"a": {"trigger": "minecraft:inventory_changed"}}, "rewards": {"function": "<namespace>:fkey/check"}}
```

```mcfunction
# fkey/check.mcfunction
# 1. 空手特判
execute unless items entity @s weapon.mainhand * unless items entity @s weapon.offhand * run return run advancement revoke @s only <namespace>:fkey_detect

# 2. 准备玩家 ID（懒初始化）
execute unless score @s <namespace>.id matches -2147483648.. store result score @s <namespace>.id run scoreboard players add id <namespace> 1
execute store result storage <namespace>:io id int 1 run scoreboard players get @s id

# 3. 打开数据（宏：从 storage 数组中按 id 取出该玩家的历史数据）
function <namespace>:fkey/open with storage <namespace>:io

# 4. 比较逻辑
function <namespace>:fkey/compare

# 5. 写回数据
function <namespace>:fkey/close with storage <namespace>:io

# 6. 撤销进度（放最后，防止内部 item 操作再次触发）
advancement revoke @s only <namespace>:fkey_detect
```

```mcfunction
# fkey/open.mcfunction（宏函数）
$data modify storage <namespace>:io player set from storage <namespace>:data player[{id:$(id)}]
```

```mcfunction
# fkey/compare.mcfunction
# 一次性读取当前主副手到 io temp，避免后续多次读取玩家实体 NBT
data modify storage <namespace>:io temp set value {now_main:{},now_off:{}}
data modify storage <namespace>:io temp.now_main set from entity @s SelectedItem
data modify storage <namespace>:io temp.now_off set from entity @s equipment.offhand

# 判断逻辑：store success 在数据相同时返回 0（data modify 覆盖后值未变化）
execute store success score #main_match <namespace> run data modify storage <namespace>:io player.prev_main set from storage <namespace>:io temp.now_off
execute store success score #off_match  <namespace> run data modify storage <namespace>:io player.prev_off  set from storage <namespace>:io temp.now_main
execute store success score #diff_match <namespace> run data modify storage <namespace>:io player.prev_off  set from storage <namespace>:io player.prev_main

# 三个条件同时满足 → F 键被按下
execute if score #main_match <namespace> matches 0 if score #off_match <namespace> matches 0 if score #diff_match <namespace> matches 1 run function <namespace>:fkey/on_press

# 更新历史数据为当前状态
data modify storage <namespace>:io player.prev_main set from storage <namespace>:io temp.now_main
data modify storage <namespace>:io player.prev_off  set from storage <namespace>:io temp.now_off
```

```mcfunction
# fkey/on_press.mcfunction — 拦截 F 键并还原物品位置（可选）
item replace entity a-b-c-d-2 contents from entity @s weapon.mainhand
item replace entity @s weapon.mainhand from entity @s weapon.offhand
item replace entity @s weapon.offhand from entity a-b-c-d-2 contents

# 同步还原 storage 中的历史数据
data modify storage <namespace>:io temp.swap        set from storage <namespace>:io player.prev_main
data modify storage <namespace>:io player.prev_main set from storage <namespace>:io player.prev_off
data modify storage <namespace>:io player.prev_off  set from storage <namespace>:io temp.swap
```

```mcfunction
# fkey/close.mcfunction（宏函数）
$data modify storage <namespace>:data player[{id:$(id)}] set from storage <namespace>:io player
```

## 文件结构

- `data/<namespace>/functions/load.mcfunction` — 初始化计分板、forceload、召唤世界实体
- `data/<namespace>/functions/load/item_display.mcfunction` — 幂等召唤持久化 item_display
- `data/<namespace>/advancements/fkey_detect.json` — inventory_changed 触发器
- `data/<namespace>/functions/fkey/check.mcfunction` — 主检测逻辑（ID分配、open/compare/close）
- `data/<namespace>/functions/fkey/open.mcfunction` — 宏函数，按 id 从 storage 数组读取历史数据
- `data/<namespace>/functions/fkey/compare.mcfunction` — 帧差分比较逻辑
- `data/<namespace>/functions/fkey/close.mcfunction` — 宏函数，将历史数据写回 storage 数组
- `data/<namespace>/functions/fkey/on_press.mcfunction` — F键触发后的自定义逻辑（含可选还原）

## 用法

构建完数据包即可在游戏内测试效果。在 `fkey/on_press.mcfunction` 中填写 F 键按下后的自定义逻辑。需要宏函数支持（1.20.2+）。

## 使用场景

- 同 t0447（物品标记法），但适合不希望修改物品 custom_data 的场景
- 主副手物品 NBT 较复杂、不适合被 item_modifier 反复写入的场景
- 不适合主副手物品 NBT 完全相同的情况（无法区分交换前后）

## 机制原理

每次 inventory_changed 触发时，检测函数从 Storage 中取出该玩家上一帧的主副手 NBT（prev_main、prev_off），与当前帧的主副手 NBT 做交叉比对：
- 用当前副手 `now_off` 覆盖 `prev_main`，若 `store success` 返回 0，说明两者相同（覆盖前后值未变）
- 用当前主手 `now_main` 覆盖 `prev_off`，同理
- 再检查历史主副手不同（`diff_match=1`，排除主副手原本就一样的情况）

三个条件同时满足 → 主副手发生了完整互换 → 判定 F 键被按下。

**性能优化关键**：在 compare 函数开始时一次性将玩家当前主副手读入 `io temp`（此步消耗约 160 单位），后续所有比较均在 Storage 内部进行（约 5~8 单位/次），而非反复读取玩家实体 NBT。

**宏函数的作用**：open/close 使用宏将玩家 ID 动态注入 storage 路径，实现对 `storage ns:data player[{id:N}]` 这个"按 ID 索引的玩家数据数组"的精确读写。

## 注意事项

- **未完整验证**，存在逻辑可能无法正常工作的风险，建议优先使用 t0447 物品标记法
- 主副手物品 NBT 完全相同时无法检测（交换前后 Storage 数据不变，三个条件不满足）
- open/close 是宏函数，需要 1.20.2+，且宏缓存命中率取决于玩家 ID 分布
- compare 中 `store success` 的语义是"修改是否真正发生了变化"，若覆盖前后值相同则返回 0
- 还原物品位置时必须同步还原 storage 历史数据，否则下次对比逻辑会出错
