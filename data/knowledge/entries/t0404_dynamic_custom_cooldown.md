---
id: t0404
title: "动态物品冷却"
title_en: "dynamic_custom_cooldown"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202507/4/content"
source_type: "feature_article"
source_issue: "202507"
version_min: "1.21"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["cooldown", "consumable", "progress", "recipe_unlocked", "dynamic", "item_modify"]
verified_in_game: false
---

## 核心洞见

利用 consumable 组件触发 use_cooldown 组件，结合 using_item 进度和配方解锁进度，可以在物品消耗过程中动态修改冷却时间并实现物品的返还与替换。

## 代码示例

```mcfunction
// 进度1: using_item
{
  "criteria": {
    "test": {
      "trigger": "minecraft:using_item",
      "conditions": {
        "item": {
          "predicates": {
            "minecraft:custom_data": "{right_click_hand:\"main\"}"
          }
        }
      }
    }
  },
  "rewards": {
    "function": "yyt:system/right_click/mainhand/consumable/main"
  }
}

// 函数1: using_item 奖励函数
advancement revoke @s only yyt:system/click_check/consumable/right_click_mainhand
execute unless entity @s[tag=cooldown_set] run function yyt:system/right_click/mainhand/consumable/cd
data remove storage yyt:item modify
data modify storage yyt:item modify set from entity @s SelectedItem
function yyt:players/get/main
data modify storage yyt:player player.temp.item.modify set from storage yyt:item modify
function yyt:players/set/main
advancement revoke @s only yyt:system/click_check/consumable/mainhand_replace
item modify entity @s weapon.mainhand {function:"set_components", components:{"minecraft:use_cooldown":{seconds:0.5,"cooldown_group":"yyt:weapon/sword/1/1"}}}
tag @s add cooldown_set

// 进度2: consume_item
{
  "criteria": {
    "test": {
      "trigger": "minecraft:consume_item",
      "conditions": {
        "item": {
          "predicates": {
            "minecraft:custom_data": "{right_click_hand:\"main\"}"
          }
        }
      }
    }
  },
  "rewards": {
    "function": "yyt:system/right_click/mainhand/main"
  }
}

// 函数2: consume_item 奖励函数
advancement revoke @s only yyt:system/click_check/right_click_mainhand
tag @s remove cooldown_set
function yyt:system/right_click/function with entity @s SelectedItem.components.minecraft:custom_data
recipe take @s yyt:click_check/mainhand
recipe give @s yyt:click_check/mainhand

// 进度3: recipe_unlocked + consume_item
{
  "criteria": {
    "requirement": {
      "trigger": "minecraft:recipe_unlocked",
      "conditions": {
        "recipe": "yyt:click_check/mainhand"
      }
    },
    "test": {
      "trigger": "minecraft:consume_item",
      "conditions": {
        "item": {
          "predicates": {
            "minecraft:custom_data": "{right_click_hand:\"main\"}"
          }
        }
      }
    }
  },
  "rewards": {
    "function": "yyt:system/right_click/mainhand/consumable/replace_main"
  }
}

// 函数3: recipe_unlocked 奖励函数
function yyt:players/get/main
data modify storage yyt:item modify set from storage yyt:player player.temp.item.modify
# 写回原始cd（自由发挥）
item replace entity @s weapon.mainhand with stick
function yyt:system/item/components/mainhand with storage yyt:item modify
function yyt:system/item/count/mainhand
data remove storage yyt:player player.temp.item.modify
function yyt:players/set/main
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术基于 Minecraft 1.21+ 的组件系统与进度触发机制。核心原理：1) consumable 组件设置消耗时间（如 0.1s），使物品在右键后进入消耗过程，期间每 tick 触发 using_item 进度。2) 在 using_item 进度奖励函数中，通过 item modify 指令动态修改玩家主手物品的 use_cooldown 组件（包括 seconds 和 cooldown_group），实现冷却的动态设置。3) 消耗完成时触发 consume_item 进度，执行效果函数并给予玩家一个空配方。4) 配方解锁进度（recipe_unlocked）在玩家更新后触发，此时可以安全地使用之前存储的物品信息（如从 storage 中读取）来替换或返还物品，因为配方更新发生在玩家数据同步之后。关键点：using_item 进度在第 1 tick 触发，保存物品信息并设置冷却；consume_item 在第 2 tick 触发，执行效果并给予配方；recipe_unlocked 在玩家更新后触发，完成物品返还。这种时序保证了物品在消耗过程中可以被动态修改，且消耗后能无缝恢复。

## 注意事项

- using_item 进度每 tick 触发，需要 tag 或条件控制只执行一次冷却修改，否则会重复设置冷却
- 配方解锁进度在玩家更新后触发，必须确保 consume_item 进度中先给予配方，否则第三个进度不会触发
- 物品返还时需注意原始冷却组和冷却时长的保存与恢复，否则物品会丢失自定义冷却行为
- 常见误解：开发者通常认为 use_cooldown 只能通过 consumable 组件固定设置，无法在运行时根据物品状态动态调整冷却时长或冷却组。
