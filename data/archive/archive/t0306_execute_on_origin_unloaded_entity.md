---
id: t0306
title: "on origin抓卸载实体"
title_en: "execute_on_origin_unloaded_entity"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202509/4/content"
source_type: "feature_article"
source_issue: "202509"
version_min: "1.20.2"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["entity", "unloaded_chunk", "execute_on_origin", "UUID", "retrieval"]
verified_in_game: false
---

## 核心洞见

execute on origin 可以定位到已卸载区块中的实体，即使该实体已离开世界五分钟以上。

## 代码示例

```mcfunction
function vdc:built_in/retriever/_monitor
# 该函数会为执行者创建随机 id，将其 UUID 数组转录为记分项，并维护一份数组UUID和十六进制字符串UUID的映射表。
# 映射表形如：
# storage vdc:sys retriever[{array:[I;0,0,0,1] ,str:"0-0-0-0-1"}]
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

在 Minecraft 中，实体被卸载（进入未加载区块）后，虽然不再参与游戏刻演算，但其数据仍保留在磁盘或内存中，UUID 和 NBT 数据并未立即清除。`execute on origin` 命令原本用于获取弹射物（如箭、末影珍珠）的发射者或投掷者，其底层机制是通过实体的 `Owner` 或 `Thrower` 标签存储的 UUID 来定位目标实体。关键发现是：即使目标实体所在的区块已卸载，只要该实体的 UUID 仍被另一个实体（如末影珍珠）的 `Owner` 或 `Thrower` 字段引用，`execute on origin` 就能通过这个 UUID 引用找到该实体，并允许执行后续命令（如 `tp`）。这与直觉相反——通常认为命令只能作用于已加载区块中的实体。但 `on origin` 的查找不依赖区块加载状态，而是直接通过 UUID 在实体数据表中检索，因此可以跨越区块卸载的限制。测试表明，即使经过五分钟，该机制仍然有效。但限制是：必须在实体被卸载前就设置好 `Owner` 或 `Thrower` 引用，卸载后无法再修改这些字段。重启服务器后，实体数据被清除，此方法失效。

## 注意事项

- 必须在实体被卸载前就设置好 Owner 或 Thrower 引用，卸载后无法再修改
- 大退（重启服务器）后此方法失效，因为实体数据被清除
- 需要额外实体（如末影珍珠）作为监视器，增加了性能负担
- 未测试维度安全问题，跨维度可能无效
- 常见误解：开发者通常认为实体一旦进入未加载区块就无法被任何命令选中或定位，只能通过大退重置UUID表来重新召唤。
