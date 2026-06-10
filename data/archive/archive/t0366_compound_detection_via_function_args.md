---
id: t0366
title: "函数参数判复合"
title_en: "compound_detection_via_function_args"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202601/e/content"
source_type: "feature_article"
source_issue: "202601"
version_min: "1.20.2"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["nbt", "type_detection", "function", "compound", "data_command"]
verified_in_game: false
---

## 核心洞见

只有复合标签可以作为参数传递给function命令，利用这一特性可以无歧义地判断一个NBT值是否为复合标签类型。

## 代码示例

```mcfunction
execute store success storage typeof:test.success byte 1 run function some_function with storage typeof:test
execute if data storage typeof:test {success:1b} run return run tellraw @s "Compound"
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Minecraft的function命令支持with参数，可以将一个NBT值作为参数传递给被调用的函数。但该参数必须是复合标签类型，否则命令会执行失败。这一限制提供了一个完美的复合标签检测方法：创建一个辅助函数，其内部只包含一条始终成功的命令（如return 1），然后使用execute store success捕获function命令的执行状态。如果目标NBT值是复合标签，函数调用成功，success被设为1；否则函数调用失败，success保持为0。相比其他方法（如data modify merge可能因源和目标相同而失败，或data modify set value可能因路径已存在而失败），这种方法没有边界情况，是判断复合标签最可靠的方式。

## 注意事项

- 需要额外创建一个辅助函数文件
- 函数参数必须是复合标签，不能是其他类型
- 辅助函数内不能有复杂的逻辑，只需保证执行成功即可
- 常见误解：开发者可能认为判断复合标签需要使用data modify merge命令，但该方法存在源和目标相同时无法判断的边界情况。
