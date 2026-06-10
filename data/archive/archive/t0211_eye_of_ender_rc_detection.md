---
id: t0211
title: "末影之眼右键检测"
title_en: "eye_of_ender_rc_detection"
layer: technique
source_url: "https://datapack.wiki/guide/right-click/eoe"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.20.5"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["right_click_detection", "advancement", "item_use", "tick_based"]
verified_in_game: false
---

## 核心洞见

末影之眼物品的using_item触发器可以每tick持续检测右键按住状态，而非仅单次触发。

## 代码示例

```mcfunction
{
  "criteria": {
    "requirement": {
      "trigger": "minecraft:using_item",
      "conditions": {
        "item": {
          "items": [
            "minecraft:ender_eye"
          ],
          "predicates": {
            "minecraft:custom_data": {"custom_id": "your_custom_item_id"}
          }
        }
      }
    }
  },
  "rewards": {
    "function": "<namespace>:rightclick_run"
  }
}

# Revoke the advancement from the player so it can be used again
advancement revoke @s only <namespace>:used_eye_of_ender

# Custom logic
say I successfully used EoE detection!
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

末影之眼物品在游戏中具有'使用'行为（类似食物或工具），当玩家右键持有时会触发using_item进度触发器。与胡萝卜钓竿方法不同，胡萝卜钓竿的using_item仅在右键按下瞬间触发一次，而末影之眼由于物品本身的使用动画持续进行，触发器会在每个游戏刻（tick）持续触发，只要右键保持按住。该机制依赖于物品的useDuration属性（末影之眼默认32刻），使得进度条件在每个刻都被重新评估。通过自定义数据标签（custom_data）区分特定物品，可以精确控制触发目标。关键限制是末影之眼在存在要塞的世界中会生成实体并飞向要塞，因此该方法仅适用于无要塞世界或需要额外处理（如阻止实体生成）。

## 注意事项

- 在有要塞的世界中，末影之眼会生成实体并飞向要塞，破坏检测逻辑
- 需要每tick撤销进度，否则触发器不会重复触发
- 自定义数据标签必须与物品完全匹配，否则检测失败
- 常见误解：开发者通常认为只有胡萝卜钓竿或弓等可交互物品才能检测右键，且默认右键检测只能触发一次。
