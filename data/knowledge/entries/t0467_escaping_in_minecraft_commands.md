---
id: t0467
title: "命令转义机制"
title_en: "escaping_in_minecraft_commands"
layer: concept
source_url: "https://minecraftcommands.github.io/wiki/questions/escaping"
source_type: "mcc_wiki"
source_issue: "questions/escaping"
version_min: "1.0"
version_max: ""
wiki_covers_this: true
confidence: low
tags: ["escaping", "string", "syntax", "json", "nbt"]
verified_in_game: false
---

## 核心洞见

mcfunction 的字符串转义规则和 Python 基本一致：反斜杠 `\` 作为转义符，`\"` 表示字面引号。最主要的 mcf 专有规则在于 **SNBT 格式**的字符串可以用单引号或双引号包裹，两者可以互相嵌套以避免转义。

## 代码示例

```mcfunction
# 标准转义：双引号字符串内用 \" 表示字面引号
tellraw @a {"text":"他说\"你好\""}

# SNBT 单双引号互用（mcf 专有，JSON 不支持）
# 双引号包裹时，内部单引号无需转义
data modify storage ns:io str set value "it's fine"

# 单引号包裹时，内部双引号无需转义
data modify storage ns:io str set value 'say "hello"'

# 嵌套时组合使用：外层单引号，内层双引号
summon armor_stand ~ ~ ~ {CustomName:'"Steve"'}
# 等价于：
summon armor_stand ~ ~ ~ {CustomName:"\"Steve\""}

# 多层嵌套（如命令方块 NBT 内含 tellraw）：
# 每多一层字符串边界，转义加一层
# 外层 SNBT 用单引号 -> 内层 tellraw 用双引号 -> 内部引号转义
data modify block ~ ~ ~ Command set value 'tellraw @a {"text":"hello \"world\""}'
```

## 文件结构

（无特定文件结构）

## 用法

理解性概念，无调用方式。编写涉及字符串嵌套的命令时，优先用单双引号组合来避免转义。

## 使用场景

- SNBT 字符串中包含特殊字符（引号、反斜杠）
- `tellraw` / `title` JSON 文本中含引号
- 命令方块 NBT 中嵌套包含命令的字符串

## 机制原理

转义规则与 Python 一致：`\` 是转义符，`\"` 表示字面双引号，`\\` 表示字面反斜杠，以此类推。

**mcf SNBT 的特殊之处**：SNBT 字符串可以用**单引号**或**双引号**包裹，两种引号可以互相嵌套而无需转义。这是 SNBT 格式独有的能力，JSON 只支持双引号，不能用单引号包裹字符串。

具体规则：
- `"outer"` — 双引号包裹，内部 `"` 需要转义为 `\"`，内部 `'` 无需转义
- `'outer'` — 单引号包裹，内部 `'` 需要转义为 `\'`，内部 `"` 无需转义

多层嵌套时，每越过一层字符串边界就需要额外一层转义，计算方式与 Python 字符串字面量完全相同。

## 注意事项

- 单双引号互用仅适用于 **SNBT 格式**（NBT 字符串），JSON 文件中只能用双引号
- 反斜杠本身必须转义为 `\\`，否则会转义后续字符导致意外行为
- 多层嵌套时，优先用单双引号组合拆开层级，减少手动计算转义层数
