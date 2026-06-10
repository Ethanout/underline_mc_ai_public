---
id: t0461
title: "投射物所有者伪造"
title_en: "projectile_owner_spoofing"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/angermob"
source_type: "mcc_wiki"
source_issue: "questions/angermob"
version_min: "1.13"
version_max: "1.19.4"
wiki_covers_this: false
confidence: medium
tags: ["projectile", "owner", "nbt", "mob", "anger", "targeting"]
verified_in_game: false
---

## 核心洞见

通过修改投射物的 Owner NBT 标签，可以伪造投射物的发射者，从而让被击中的生物攻击伪造的发射者

## 代码示例

```mcfunction
# summon the snowball
execute at @e[type=skeleton,tag=attacker] run summon minecraft:snowball ~ ~2.3 ~ {Tags:["atk_target"]}
# make the snowball owner the zombie
execute as @e[type=minecraft:snowball,tag=atk_target] run data modify entity @s Owner set from entity @e[type=zombie,limit=1,tag=target] UUID
```

## 文件结构

（待补充）

## 用法

在命令方块或函数中依次执行上述两条命令。第一条在攻击者（如骷髅）位置上方2.3格处生成雪球，第二条将雪球的 Owner 标签修改为目标实体（如僵尸）的 UUID。当雪球击中目标时，游戏会认为雪球是由目标实体发射的，从而触发仇恨。

## 使用场景

['在 Java 版 1.19.4 之前（/damage 命令未引入时），让生物攻击另一个特定实体', '需要更精细控制投射物行为（如雪球击中特定实体才触发仇恨）的场景', '作为 /damage 命令的替代方案，适用于不支持 /damage 的旧版本']

## 机制原理

Minecraft 中，投射物（如雪球、箭）的 Owner NBT 标签存储了发射者的 UUID。当投射物击中实体时，游戏会检查 Owner 标签，并将伤害来源归因于该 UUID 对应的实体。通过 /data modify 命令，可以手动将投射物的 Owner 标签设置为任意实体的 UUID，从而伪造发射者。当投射物击中目标时，目标会认为是被伪造的发射者攻击，从而产生仇恨。雪球被选为投射物是因为它不会对大多数生物造成伤害（仅对烈焰人有效），且生成后不会立即消失。生成位置在目标上方2.3格是为了避免投射物与目标碰撞箱重叠导致无法命中。

## 注意事项

- 如果目标玩家正在爬行或头顶有方块，雪球可能无法命中（原文表述需核实）
- 此方法仅适用于 Java 版，基岩版没有 Owner NBT 标签
- 雪球仅对烈焰人造成伤害，对其他实体仅产生击退效果，但仇恨机制仍会触发
- 需要确保投射物最终能击中目标实体，否则不会触发仇恨
