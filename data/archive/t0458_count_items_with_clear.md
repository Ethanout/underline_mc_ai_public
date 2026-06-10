---
id: t0458
title: "clear计数法"
title_en: "count_items_with_clear"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/amountitems"
source_type: "mcc_wiki"
source_issue: "questions/amountitems"
version_min: "1.13"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["item-counting", "clear-command", "scoreboard", "execute-store"]
verified_in_game: false
---

## 核心洞见

将 clear 命令的 maxCount 设为 0 可以获取物品数量而不实际清除物品

## 代码示例

```mcfunction
# Setup
scoreboard objectives add diamonds dummy

# Commands
execute store result score @s diamonds run clear @s diamond 0
execute if score @s diamonds matches 5 run say I have exactly 5 diamonds in my inventory.
execute if score @s diamonds matches 1..4 run say I have somewhere between 1 and 4 diamonds in my inventory.
execute if score @s diamonds matches 10.. run say I have 10 or more diamonds in my inventory.
execute if score @s diamonds matches ..20 run say I have 20 or less diamonds in my inventory.
```

## 文件结构

- data/<namespace>/functions/check_diamonds.mcfunction

## 用法

将上述命令放入一个函数中，对目标玩家执行该函数即可。需要先创建 scoreboard 目标。

## 使用场景

['检测玩家背包中特定物品的精确数量', '根据物品数量范围触发不同行为（如奖励、限制）', '在旧版本（1.20.5 之前）中实现物品计数']

## 机制原理

clear 命令的 maxCount 参数设为 0 时，不会清除任何物品，但命令仍然会返回玩家拥有的该物品总数。通过 execute store result 可以将这个返回值存储到 scoreboard 中，然后使用 score 条件判断进行范围匹配。这个行为利用了 clear 命令的副作用——即使不执行清除操作，它也会计算并返回匹配物品的数量。

## 注意事项

- clear 命令只能用于玩家实体，不能用于容器方块或其他实体
- clear 命令只能按物品 ID 匹配，无法匹配物品组件（如 custom_data、item_name 等）
- 此方法在 1.20.5 之后仍然可用，但推荐使用 execute if items 以获得更强大的匹配能力
