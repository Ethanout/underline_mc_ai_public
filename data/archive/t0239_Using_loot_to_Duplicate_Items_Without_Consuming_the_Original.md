---
id: t0239
title: 使用/loot命令复制物品而不消耗原方块
title_en: Using /loot to Duplicate Items Without Consuming the Original Block
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["loot", "duplication", "block manipulation", "resource generation"]
verified_in_game: false
---

## 核心洞见

通过/loot mine命令可以复制方块战利品，而原方块不会被破坏，这不同于/setblock或/fill的破坏行为。

## 代码示例

```mcfunction
# 复制钻石矿石的掉落物（如钻石）而不破坏矿石
loot give @p mine block ~ ~ ~ diamond_ore
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

/loot mine <pos> 会模拟挖掘指定位置的方块，生成其战利品表掉落物，但方块本身不会被移除或改变。这允许在不破坏方块的情况下获取其掉落物，例如用于复制资源或创建自定义掉落机制。

## 注意事项

- 常见误解：开发者可能认为只有通过破坏方块才能获得其战利品，或者认为/loot mine会像玩家挖掘一样消耗方块。
