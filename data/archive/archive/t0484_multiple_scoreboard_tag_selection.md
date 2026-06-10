---
id: t0484
title: "多标签实体选择"
title_en: "multiple_scoreboard_tag_selection"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/multipletags"
source_type: "mcc_wiki"
source_issue: "questions/multipletags"
version_min: "1.12"
version_max: "1.12.2"
wiki_covers_this: false
confidence: medium
tags: ["selector", "scoreboard", "tag", "nbt", "legacy"]
verified_in_game: false
---

## 核心洞见

在1.13之前，选择器无法直接指定多个相同类型的标签参数，但可以通过嵌套@s执行或NBT检测绕过限制

## 代码示例

```mcfunction
# Method 1: Nested @s execute (1.12 and above)
execute @a[tag=A] ~ ~ ~ execute @s[tag=B] ~ ~ ~ execute @s[tag=C] ~ ~ ~ execute @s[tag=D] ~ ~ ~ kill @s[tag=E]

# Method 2: NBT tag checking
scoreboard players tag @e add HasAllTags {Tags:["A","B","C"]}

# Optimized version with least common tag
scoreboard players tag @e[tag=A] add HasAllTags {Tags:["B","C"]}
```

## 文件结构

（待补充）

## 用法

方法1：直接作为命令执行，无需额外文件。方法2：在函数或命令方块中运行添加标签的命令，之后即可用@e[tag=HasAllTags]选择目标实体

## 使用场景

['在1.12及以下版本中需要选择同时拥有多个标签的实体', '需要精确控制实体选择条件，避免选择器限制', '优化性能时，先通过一个常见标签缩小候选范围，再检查NBT']

## 机制原理

在Minecraft 1.12及以下版本中，选择器参数不支持重复的键名，例如@e[tag=A,tag=B,tag=C]会忽略前两个tag参数，只保留最后一个tag=C的效果。方法1利用@s（自身）选择器和嵌套execute命令，每一层只检查一个标签，只有通过所有标签检查的实体才会执行最终命令。方法2利用NBT数据中存储的Tags列表，通过NBT匹配语法{Tags:["A","B","C"]}来检测实体是否同时拥有多个标签，然后添加一个临时标签用于后续选择。优化版本先通过一个最不常见的标签缩小候选实体范围，减少NBT检查的开销。

## 注意事项

- 此技术仅适用于1.12及以下版本，1.13及以上版本已原生支持选择器中的多个tag参数
- 方法1中嵌套层数过多可能导致命令过长，受限于命令长度限制
- 方法2的NBT匹配语法在1.12及以下版本中可用，但需要注意NBT格式的准确性
- 优化版本中指定的标签应选择最不常见的标签，以最大化性能提升
