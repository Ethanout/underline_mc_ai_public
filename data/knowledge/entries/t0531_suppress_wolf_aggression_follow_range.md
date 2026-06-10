---
id: t0531
title: "临时消除狼的攻击行为"
title_en: "suppress_wolf_aggression_with_follow_range"
layer: technique
source_url: "manual:pasted-text.txt"
source_type: manual
version_min: "1.21"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["wolf", "attribute", "follow_range", "ai", "anger"]
verified_in_game: false
---

## 核心洞见

狼出现 `AngryAt` 数据时，临时添加值为 `-1` 的 `add_multiplied_total` follow_range 修饰器，可把有效追踪范围压低，从而抑制其攻击行为；愤怒状态消失后再移除修饰器。

## 代码示例

```mcfunction
execute if data entity @s AngryAt run attribute @s follow_range modifier add anger -1 add_multiplied_total
execute unless data entity @s AngryAt run attribute @s follow_range modifier remove anger
```

## 机制原理

狼仍然保留愤怒目标，但 `follow_range` 总乘数减少 100%，使目标超出其有效追踪范围。该方法不删除 `AngryAt`，因此更像临时屏蔽攻击决策，而不是清除愤怒状态。

## 注意事项

- 需要以目标狼为执行者高频运行。
- `anger` 修饰器 ID 必须避免与其他系统冲突。
- 需验证 follow_range 被压到零或负值时在目标版本中的钳制行为。
- 可能影响狼的其他寻路和跟随逻辑。

