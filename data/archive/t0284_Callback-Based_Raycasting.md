---
id: t0284
title: 基于回调的射线投射
title_en: Callback-Based Raycasting
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-datapack/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["raycast", "callback", "collision-detection", "mcbookshelf"]
verified_in_game: false
---

## 核心洞见

MCBookshelf 的射线投射模块支持在命中方块或实体时触发回调函数，实现非阻塞的碰撞检测和事件驱动逻辑，而无需手动循环或递归。

## 代码示例

```mcfunction
execute anchored eyes positioned ^ ^ ^ run function #bs.raycast:run {with:{
  max_distance:10,
  entities:true,
  on_targeted_block:"setblock ~ ~ ~ minecraft:redstone_block"
}}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

通过 execute anchored eyes positioned ^ ^ ^ 设置射线起点和方向，调用 #bs.raycast:run 并传入 with 参数，其中可指定 on_targeted_block 和 on_targeted_entity 回调函数。当射线命中时，自动执行回调，并传递命中位置、方块状态或实体信息。

## 注意事项

- 常见误解：开发者通常认为射线投射只能通过递归函数或循环逐步移动位置来实现，且难以处理碰撞后的复杂逻辑。
