---
id: t0453
title: "宏变量与缓存机制"
title_en: "macro_variable_and_cache_mechanism"
layer: technique
source_url: "data/archive/inbox/20260606_140955.md"
source_type: "manual"
source_issue: ""
version_min: "1.20.2"
version_max: ""
wiki_covers_this: false
confidence: high
tags: ["macro", "宏", "缓存", "性能", "局部变量", "function"]
verified_in_game: false
---

## 核心洞见

宏变量有 8 个全局缓存槽，缓存命中时性能极佳（~1~3），但传入动态变化的值（如随机坐标）会持续挤占缓存导致完全退化（~200），性能差距高达 100 倍。

## 代码示例

```mcfunction
# 被调用方：用 $ 声明当前行启用宏解析
# data/<namespace>/functions/draw_particle.mcfunction
$particle flame $(x) $(y) $(z) 0 0 0 0 1

# 调用方：将 storage 数据作为局部变量压入函数上下文
data modify storage ns:macro pos set value {x: 10.0d, y: 64.0d, z: 20.5d}
function <namespace>:draw_particle with storage ns:macro pos
```

## 文件结构

- `data/<namespace>/functions/draw_particle.mcfunction` — 含宏语法（`$` 前缀行）的被调用函数
- `data/<namespace>/functions/main.mcfunction` — 调用方，负责准备 storage 数据并传参

## 用法

调用方将参数写入 storage，然后 `function <ns>:func with storage ns:macro key` 传入。被调用函数中凡是含 `$(var)` 的行必须以 `$` 开头声明启用宏解析。

## 使用场景

- 需要将动态值（坐标、ID、名称）注入命令字面量的场景
- 实现通用工具函数时需要传入参数（替代全局变量传参）
- 传入**固定或低变化**的参数集合时性能最优（充分利用缓存）

## 机制原理

宏变量自 1.20.2 引入，是 mcfunction 中唯一真正意义上的显式局部变量，生命周期严格跟随当前函数调用栈，与编程语言的局部参数行为一致。

**工作原理**：每次调用宏时，系统将 `$(var)` 替换为纯文本后重新进行语法解析，生成可执行命令。

**缓存机制（8个槽）**：游戏存在全局 8 个宏缓存位置。以 `函数名 + 输入变量转换出的文本` 计算 Hash 值：
- **缓存命中**：Hash 已在 8 个缓存槽内 → 跳过语法解析，直接执行，速度极快（~1~3 单位）
- **缓存未命中**：新 Hash 挤占最老的缓存槽，重新解析语法，消耗 ~5~200 单位

**缓存失效场景**：如果不断传入新的数值（如每 tick 变化的随机坐标），每次调用都会产生新 Hash，8 个缓存槽被快速轮换，缓存完全失效，退化为每次重新解析语法，性能不稳定且极高。

## 注意事项

- 只有带 `$` 前缀的行才会进行宏解析，其余行正常执行，不产生额外开销
- 传入高频变化的数值（随机数、实时坐标）会导致缓存失效，此时应考虑改用上下文变量或 storage 直接操作
- 宏变量不能在同一行内嵌套或做运算，只是文本替换，复杂逻辑仍需借助 scoreboard
- 版本要求：1.20.2+，低版本数据包需要版本兼容处理
