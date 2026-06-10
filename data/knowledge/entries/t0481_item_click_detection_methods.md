---
id: t0481
title: "物品点击检测"
title_en: "item_click_detection_methods"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/itemclick"
source_type: "mcc_wiki"
source_issue: "questions/itemclick"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["click detection", "interaction entity", "carrot on a stick", "food component", "villager", "inventory click", "bundle"]
verified_in_game: false
---

## 核心洞见

通过交互实体、胡萝卜钓竿、食物组件、村民等多种方法，可以在不依赖资源包的情况下检测玩家对物品的左键/右键点击

## 代码示例

（原文无完整代码示例）

## 文件结构

（待补充）

## 用法

根据所选方法不同，构建数据包后即可在游戏内测试效果。交互实体法需召唤实体并运行命令；胡萝卜钓竿法需给玩家带有特定NBT的胡萝卜钓竿；食物组件法需给玩家带有food组件的物品；村民法需生成虚拟村民。

## 使用场景

['需要检测玩家对特定物品的右键点击以触发自定义功能（如使用道具、打开菜单）', '需要检测玩家对特定区域的左键/右键点击（如点击按钮、触发机关）', '需要检测玩家在物品栏中点击物品（1.20.5+）']

## 机制原理

本文介绍了多种物品点击检测方法，每种方法利用不同的游戏机制：

1. **交互实体法（1.19.4+）**：利用`interaction`实体检测左键（`attack`）和右键（`interact`）点击。通过`store success entity @s attack.player[] int 0 on attacker`和`store success entity @s interaction.player[] int 0 on target`命令捕获点击事件。配合`player_interacted_with_entity`和`entity_hurt_player`触发器实现高效检测。

2. **胡萝卜钓竿法**：利用MC-112991漏洞——使用胡萝卜钓竿（或诡异菌钓竿）时，`minecraft.used:minecraft.carrot_on_a_stick`分数会增加。通过检测分数变化和物品NBT（如`{shoot_fireball:1b}`）来判断右键点击。可通过资源包或1.21.2+的`item_model`组件改变外观。

3. **食物组件法（1.20.5+）**：给物品添加`minecraft:food`组件使其可食用。通过设置`eat_seconds`为极小值（命令方块法）或极大值（数据包法），配合`used:item`分数或`using_item`触发器检测右键点击。1.21.2+需同时使用`consumable`组件。

4. **村民法**：在玩家面前生成隐形、无AI的村民，检测`minecraft.custom:minecraft.talked_to_villager`分数变化来判断右键点击。

5. **物品栏点击法（1.20.5+）**：通过检查`player.cursor`槽位（`if items entity @s player.cursor`）检测玩家在物品栏中点击物品。

6. **束口袋法（Java和基岩版）**：右键束口袋会弹出第一个物品，通过检测掉落的物品实体来触发事件。

## 注意事项

- 交互实体法：不要创建过大的交互实体，否则点击检测会不一致
- 胡萝卜钓竿法：会吸引猪/炽足兽（使用诡异菌钓竿时）；在1.20.5前有不可移除的Damage NBT标签
- 食物组件法（命令方块版）：会有粒子效果、声音，且物品会被实际使用
- 食物组件法（数据包版）：设置`eat_seconds`为极大值可避免食用动画，但需注意延迟设置
- 村民法：会阻止玩家攻击实体、放置和破坏方块；僵尸会寻路到村民；多人模式下可能被滥用
- 物品栏点击法：不适用于创造模式玩家
- 束口袋法（Java版）：推荐使用其他方法替代

## 相关条目

- `t0204_right_click_detection_methods`：右键单击、按住与松开检测
- `t0517_left_click_detection_methods`：左键检测，以及 1.21.11+ 的 `piercing_weapon` 空挥检测
- `t0519_interaction_entity_click_detector`：使用跟随 `interaction` 实体同时检测左右键
