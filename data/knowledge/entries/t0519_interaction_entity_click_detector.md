---
id: t0519
title: "Interaction 实体左右键检测系统"
title_en: "interaction_entity_click_detector"
layer: technique
source_url: "data/archive/drafts/Q01_按键检测.md"
source_type: "manual"
source_issue: ""
version_min: "1.19.4"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["interaction", "left_click", "right_click", "player_hurt_entity", "player_interacted_with_entity", "entity_binding"]
verified_in_game: false
---

## 核心洞见

`interaction` 实体能够分别记录玩家对它的左键攻击和右键交互。让每位玩家绑定一个检测实体，并持续将实体传送到玩家附近，即可在不依赖手持物品的情况下近似检测通用左右键。

该方案兼容 1.19.4+，但并非首选：实体可能因 tick 与传送延迟跟丢玩家，导致漏检；持续传送还会增加服务器运算和网络同步开销。

本文给出一个完整、可独立创建的数据包模块。将所有 `<namespace>` 替换成自己的命名空间，例如 `click_detect`。

## 版本目录差异

下文所有路径使用 **1.21+** 的目录命名：

| 1.21+ 路径 | 1.19.4 至 1.20.6 路径 |
|---|---|
| `data/<namespace>/function/` | `data/<namespace>/functions/` |
| `data/<namespace>/advancement/` | `data/<namespace>/advancements/` |
| `data/minecraft/tags/function/` | `data/minecraft/tags/functions/` |

在 1.19.4 至 1.20.6 中使用本方案时，必须把文件夹名称替换成右列的复数形式。函数 ID 和进度 ID 本身不变，例如文件路径虽然是 `functions/load.mcfunction`，调用时仍写 `<namespace>:load`。

## 完整文件结构

以下结构适用于 **1.21+**：

```text
data/
├── minecraft/
│   └── tags/
│       └── function/
│           ├── load.json
│           └── tick.json
└── <namespace>/
    ├── advancement/
    │   ├── left_click/
    │   │   └── using.json
    │   └── right_click/
    │       └── using.json
    └── function/
        ├── load.mcfunction
        ├── tick.mcfunction
        ├── player/
        │   └── tick.mcfunction
        ├── click_detector/
        │   ├── summon.mcfunction
        │   ├── tp_and_keep_single.mcfunction
        │   └── cleanup.mcfunction
        ├── left_click/
        │   ├── using.mcfunction
        │   ├── check_owner.mcfunction
        │   └── on_press.mcfunction
        └── right_click/
            ├── using.mcfunction
            ├── check_owner.mcfunction
            └── on_press.mcfunction
```

## 调用关系

```text
#minecraft:load
└── <namespace>:load

#minecraft:tick
└── <namespace>:tick
    ├── 每位玩家执行 <namespace>:player/tick
    │   ├── 找到已绑定实体 -> <namespace>:click_detector/tp_and_keep_single
    │   └── 没有已绑定实体 -> <namespace>:click_detector/summon
    └── 每个检测实体执行 <namespace>:click_detector/cleanup

玩家左键攻击检测实体
└── advancement left_click/using
    └── <namespace>:left_click/using
        ├── <namespace>:left_click/check_owner
        └── <namespace>:left_click/on_press

玩家右键交互检测实体
└── advancement right_click/using
    └── <namespace>:right_click/using
        ├── <namespace>:right_click/check_owner
        └── <namespace>:right_click/on_press
```

## 第一步：注册 Load 和 Tick 函数

创建 `data/minecraft/tags/function/load.json`：

```json
{
  "values": [
    "<namespace>:load"
  ]
}
```

创建 `data/minecraft/tags/function/tick.json`：

```json
{
  "values": [
    "<namespace>:tick"
  ]
}
```

这两个函数标签不可省略。缺少它们时，初始化函数和每 tick 主循环都不会自动执行。

## 第二步：创建初始化函数

创建 `data/<namespace>/function/load.mcfunction`：

```mcfunction
# 通用临时变量和全局自增 ID
scoreboard objectives add <namespace> dummy

# 玩家自己的唯一 ID
scoreboard objectives add <namespace>.id dummy

# interaction 实体所绑定玩家的 ID
scoreboard objectives add <namespace>.owner dummy

# 初始化全局 ID 计数器
scoreboard players add #next_id <namespace> 0

# 数据包重载后撤销进度，确保玩家可以再次触发
advancement revoke @a only <namespace>:left_click/using
advancement revoke @a only <namespace>:right_click/using
```

三个计分项目标的用途：

| 目标 | 用途 |
|---|---|
| `<namespace>` | 保存 `#next_id`、`#id`、`#has_entity`、`#event_found` 等全局临时分数 |
| `<namespace>.id` | 保存每位玩家的唯一 ID |
| `<namespace>.owner` | 保存每个检测实体所属玩家的 ID |

## 第三步：创建主 Tick 函数

创建 `data/<namespace>/function/tick.mcfunction`：

```mcfunction
# 为每位可检测玩家创建或更新检测实体
execute as @a[gamemode=!spectator] at @s run function <namespace>:player/tick

# 清理附近没有对应玩家的遗留检测实体
execute as @e[type=minecraft:interaction,tag=<namespace>.click_detector] at @s run function <namespace>:click_detector/cleanup
```

