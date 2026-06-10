---
id: t0460
title: "伤害命令激怒生物"
title_en: "mob_attack_anger_via_damage"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/angermob"
source_type: "mcc_wiki"
source_issue: "questions/angermob"
version_min: "1.19.4"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["damage", "mob", "anger", "hate", "targeting"]
verified_in_game: false
---

## 核心洞见

利用 /damage 命令造成0点伤害，可以欺骗生物使其攻击指定的目标实体

## 代码示例

```mcfunction
# bedrock
/damage @e[type=wolf,c=1] 0 entity_attack entity @p
# java
/damage @e[type=wolf,limit=1,sort=nearest] 0 player_attack by @p

# bedrock
/damage @e[type=skeleton] 0 entity_attack entity @e[type=zombie]
# java
/execute as @e[type=skeleton] run damage @s 0 player_attack by @e[type=zombie,limit=1]
```

## 文件结构

（待补充）

## 用法

在命令方块或函数中直接运行对应版本的 /damage 命令即可。无需额外文件结构。

## 使用场景

['让任意可攻击生物（如狼、骷髅）攻击指定玩家或实体，用于陷阱、剧情事件或自定义战斗', '在不实际造成伤害的前提下触发生物的仇恨机制，用于测试或视觉效果']

## 机制原理

Minecraft 中，大多数可攻击生物会对攻击它们的实体产生仇恨并反击。/damage 命令可以指定伤害来源实体（source entity），即使伤害量为0，游戏仍会记录该伤害来源，触发目标生物的仇恨系统。因此，通过 /damage 命令让目标生物受到来自指定实体的0点伤害，即可欺骗目标生物，使其认为被该实体攻击，从而主动反击。此方法利用了游戏内置的仇恨机制，无需修改行为文件或生成投射物。

## 注意事项

- 在基岩版中，许多实体有严格的可攻击目标列表（由行为包定义），如果目标不在列表中，即使使用 /damage 也无法激怒该生物（原文表述需核实）
- 伤害量设为0不会实际减少生命值，但可能触发其他伤害相关效果（如击退、音效等），具体取决于伤害类型
- Java 版和基岩版的命令语法略有不同，需注意区分
