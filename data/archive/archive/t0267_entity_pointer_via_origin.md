---
id: t0267
title: "实体指针与origin"
title_en: "entity_pointer_via_origin"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202604/3/content"
source_type: "feature_article"
source_issue: "202604"
version_min: "1.20"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["entity_pointer", "origin", "thrower", "execute_on", "uuid"]
verified_in_game: false
---

## 核心洞见

利用掉落物的 Thrower NBT 字段和 execute on origin 子命令，可以创建指向任意实体的指针，实现 O(1) 的跨实体访问。

## 代码示例

```mcfunction
mcfunction
# character:method/bind_player
# 绑定玩家，假设执行该方法的上下文坐标在玩家的位置，上下文执行者则是该对象的根实体
execute on passengers if entity @s[tag=CharacterController] run data modify entity @s Thrower set from entity @p UUID
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

掉落物（item）实体有一个 `Thrower` NBT 字段，原本用于记录投掷者的 UUID。通过 `data modify entity <item> Thrower set from entity <target> UUID` 可以将该字段设置为任意实体的 UUID。然后使用 `execute on origin` 子命令，执行者会切换到该 UUID 对应的实体。这个查找过程是直接通过 UUID 进行的，比任何选择器都快（O(1)）。这样，掉落物就成为了一个轻量级的实体指针，可以指向树上的其他实体或完全独立的实体，而不需要依赖骑乘关系。

## 注意事项

- 掉落物必须设置 PickupDelay 为 32767 和 Age 为 -32768 以防止被捡起和消失。
- 指针指向的实体被销毁后，指针会失效，需要重新绑定。
- 多个指针指向同一个实体时，需要管理好生命周期，避免悬挂指针。
- 常见误解：开发者通常认为实体间引用只能通过 NBT 存储 UUID 然后使用 @e 选择器查找，或者使用记分板标记，这些方法都需要遍历实体。
