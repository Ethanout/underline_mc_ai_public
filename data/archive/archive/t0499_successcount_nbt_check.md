---
id: t0499
title: "SuccessCount检测"
title_en: "successcount_nbt_check"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/numplayers"
source_type: "mcc_wiki"
source_issue: "questions/numplayers"
version_min: "1.0"
version_max: "1.12"
wiki_covers_this: false
confidence: medium
tags: ["entity counting", "command block", "successcount", "legacy"]
verified_in_game: false
---

## 核心洞见

命令方块的 SuccessCount NBT 会记录匹配实体数量，可通过 testforblock 读取

## 代码示例

```mcfunction
testfor @a[team=red]
testforblock <x> <y> <z> command_block -1 {SuccessCount:2}
```

## 文件结构

- （命令方块方案，无需数据包文件）

## 用法

放置两个命令方块：第一个执行 testfor，第二个（条件连锁或普通）执行 testforblock 检测第一个命令方块的 SuccessCount。将 <x> <y> <z> 替换为第一个命令方块的坐标。第二个命令方块成功时即表示匹配到恰好2个实体。

## 使用场景

['1.12 及以下旧版本需要检测精确实体数量', '简单的红石电路触发场景', '不需要复杂逻辑的快速检测']

## 机制原理

当 testfor 命令执行时，命令方块的 SuccessCount NBT 标签会被设置为匹配的实体数量。testforblock 命令可以检测指定位置的方块 NBT 数据，通过检查 SuccessCount 是否等于特定值来实现精确计数。这种方法利用了命令方块内部状态存储机制，但只能检测精确值，不支持范围检测。与 execute store 方法相比，它受限于命令方块环境，无法在函数中使用。

## 注意事项

- 仅适用于 1.12 及以下版本，1.13 后 testfor 被移除
- 只能检测精确值，不支持范围检测
- 需要根据命令方块类型调整方块名称（command_block/chain_command_block/repeating_command_block）
- 命令方块坐标需要手动填写
