---
id: t0468
title: "假玩家分数比较"
title_en: "score_comparison_via_fake_player"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/findsamescoreentity"
source_type: "mcc_wiki"
source_issue: "questions/findsamescoreentity"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["scoreboard", "predicate", "fake_player", "entity_comparison", "performance"]
verified_in_game: false
---

## 核心洞见

通过将实体分数存入假玩家，可以避免重复计算目标选择器，并配合谓词实现高性能的分数匹配查找。

## 代码示例

```mcfunction
# function example:some_function (run as player)
scoreboard players operation #this ID = @s ID
tag @s add this
execute as @e[predicate=example:this_id,tag=!this] run say Some ID!
tellraw @s ["ID ",{"selector":"@s"}," = ",{"selector":"@e[predicate=example:this_id,tag=!this]"}]
tag @s remove this

# predicate example:this_id
{
    "condition": "minecraft:entity_scores",
    "entity": "this",
    "scores": {
        "ID": {
            "min": {
                "type": "minecraft:score",
                "target": {
                    "type": "minecraft:fixed",
                    "name": "#this"
                },
                "score": "ID"
            },
            "max": {
                "type": "minecraft:score",
                "target": {
                    "type": "minecraft:fixed",
                    "name": "#this"
                },
                "score": "ID"
            }
        }
    }
}
```

## 文件结构

- data/example/functions/some_function.mcfunction
- data/example/predicates/this_id.json

## 用法

以玩家身份运行 `function example:some_function`，该函数会查找所有与当前玩家 ID 分数相同的实体（排除自身），并输出相关信息。

## 使用场景

['在计分板 ID 系统中，快速查找与指定实体具有相同 ID 的其他实体', '需要高效比较多个实体分数且避免重复计算目标选择器的场景', '配合谓词在目标选择器中直接使用分数比较，提升性能']

## 机制原理

该技术的核心在于利用假玩家（以 `#` 开头的名称）作为分数存储的中间变量。首先通过 `scoreboard players operation` 将目标实体的分数复制到假玩家 `#this` 中，这样后续命令只需引用假玩家即可，无需重复执行目标选择器。然后通过标签 `this` 标记当前实体，以便在后续命令中排除自身。关键在于谓词 `this_id` 的使用：它通过 `entity_scores` 条件检查目标实体的 `ID` 分数是否等于假玩家 `#this` 的 `ID` 分数（使用 `min` 和 `max` 限定为精确值）。这样，`@e[predicate=example:this_id,tag=!this]` 就能选出所有与当前玩家 ID 相同且不是自身的实体。相比直接使用 `execute if score` 逐实体比较，这种方法将分数比较逻辑封装在谓词中，可以在目标选择器层面直接过滤，性能更优。

## 注意事项

- 假玩家名称必须以 `#` 开头，且不会在计分板列表中显示
- 使用谓词进行分数比较在性能上优于 `execute if score` 命令（原文引用了 Reddit 性能对比）
- 该方法需要 1.13+ 版本，谓词功能在 Bedrock 版中不可用
- 函数末尾必须移除 `this` 标签，否则会影响后续操作
