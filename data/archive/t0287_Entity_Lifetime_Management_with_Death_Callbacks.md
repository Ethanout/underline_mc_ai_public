---
id: t0287
title: 实体生命周期管理与死亡回调
title_en: Entity Lifetime Management with Death Callbacks
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-datapack/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["health", "ttl", "death-callback", "entity-management", "mcbookshelf"]
verified_in_game: false
---

## 核心洞见

MCBookshelf 的健康模块提供了实体 TTL（生存时间）管理，并在实体死亡时自动触发回调函数，实现类似对象生命周期的模式。

## 代码示例

```mcfunction
# 为最近的实体设置100刻后自动死亡，并执行回调
function #bs.health:set_ttl {ttl:100,on_death:"say Entity expired!"}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

通过 #bs.health:set_ttl 函数为实体设置生存时间（以刻为单位），内部使用调度器在到期时执行 on_death 回调。同时支持 HP 管理，当 HP 归零时同样触发回调。

## 注意事项

- 常见误解：开发者通常认为实体死亡检测只能通过循环检查 Health 分数或使用 advancement 监听，无法设置自动过期和回调。
