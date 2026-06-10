---
id: t0443
title: "递归替代循环"
title_en: "recursion_as_loop_in_mcfunction"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202511/1/content"
source_type: "feature_article"
source_issue: "202511"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["recursion", "loop", "function", "control-flow"]
verified_in_game: false
---

## 核心洞见

mcfunction没有原生循环，但函数递归可以替代循环，且无需局部变量，利用全局变量传递状态。

## 代码示例

```mcfunction
# 示例：递归遍历字符串（假设c-:code.0存储字符串）
# 函数c-:loop
# 检查字符串是否为空
execute unless data storage c-:code.0 run return 0
# 处理第一个字符（略）
# 递归调用自身
function c-:loop
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

mcfunction语言没有goto或循环语句，但函数可以递归调用自身。与高级语言不同，mcfunction的递归不传递局部变量（无局部变量），所有变量都是全局的（计分板或NBT）。因此，递归调用不会像传统递归那样消耗栈空间（除非使用宏函数生成新实例）。递归通过`/function`命令调用自身，并在每次调用中更新全局状态（如计分板计数器或NBT数据）。循环条件通过`/execute if ... run function`实现：如果条件满足，则继续递归；否则停止。例如，遍历字符串时，每次递归处理一个字符，直到字符串为空。这种递归本质上是一种尾递归，因为递归调用是函数的最后操作。与朴素实现（如使用重复命令块或外部循环）相比，递归更灵活，可以处理动态循环次数，且无需额外资源。

## 注意事项

- 递归深度受命令链长度限制（默认65536），但实际性能可能先达到瓶颈
- 使用宏函数时，每次递归会生成新函数实例，可能消耗大量存储空间
- 需要确保递归终止条件正确，否则可能导致无限递归
- 常见误解：开发者可能认为mcfunction无法实现循环，或者需要使用复杂的命令链或外部工具来模拟循环。
