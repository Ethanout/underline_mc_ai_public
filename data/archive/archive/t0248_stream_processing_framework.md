---
id: t0248
title: "流处理框架"
title_en: "stream_processing_framework"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202602/7/content"
source_type: "feature_article"
source_issue: "202602"
version_min: "1.20"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["stream", "functional", "macro", "storage", "batch"]
verified_in_game: false
---

## 核心洞见

在Minecraft数据包中，可以通过命令存储和宏函数模拟Java Stream API，实现数组的链式流处理。

## 代码示例

（原文无完整代码示例）

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用Minecraft的宏函数（function）和命令存储（storage）来模拟流处理。核心机制是：1) 将流（数组）存储在NBT路径中，通过address参数（如'storage foo:bar value'）动态指定来源；2) 使用patrickstool:stream/record作为统一的参数传递容器，宏函数通过$(value)、$(index)等变量接收元素；3) 通过循环遍历流中的每个元素，对每个元素调用用户指定的宏函数（如filter的条件函数、foreach的处理函数）；4) 比较器函数（用于max/min/sort）接受first和second参数，通过比较返回1/0来决定顺序。关键设计是：所有流处理函数都接受$(address)参数来定位流，用户自定义函数通过patrickstool:stream/record中的value、index、length等变量获取上下文，实现了类似Java Stream的链式调用。

## 注意事项

- 胡乱操作patrickstool:stream/record中的value、index、function、length、address、result、resultBatch、first、second、size等关键字会导致严重bug
- 输入的address必须指向一个有效的流（NBT数组），否则行为未定义
- distinct方法要求流中的元素必须是对象（NBT compound），不能是基本类型
- private方法不支持批处理，且不建议用户直接使用
- 常见误解：开发者通常认为数据包只能处理简单的NBT操作，无法实现高阶函数式的流处理（如filter、map、sort等），或者认为需要大量重复代码才能实现。
