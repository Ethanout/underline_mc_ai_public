---
id: t0451
title: "Storage 用法全览"
title_en: "storage_usage_overview"
layer: concept
source_url: "data/archive/inbox/20260606_140955.md"
source_type: "manual"
source_issue: ""
version_min: "1.15"
version_max: ""
wiki_covers_this: false
confidence: high
tags: ["storage", "nbt", "data", "变量", "全局"]
verified_in_game: false
---

## 核心洞见

Storage 是挂载在服务端的全局 NBT 复合容器，免声明、支持任意 NBT 类型、不依附实体/方块，是复杂数据结构的最佳全局存储。

## 代码示例

```mcfunction
# 1. 基础读写删
data modify storage ns:data var set value {a:1b, b:"hello", c:[1,2,3]}
execute store result score #val ns run data get storage ns:data var.a
data modify storage ns:io tmp set from storage ns:data var.b
data remove storage ns:data var

# 2. 支持的完整 NBT 类型
data modify storage ns:data x set value {
    byte: 1b, short: 1000s, int: 114514, long: 999999999999L,
    float: 3.14f, double: 2.718d, string: "hi",
    list: [1, "a", 3], compound: {nested: "v"},
    bool_true: true, byte_array: [B; 1b, 2b], int_array: [I; 1, 2]
}

# 3. 高级条件筛选（按 NBT 内容过滤列表元素）
data modify storage ns:io f1 set from storage ns:data players[{name:"Alice"}].score
data modify storage ns:io f2 set from storage ns:data items[{type:"sword",level:10..}]
data modify storage ns:io f3 set from storage ns:data item.tag."custom_tag_xxx"

# 4. 从实体/方块载入 Storage（一次性提取，避免反复读 NBT）
data modify storage ns:io player_pos set from entity @s Pos
data modify storage ns:io block_data set from block ~ ~-1 ~
```

## 文件结构

（Storage 是服务端全局容器，无需独立文件，在任何 mcfunction 中直接使用）

## 用法

构建完数据包即可在游戏内测试效果。Storage 数据在存档中持久化，重启服务器不会丢失。

## 使用场景

- 存储复杂数据结构（列表、复合标签、多类型混合）
- 作为函数调用的 IO 缓冲区（`ns:io` 命名惯例）
- 将实体/方块 NBT 一次性提取出来做复杂运算，避免反复读写高消耗的实体 NBT
- 跨 tick 持久化临时计算结果

## 机制原理

Storage 是一个挂载在服务端的全局 NBT 复合容器（Compound），通过命名空间 `ns:name` 寻址。

**免声明**：随用随创，完全不需要初始化，第一次 `data modify set` 即自动创建。

**支持任意 NBT 类型**：byte、short、int、long、float、double、string、list、compound、byte_array、int_array、long_array，远超记分板只能存 int 的限制。

**持久化**：Storage 数据存储在存档的 `data/` 目录中，服务器重启后不会丢失。

**性能**：读写消耗约 2~10 单位（以假玩家记分板为基准 1），远优于实体/方块 NBT（20~200 单位）。因此标准做法是"先批量读入 Storage，在 Storage 内运算，最后批量写回"。

**条件筛选**：`data modify ... set from storage ... list[{key:val}]` 支持按 NBT 内容过滤列表元素，相当于简单的 WHERE 查询。

## 注意事项

- `ns:io` 是惯用的临时 IO 缓冲区命名，`ns:data` 用于持久数据，保持一致有利于维护
- 使用 tag 做精确匹配时，建议对路径中的特殊键名加双引号（如 `"custom_tag_xxx"`），避免与 `item` 或 `tag` 本身发生解析冲突
- Storage 数据不会自动清理，长期运行的服务器需要注意手动 `data remove` 释放不再使用的数据
