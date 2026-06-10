---
id: t0482
title: "计分板ID系统"
title_en: "scoreboard_id_system"
layer: pattern
source_url: "https://minecraftcommands.github.io/wiki/questions/linkentity"
source_type: "mcc_wiki"
source_issue: "questions/linkentity"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: high
tags: ["计分板", "实体链接", "ID系统", "玩家追踪"]
verified_in_game: false
---

## 核心洞见

通过给玩家和实体分配相同的计分板分数，可以在逻辑上将两个实体链接起来，实现实体间的关联追踪。

## 代码示例

```mcfunction
# ── 初始化（load.mcfunction）──────────────────────────────
# 声明计分板 objective，ID 从 0 开始（#new 用来分配下一个可用 ID）
scoreboard objectives add ID dummy

# ── 方法一：进度触发（推荐，数据包版）────────────────────────
# advancement example:first_join
# {
#   "criteria": { "requirement": { "trigger": "minecraft:tick" } },
#   "rewards": { "function": "example:set_id" }
# }
# 进度触发 set_id：给第一次进入的玩家分配唯一 ID，自动递增 #new
# function example:set_id
execute store result score @s ID run scoreboard players add #new ID 1
# store result 把 add 的结果（新值）直接写入 @s 的 ID 分数
# 确保每个玩家拿到不同值：#new 每次 +1，@s 拿到那个新值

# ── 方法二：命令方块版（每 tick 处理一个新玩家）───────────────
# 给所有玩家初始化 ID 分数为 0（已有 ID 的玩家不受影响，因为 add 0 不变）
scoreboard players add @a ID 0
# 选出 ID 仍为 0 的玩家打上临时 tag，每 tick 只处理一个（@r 随机选一个）
tag @r[scores={ID=0}] add needsId
# 把 #new 的当前值赋给这个玩家
scoreboard players operation @a[tag=needsId] ID = #new ID
# #new 自增，准备下一次分配
execute as @a[tag=needsId] run scoreboard players add #new ID 1
# 清除临时 tag
tag @a remove needsId

# ── 将 ID 复制给关联实体（链接两个实体）─────────────────────
# 比如：把玩家的 ID 复制给刚召唤的宠物
scoreboard players operation @e[type=wolf,tag=my_pet,limit=1] ID = @s ID
# 之后就可以用 ID 值找到这只宠物
execute as @e[type=wolf,scores={ID=42}] run say 我是玩家 42 的宠物
```

## 文件结构

- data/example/functions/set_id.mcfunction
- data/example/advancements/first_join.json

## 用法

构建完数据包后，玩家首次进入游戏时会自动触发进度并分配唯一ID。之后可通过 `scoreboard players operation` 将玩家的ID分数复制到其他实体上，实现实体链接。

## 使用场景

['将宠物/坐骑与主人关联，实现跟随或传送功能', '在多人游戏中追踪每个玩家专属的投射物或召唤物', '实现玩家与自定义NPC的一对一绑定，用于任务系统或对话系统']

## 机制原理

该技术的核心是利用计分板系统为每个玩家分配一个唯一的整数ID。通过 `scoreboard players add #new ID 1` 或 `$total id` 这样的假玩家计数器，每次分配时自增1，确保每个玩家获得不同的分数。然后通过 `scoreboard players operation` 将玩家的ID分数复制到目标实体上，使实体和玩家拥有相同的分数值。最后通过 `execute as @e[scores={ID=<目标分数>}]` 或类似方法，可以找到具有相同分数的实体，从而实现逻辑上的链接。这种方法的特殊之处在于它不依赖NBT修改或UUID匹配，而是利用计分板这一轻量级机制实现实体间的关联，且支持跨维度、跨世界的实体查找。

## 注意事项

- 假玩家名称前加 `#` 可以使其在计分板列表中隐藏（仅Java版）
- 数据包版使用 `tick` 触发进度可能会在每次tick都执行，建议使用 `minecraft:impossible` 触发或添加 `once` 条件避免重复执行（原文表述需核实）
- 基岩版和Java版的命令语法有差异，跨版本使用时需注意
- 命令方块版的方法在处理大量玩家时会有延迟（每tick处理一个玩家）
