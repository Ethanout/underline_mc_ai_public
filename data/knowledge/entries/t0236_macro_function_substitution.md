---
id: t0236
title: "宏函数替换"
title_en: "macro_function_substitution"
layer: technique
source_url: "https://datapack.wiki/wiki/files/functions"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.20.2"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["function", "macro", "dynamic-command", "parameter-substitution"]
verified_in_game: false
---

## 核心洞见

函数文件可以通过 `$` 前缀和 `$(argument)` 语法实现动态参数替换，类似函数调用传参。

## 代码示例

```mcfunction
```mcfunction:macro.mcfunction
# When called, $(count) will be replaced with some number, producing a valid command
$give @s diamond $(count)
```

```mcfunction:give.mcfunction
function example:macro {count: 7}

# This also works
data modify storage example:storage count set value 12
function example:macro with storage example:storage
```
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Minecraft 的宏函数机制允许在 `.mcfunction` 文件中使用 `$` 前缀定义宏行，其中 `$(argument)` 是占位符。当通过 `/function <function> {argument: value}` 或 `/function <function> with storage <storage>` 调用时，游戏会解析 NBT 参数，将占位符替换为实际值，然后执行替换后的命令。这类似于编程语言中的模板字符串或函数参数，避免了为每个参数值重复编写函数。关键点在于：宏替换发生在命令执行前，且只对 `$` 开头的行生效；非 `$` 行正常执行。与直觉不同，宏不是运行时变量，而是编译期文本替换，因此不能用于动态计算或条件分支。

## 注意事项

- 宏替换是纯文本替换，不会进行类型检查或语法验证，替换后可能产生无效命令
- `$(argument)` 中的参数名必须与调用时提供的 NBT 键完全匹配，否则替换失败
- 宏行必须以 `$` 开头，且 `$` 后不能有空格，否则不会被识别为宏
- 常见误解：开发者可能认为函数只能执行固定命令，无法动态改变命令内容，需要为每个参数值编写独立函数。