如果不希望影响创造模式玩家，可以把第一条命令改为：

```mcfunction
execute as @a[gamemode=!creative,gamemode=!spectator] at @s run function <namespace>:player/tick
```

## 第四步：为玩家分配并更新检测实体

创建 `data/<namespace>/function/player/tick.mcfunction`：

```mcfunction
# 尚无 ID 的玩家从全局计数器领取唯一 ID
execute unless score @s <namespace>.id matches -2147483648.. run scoreboard players add #next_id <namespace> 1
execute unless score @s <namespace>.id matches -2147483648.. run scoreboard players operation @s <namespace>.id = #next_id <namespace>

# 默认认为没有找到该玩家的检测实体
scoreboard players set #has_entity <namespace> 0

# 把当前玩家 ID 复制到临时分数，供实体上下文比较
scoreboard players operation #id <namespace> = @s <namespace>.id

# 找到 owner 与当前玩家 ID 相同的实体，传送它并删除重复实体
execute as @e[type=minecraft:interaction,tag=<namespace>.click_detector] if score @s <namespace>.owner = #id <namespace> run function <namespace>:click_detector/tp_and_keep_single

# 没找到实体时，在玩家眼睛位置创建一个
execute if score #has_entity <namespace> matches 0 anchored eyes positioned ^ ^ ^ run function <namespace>:click_detector/summon
```

这里的 `@s` 在函数开始时是玩家；进入 `execute as @e[...]` 后才变为检测实体。

## 第五步：创建检测实体

创建 `data/<namespace>/function/click_detector/summon.mcfunction`：

```mcfunction
# 此函数以玩家为 @s，并位于玩家眼睛位置
summon minecraft:interaction ~ ~ ~ {Tags:["<namespace>.click_detector","<namespace>.init"],width:1.8f,height:1.8f,response:0b}

# 将新实体的 owner 设置为当前玩家 ID
scoreboard players operation @e[type=minecraft:interaction,tag=<namespace>.init,limit=1,sort=nearest] <namespace>.owner = @s <namespace>.id

# 移除临时初始化标签
tag @e[type=minecraft:interaction,tag=<namespace>.init,limit=1,sort=nearest] remove <namespace>.init
```

`response:0b` 表示交互实体不播放默认的手部摆动响应。可根据实际需求调整实体的 `width` 和 `height`。

## 第六步：传送实体并删除重复项

创建 `data/<namespace>/function/click_detector/tp_and_keep_single.mcfunction`：

```mcfunction
# 此函数以检测实体为 @s，但执行位置仍来自 player/tick 中的玩家位置

# 已经处理过一个实体时，当前实体是重复项，直接删除
execute if score #has_entity <namespace> matches 1 run return run kill @s

# 标记已经找到实体
scoreboard players set #has_entity <namespace> 1

# 把唯一保留的实体传送到玩家眼睛位置
tp @s ~ ~ ~
```

## 第七步：清理遗留实体

创建 `data/<namespace>/function/click_detector/cleanup.mcfunction`：

```mcfunction
# 此函数以检测实体为 @s
scoreboard players set #owner_online <namespace> 0
scoreboard players operation #owner_id <namespace> = @s <namespace>.owner

# 在线玩家中存在相同 ID 时，将标记设为 1
execute as @a if score @s <namespace>.id = #owner_id <namespace> run scoreboard players set #owner_online <namespace> 1

# 所属玩家不在线时删除实体
execute if score #owner_online <namespace> matches 0 run kill @s
```

该清理逻辑按绑定 ID 判断，不依赖实体与玩家的距离，因此不会在玩家快速移动时误删实体。

## 第八步：创建左键进度监听器

创建 `data/<namespace>/advancement/left_click/using.json`：

```json
{
  "criteria": {
    "attack_interaction": {
      "trigger": "minecraft:player_hurt_entity",
      "conditions": {
        "entity": {
          "type": "minecraft:interaction",
          "nbt": "{Tags:[\"<namespace>.click_detector\"]}"
        }
      }
    }
  },
  "rewards": {
    "function": "<namespace>:left_click/using"
  }
}
```

创建 `data/<namespace>/function/left_click/using.mcfunction`：

```mcfunction
# 此函数以触发左键的玩家为 @s
advancement revoke @s only <namespace>:left_click/using

# 临时标记触发玩家
tag @s add <namespace>.event_player
scoreboard players set #event_found <namespace> 0

# 找到 attack 记录中的 attacker 为当前玩家的检测实体
execute as @e[type=minecraft:interaction,tag=<namespace>.click_detector] if function <namespace>:left_click/check_owner run data remove entity @s attack

tag @s remove <namespace>.event_player

# 仅在找到属于该玩家的检测实体时运行响应
execute if score #event_found <namespace> matches 1 run function <namespace>:left_click/on_press
```

创建 `data/<namespace>/function/left_click/check_owner.mcfunction`：

