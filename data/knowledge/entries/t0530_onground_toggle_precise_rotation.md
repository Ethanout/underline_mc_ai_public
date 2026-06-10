---
id: t0530
title: "切换 OnGround 提高旋转同步精度"
title_en: "onground_toggle_precise_rotation"
layer: technique
source_url: "https://mojira.dev/MC-278440"
source_type: manual
version_min: "1.21"
version_max: ""
wiki_covers_this: false
confidence: high
tags: ["rotation", "OnGround", "display_entity", "packet", "bug_workaround"]
verified_in_game: false
---

## 核心洞见

实体旋转通常以 `360/256 = 1.40625` 度步长同步给客户端。每 tick 把实体的 `OnGround` 切换为与上一刻相反的状态，会触发包含完整旋转精度的同步包，可改善展示实体和旁观镜头的视觉旋转精度。

## 代码示例

```mcfunction
execute as @n[type=item_display,limit=2] at @s run rotate @s ~0.1 ~
execute as @n[type=item_display] store success entity @s OnGround byte 1 store success score @s onground unless score @s onground matches 1
```

## 机制原理

第二条命令通过嵌套 `store success` 与上一次记录的分数交替写入 `OnGround`。状态变化迫使服务端发送实体数据更新，绕过普通旋转同步的量化精度限制。

## 使用场景

- 长模型 `item_display` 的精细旋转
- 基于 `/spectate` 的非生物实体镜头
- 部分实体视觉旋转不同步问题的规避

## 注意事项

- 该方法主动利用 MC-278440，漏洞修复后可能失效。
- 来源指出它不同于 Air toggling。
- 对生物实体、碰撞和身体旋转插值可能有副作用。

