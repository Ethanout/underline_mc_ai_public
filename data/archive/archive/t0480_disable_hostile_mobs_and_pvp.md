---
id: t0480
title: "禁用敌对与PVP"
title_en: "disable_hostile_mobs_and_pvp"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/hostilefriendly"
source_type: "mcc_wiki"
source_issue: "questions/hostilefriendly"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["hostile mobs", "pvp", "teams", "effects", "interaction entity", "attribute", "game rule"]
verified_in_game: false
---

## 核心洞见

通过队伍、效果、属性或交互实体，可以分别或同时禁用敌对生物攻击和玩家间PVP，无需修改游戏规则。

## 代码示例

```mcfunction
# 方法1：队伍（Java版）
# 加载函数/聊天中执行
team add Friendly
team join @a friendly

# 刻函数/命令方块
team join @e[team=!friendly,type=zombie] friendly

# 方法2：虚弱+抗性（Java和基岩版）
# 使僵尸无法攻击玩家（持续60秒）
/effect give @e[type=zombie] weakness 60 127 true

# 使玩家无法攻击僵尸（持续60秒）
/effect give @a weakness 60 127

# 方法3：头盔（Java版）
# 持续替换骷髅头盔以干扰AI
/item replace entity @e[type=skeleton] armor.head with iron_helmet

# 方法4：交互实体（Java版）
# 创建一个交互实体骑乘目标生物，使玩家攻击交互实体而非生物
/summon minecraft:interaction ~ ~ ~

# 方法5：距离属性（Java版）
# 将玩家的实体交互范围设为0
/attribute <target> entity_interaction_range base set 0

# 方法6：游戏规则（基岩版）
/gamerule pvp false
```

## 文件结构

- data/<namespace>/functions/load.mcfunction
- data/<namespace>/functions/tick.mcfunction

## 用法

构建数据包后，在游戏中执行加载函数（如 /function <namespace>:load）初始化队伍，然后刻函数会自动将僵尸加入队伍。其他方法可直接在聊天或命令方块中执行对应命令。

## 使用场景

['在冒险地图或小游戏服务器中，需要让敌对生物（如僵尸、骷髅）对玩家友好，不主动攻击。', '在PVP地图或服务器中，需要禁用玩家之间的攻击，但保留生物攻击。', '在混合场景中，需要同时禁用敌对生物攻击和PVP，但不想修改全局游戏规则。']

## 机制原理

该文章提供了多种禁用敌对生物攻击和PVP的方法，每种方法基于不同的游戏机制：
1. **队伍（Teams）**：Java版中，队伍可以配置友好伤害（friendly fire）。将玩家和敌对生物加入同一队伍并禁用友好伤害后，生物不会攻击玩家，玩家也无法攻击同队生物。这是最直接的方法，但会占用队伍系统。
2. **虚弱+抗性（Weakness and Resistance）**：虚弱效果（等级127）会大幅降低生物的攻击力，使其无法造成伤害；抗性效果（等级5或更高）使实体免疫所有伤害（除/kill命令）。两者结合可完全禁用攻击和伤害。注意：锋利附魔可以绕过虚弱效果，因此需要抗性来防止伤害。
3. **头盔（Helmet）**：通过/item命令持续替换生物的头盔槽位，会干扰生物AI，使其无法攻击玩家。这被认为是一个bug，仅适用于Java版。
4. **交互实体（Interactions）**：创建一个交互实体（interaction entity）并使其骑乘目标生物。玩家攻击时，会优先攻击交互实体而非生物，从而保护生物。但该方法有局限性：玩家无法与生物交互（如交易），且投射物仍可攻击生物。
5. **距离属性（Distance Attribute）**：Java版中，`entity_interaction_range`属性控制玩家与实体交互的范围。将其设为0后，玩家无法攻击或右键交互任何实体（包括生物和村民）。
6. **游戏规则（Game Rule）**：基岩版中，`pvp`游戏规则可直接禁用玩家间攻击，但影响所有玩家。

## 注意事项

- 队伍方法仅适用于Java版，基岩版不支持/team命令。
- 虚弱+抗性方法中，抗性等级5或更高可使实体免疫所有伤害，包括摔落伤害和窒息伤害。
- 虚弱+抗性方法中，锋利附魔可以绕过虚弱效果，因此必须同时使用抗性。
- 头盔方法在基岩版中无效，且可能被视为bug，未来版本可能修复。
- 交互实体方法中，交互实体可能因生物快速移动（如下落）而滞后，导致保护失效。
- 交互实体方法中，黑客客户端（如killaura）可以直接攻击生物，绕过交互实体。
- 交互实体方法中，箭矢和其他投射物仍可攻击生物。
- 距离属性方法会影响所有交互，包括右键交易，因此玩家无法与村民交易。
- 基岩版的gamerule pvp会影响所有玩家，无法指定个别玩家。
