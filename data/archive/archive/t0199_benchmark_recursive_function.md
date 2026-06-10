---
id: t0199
title: "递归函数基准测试"
title_en: "benchmark_recursive_function"
layer: technique
source_url: "https://datapack.wiki/guide/performance/how-to-measure"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.21.8"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["performance", "benchmark", "recursive_function", "world_border"]
verified_in_game: false
---

## 核心洞见

通过递归执行函数并利用世界边界实时移动作为计时器，可以精确测量数据包中特定代码段的性能。

## 代码示例

```mcfunction
```mcfunction:test.mcfunction
execute as @e[type=armor_stand] if score @s test matches 1.. 
```
```mcfunction:test2.mcfunction
execute as @e[type=armor_stand] if data entity @s {ShowArms:false}
```
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用世界边界移动不依赖游戏刻、而是基于实时时间这一特性。具体实现：每刻开始时将世界边界在1秒内移动1000格，然后递归运行目标函数，直到边界移动了40格（即40毫秒已过去）。重复此过程100刻（5秒），记录每刻的迭代次数。平均迭代次数越高，函数性能越好。世界边界移动速度恒定且与TPS无关，因此可作为实时计时器，确保每次测试的时间窗口一致（40ms），从而公平比较不同实现的性能。

## 注意事项

- 基准测试结果在不同硬件上不一致，只能用于相对比较
- 需要确保测试环境（如实体数量）一致，否则结果不可比
- 世界边界移动可能受其他因素影响，需在空世界中进行测试
- 常见误解：开发者可能认为测量数据包性能只能依赖TPS图或外部工具，无法在游戏内对单个函数进行精确基准测试。