```mcfunction
# 此函数以检测实体为 @s
execute on attacker if entity @s[tag=<namespace>.event_player] run scoreboard players set #event_found <namespace> 1
execute on attacker if entity @s[tag=<namespace>.event_player] run return 1
return 0
```

创建 `data/<namespace>/function/left_click/on_press.mcfunction`：

```mcfunction
# 此函数以点击玩家为 @s，在这里编写实际左键逻辑
title @s actionbar {"text":"检测到左键","color":"red"}
playsound minecraft:entity.experience_orb.pickup player @s ~ ~ ~ 1 1.5
```

## 第九步：创建右键进度监听器

创建 `data/<namespace>/advancement/right_click/using.json`：

```json
{
  "criteria": {
    "interact": {
      "trigger": "minecraft:player_interacted_with_entity",
      "conditions": {
        "entity": {
          "type": "minecraft:interaction",
          "nbt": "{Tags:[\"<namespace>.click_detector\"]}"
        }
      }
    }
  },
  "rewards": {
    "function": "<namespace>:right_click/using"
  }
}
```

创建 `data/<namespace>/function/right_click/using.mcfunction`：

```mcfunction
# 此函数以触发右键的玩家为 @s
advancement revoke @s only <namespace>:right_click/using

# 临时标记触发玩家
tag @s add <namespace>.event_player
scoreboard players set #event_found <namespace> 0

# 找到 interaction 记录中的 target 为当前玩家的检测实体
execute as @e[type=minecraft:interaction,tag=<namespace>.click_detector] if function <namespace>:right_click/check_owner run data remove entity @s interaction

tag @s remove <namespace>.event_player

# 仅在找到属于该玩家的检测实体时运行响应
execute if score #event_found <namespace> matches 1 run function <namespace>:right_click/on_press
```

创建 `data/<namespace>/function/right_click/check_owner.mcfunction`：

```mcfunction
# 此函数以检测实体为 @s
execute on target if entity @s[tag=<namespace>.event_player] run scoreboard players set #event_found <namespace> 1
execute on target if entity @s[tag=<namespace>.event_player] run return 1
return 0
```

创建 `data/<namespace>/function/right_click/on_press.mcfunction`：

```mcfunction
# 此函数以点击玩家为 @s，在这里编写实际右键逻辑
title @s actionbar {"text":"检测到右键","color":"green"}
playsound minecraft:ui.button.click player @s ~ ~ ~ 1 1
```

## 第十步：加载和测试

创建完所有文件后，在游戏中执行：

```mcfunction
reload
```

检查数据包是否加载：

```mcfunction
datapack list enabled
```

检查当前玩家是否获得唯一 ID：

```mcfunction
scoreboard players get @s <namespace>.id
```

检查是否创建检测实体：

```mcfunction
execute if entity @e[type=minecraft:interaction,tag=<namespace>.click_detector] run say detector_exists
```

查看检测实体数据：

```mcfunction
data get entity @e[type=minecraft:interaction,tag=<namespace>.click_detector,limit=1,sort=nearest]
```

## 机制原理

攻击 `interaction` 实体时，实体的 `attack` 数据记录攻击者；右键交互时，实体的 `interaction` 数据记录交互玩家。进度奖励函数先临时标记触发玩家，再遍历检测实体，通过 `execute on attacker` 或 `execute on target` 找到属于该玩家的事件，清除事件数据并运行响应函数。

唯一计分板 ID 用于保证每位玩家只绑定自己的检测实体。`#has_entity` 防止重复实体，`cleanup` 函数负责移除离线玩家遗留的实体。

## 常见故障

| 现象 | 检查项 |
|---|---|
| 完全没有实体生成 | 检查 `data/minecraft/tags/function/load.json` 和 `tick.json` 是否存在 |
| `/reload` 后没有计分项目标 | 检查 `<namespace>:load` 是否写入 load 标签，以及命名空间是否替换一致 |
| 左右键只触发一次 | 检查 `using.mcfunction` 是否撤销对应进度 |
| 点击触发但找不到玩家 | 检查 `.event_player` 标签，以及 `execute on attacker/target` 的上下文 |
| 多人互相串扰 | 检查玩家 `<namespace>.id` 与实体 `<namespace>.owner` 是否正确绑定 |
| 快速移动时漏检 | `interaction` 实体存在传送延迟；该问题无法完全消除 |
| 无法攻击或使用附近目标 | 检测实体拦截了点击；缩小尺寸或改用其他检测方案 |

## 注意事项

- 该方案检测的是玩家命中 `interaction` 实体的点击，并不是真正读取客户端按键状态。
- 实体尺寸和相对位置会影响命中率；尺寸过大会阻挡正常游戏交互。
- 实体持续传送存在一 tick 左右的跟随延迟，玩家快速移动或网络延迟时可能漏检。
- 每位玩家都需要独立实体；多人服务器必须处理 ID 绑定、重复实体和离线清理。
- 持续传送实体会消耗服务器性能和网络带宽，不适合玩家数量较多的服务器。
- 检测实体会拦截攻击和交互，可能影响破坏方块、攻击生物或使用方块。
- 左键空挥优先考虑 `t0517_left_click_detection_methods` 中的 1.21.11+ `piercing_weapon` 方案。
