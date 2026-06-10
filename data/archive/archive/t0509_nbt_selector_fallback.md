---
id: t0509
title: "NBT选择器回退"
title_en: "nbt_selector_fallback"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/tagentity"
source_type: "mcc_wiki"
source_issue: "questions/tagentity"
version_min: "1.8"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["selector", "nbt", "tag", "scoreboard", "entity"]
verified_in_game: false
---

## 核心洞见

当 execute if entity 依赖 NBT 时，无法直接复用选择器，需通过 tag 或 scoreboard 间接标记实体后再操作

## 代码示例

```mcfunction
# 1.12及以下版本：使用tag标记实体
scoreboard players tag @a add IsGrounded {OnGround:1b}
# 对标记后的实体执行操作
kill @a[tag=IsGrounded]
# 清理标记，避免永久生效
scoreboard players tag @a[tag=IsGrounded] remove IsGrounded

# 1.13及以上版本：直接在selector中使用nbt参数
kill @a[nbt={OnGround:1b}]
```

## 文件结构

（待补充）

## 用法

在命令方块或函数中直接执行上述命令序列。1.12及以下需先标记再操作最后清理；1.13及以上可直接在selector中指定nbt。

## 使用场景

['当需要根据实体的NBT数据（如是否在地面、手持物品等）执行kill、tp、effect等操作时', '在1.12及以下版本中，execute if entity无法直接配合其他命令使用NBT条件时', '任何需要将条件检测与动作执行分离的场景']

## 机制原理

在1.12及以下版本中，`execute if entity`（或`testfor`）只能检测实体是否存在，无法将检测结果直接传递给后续命令。因此需要两步走：先用`scoreboard players tag`（或`scoreboard players set`）给符合条件的实体打上标记，然后通过选择器参数`tag=...`选中这些标记实体执行操作。最后必须清理标记，否则标记会永久保留。1.13及以上版本引入了`nbt=`选择器参数，可以直接在selector中指定NBT条件，无需中间标记步骤。

## 注意事项

- 1.12及以下版本中，`testfor`命令已被移除，需使用`execute if entity`替代
- 标记后必须及时清理，否则实体会永久携带该标记，影响后续检测
- 1.13及以上版本中`nbt=`选择器参数性能可能不如tag方式，大量实体时建议仍用tag方案
- 此技术适用于所有需要根据NBT条件执行动作的场景，不仅限于kill
