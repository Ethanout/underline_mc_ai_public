---
id: t0449
title: "假玩家记分板惯例"
title_en: "fake_player_scoreboard_conventions"
layer: concept
source_url: "data/archive/inbox/20260606_140955.md"
source_type: "manual"
source_issue: ""
version_min: "1.14"
version_max: ""
wiki_covers_this: false
confidence: high
tags: ["scoreboard", "假玩家", "变量声明", "性能", "命名惯例"]
verified_in_game: false
---

## 核心洞见

假玩家记分板是性能最优的全局变量（消耗基准值 1），但必须在 load 中预声明，且命名惯例直接影响性能和可读性。假玩家名是任意字符串，不需要对应真实在线玩家，计分板系统直接通过字符串索引存取分数。

## 代码示例

```mcfunction
# load.mcfunction — 声明容器与常量
scoreboard objectives add <namespace> dummy

# 声明数字常量与配置
scoreboard players set 123 <namespace> 123
scoreboard players set #123 <namespace> 123
scoreboard players set config <namespace> 123
```

## 文件结构

- `data/<namespace>/functions/load.mcfunction` — 在数据包加载时声明所有记分板 objective 和常量

## 用法

在 `#minecraft:load` 函数标签对应的 load 函数中声明，数据包加载后全局可用。

## 使用场景

- 全局整数变量（计数器、状态标志、配置值）
- 跨函数传递整数运算结果
- 存储常量（如 `#100`、`#360` 等数学常数）

## 机制原理

计分板系统允许对任意字符串（玩家名）存储分数，不要求该字符串对应在线玩家。利用这一特性，可以用虚构名称作为变量容器，无需依赖真实实体或选择器。

**性能对比**：假玩家操作直接通过字符串索引，消耗基准值约为 1；`@e` 选择器需要遍历所有实体，开销显著高于假玩家。一个计分板 objective 可以存储近乎无限个假玩家分数，而每个真实实体每个 objective 只能存储一个分数。

**预声明要求**：类似静态语言，记分板 objective 在使用前必须在 load 中全局声明，否则运行时报错。

**命名惯例与前缀**：
- `#` 前缀（如 `#123`）：在侧边栏显示时隐藏，带来约 5% 的底层渲染/查找性能提升。推荐内部运算变量使用
- `$` 前缀：语义上表示"变量"，源自其他编程语言习惯，适合接口变量
- `.` 分隔符（如 `homes.x`）：模拟命名空间，提高可读性
- 不带特殊前缀：适合需要在侧边栏显示或跨 tick 存储的变量

**类型限制**：只能存储 32 位有符号整数（int），范围 `-2147483648` ~ `2147483647`。

## 注意事项

- objective 名称长度有限制，建议用命名空间缩写
- 常量建议在 load 中统一声明，不要在运行时动态创建
- 若假玩家名与真实在线玩家名相同（如 `Max`），计分板操作会同时影响该真实玩家，建议使用特殊字符前缀避免冲突
- `#` 前缀仅影响侧边栏显示和少量性能，不影响逻辑行为
- 假玩家仅适用于计分板操作，不能用于 `@e`、`@p` 等实体选择器
