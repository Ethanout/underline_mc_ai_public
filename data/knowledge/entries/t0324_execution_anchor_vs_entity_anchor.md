---
id: t0324
title: "锚点分离机制"
title_en: "execution_anchor_vs_entity_anchor"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202509/6/content"
source_type: "feature_article"
source_issue: "202509"
version_min: "1.19"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["命令机制", "锚点", "朝向", "execute"]
verified_in_game: false
---

## 核心洞见

执行锚点与实体锚点是两个独立概念，修改执行锚点不影响执行位置，仅改变局部坐标原点和朝向起点。

## 代码示例

```mcfunction
execute anchored eyes run rotate @s facing entity @n[type=villager] eyes
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

在 Minecraft 命令系统中，存在两种独立的锚点：实体锚点（Entity Anchor）和执行锚点（Execution Anchor）。实体锚点是实体身上用于定位的点，有 feet（脚部，位于碰撞箱底部中心，即实体实际位置）和 eyes（眼部，位于眼睛高度处碰撞箱中心）两个值，水平位置相同仅 y 轴不同。不同实体的眼部高度不一致（玩家约1.62格，村民相同，末影人不同）。执行锚点是命令上下文参数的一部分，默认始终为脚部，修改执行锚点不会改变执行位置（始终在脚部），但会影响：局部坐标（^ ^ ^）的原点、实体朝向的起点、执行朝向的起点。当锚点为脚部时，相对坐标和局部坐标的原点、朝向起点都在执行位置（脚部）；当锚点为眼部时，相对坐标原点仍在脚部，但局部坐标原点和朝向起点在眼部。因此 rotate 命令中 facing entity 的 facingAnchor 参数指定的是目标实体的实体锚点（终点），而 anchored 子命令修改的是执行锚点（起点），两者独立。要使玩家准确朝向任意实体的眼睛，必须同时设置：执行锚点为 eyes（起点在玩家眼部），目标实体锚点为 eyes（终点在目标眼部）。

## 注意事项

- 误以为 anchored eyes 会将执行位置也移到眼部，导致 setblock ~ ~ ~ 放置位置与预期不符
- 忽略不同实体眼部高度不同，使用默认脚部锚点朝向村民时恰好因高度相同而看似正确，但对末影人等不适用
- 混淆 rotate 命令中 facingAnchor 参数（目标实体锚点）与 anchored 子命令（执行锚点）的作用
- 常见误解：开发者常误以为 anchored eyes 会将执行位置也移到眼部，或者认为朝向命令中的 facingAnchor 与执行锚点作用相同。
