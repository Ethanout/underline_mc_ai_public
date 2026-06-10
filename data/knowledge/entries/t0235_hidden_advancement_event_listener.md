---
id: t0235
title: "隐藏进度事件监听"
title_en: "hidden_advancement_event_listener"
layer: technique
source_url: "https://datapack.wiki/wiki/files/advancements"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.20.5"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["advancement", "event_listener", "hidden_mechanic", "function"]
verified_in_game: false
---

## 核心洞见

通过隐藏进度（无 display）配合函数奖励和自撤销，可以将进度系统用作可重复触发的事件监听器

## 代码示例

```mcfunction
{
  "criteria": {
    "trigger_condition": {
      "trigger": "minecraft:player_killed_entity",
      "conditions": {}
    }
  },
  "rewards": {
    "function": "namespace:on_kill"
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

进度系统在 Minecraft 中内置了多种触发器（trigger），可以检测玩家行为（如攻击实体、进入维度等）。当进度达成时，rewards.function 会以玩家身份（as player）执行指定函数，但不会在玩家位置执行（at player）。通过不在 JSON 中设置 display 字段，进度对玩家完全隐藏，不会弹出提示。最关键的是，在奖励函数中调用 `advancement revoke @s only <advancement_id>` 撤销该进度，使得玩家可以再次触发条件并重新获得进度，从而实现可重复的事件监听。这种机制利用了进度系统的触发检测能力，将其转化为一个事件驱动的函数调用系统，而不需要玩家手动交互或看到任何 UI 元素。

## 注意事项

- 奖励函数以玩家身份执行而非在玩家位置执行，需要额外处理位置相关逻辑
- 必须手动撤销进度才能重复触发，否则只触发一次
- 撤销进度后需要等待玩家再次满足条件才能重新触发，存在短暂延迟
- 常见误解：开发者可能认为进度只能用于显示给玩家的成就系统，或者认为进度触发是一次性的，无法重复使用
