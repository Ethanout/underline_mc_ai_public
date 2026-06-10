---
id: t0517
title: "左键检测方法"
title_en: "left_click_detection_methods"
layer: technique
source_url: "data/archive/drafts/Q01_按键检测.md"
source_type: "manual"
source_issue: ""
version_min: "1.21.11"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["left_click", "attack", "piercing_weapon", "post_piercing_attack", "custom_enchantment"]
verified_in_game: false
---

## 核心洞见

数据包不能直接读取玩家是否按下了通用攻击键。1.21.11+ 推荐给主手物品添加 `piercing_weapon`，再用自定义魔咒的 `post_piercing_attack` 效果运行函数。该方案可以检测对空气的左键空挥，适合法杖和交互工具。

旧版本或不允许绑定专用物品时，可以使用独立的 `t0519_interaction_entity_click_detector` 跟随实体方案，但它需要持续维护实体且可能漏检。

## 方案选择

| 方案 | 版本 | 可检测空挥 | 手持物品依赖 | 主要代价 |
|---|---|---:|---:|---|
| `piercing_weapon` + `post_piercing_attack` | 1.21.11+ | 是 | 是，必须主手持有检测物品 | 检测物品无法正常破坏方块 |
| `interaction` 跟随实体 | 1.19.4+ | 仅当攻击命中实体 | 否 | 详见 `t0519_interaction_entity_click_detector` |

## 推荐方案：Piercing Weapon

### 机制原理

1. `piercing_weapon` 把主手物品的攻击转化为穿刺攻击，使对空气的左键空挥也成为可捕获事件。
2. 自定义魔咒的 `minecraft:post_piercing_attack` 效果在每次穿刺攻击后运行函数。
3. `minimum_attack_charge=0.0f` 解除攻击充能限制，允许快速连续点击。

### 自定义魔咒

`data/<namespace>/enchantment/left_click/using.json`：

```json
{
  "anvil_cost": 4,
  "description": {
    "translate": "enchantment.<namespace>.left_click_detect",
    "fallback": "左键检测"
  },
  "max_cost": {
    "base": 65,
    "per_level_above_first": 9
  },
  "max_level": 1,
  "min_cost": {
    "base": 15,
    "per_level_above_first": 9
  },
  "slots": ["mainhand"],
  "supported_items": "minecraft:recovery_compass",
  "weight": 2,
  "effects": {
    "minecraft:post_piercing_attack": [
      {
        "effect": {
          "type": "minecraft:run_function",
          "function": "<namespace>:left_click/using"
        }
      }
    ]
  }
}
```

`recovery_compass` 适合作为检测物品，因为它没有需要避让的基础交互行为。

### 给予检测物品

```mcfunction
give @s minecraft:recovery_compass[\
  minecraft:piercing_weapon={deals_knockback:false},\
  minecraft:minimum_attack_charge=0.0f,\
  minecraft:enchantments={"<namespace>:left_click/using":1},\
  minecraft:enchantment_glint_override=false,\
  minecraft:tooltip_display={hidden_components:["enchantments"]},\
  minecraft:rarity="common",\
  minecraft:item_model="stone",\
  minecraft:item_name={"translate":"item.<namespace>.detector","fallback":"左键检测器"}\
]
```

### 响应函数

`data/<namespace>/function/left_click/using.mcfunction`：

```mcfunction
# 每次左键点击时，以点击玩家为执行源运行
say 检测到左键点击！
playsound minecraft:entity.experience_orb.pickup player @s ~ ~ ~ 1 1.5
```

## 使用场景

- 需要检测空挥的法杖、武器或交互工具
- 左键施法、连点技能和自定义攻击逻辑

## 注意事项

- `piercing_weapon` 与 `post_piercing_attack` 要求 **1.21.11（25w41a）或更高版本**。
- 创建、修改或重写自定义附魔 JSON 后，必须**退出当前存档并重新进入**才能加载新定义；仅执行 `/reload` 不会可靠地刷新附魔注册内容。函数文件的普通修改仍可使用 `/reload` 测试。
- 自定义附魔属于实验性特性。进入使用该附魔的数据包存档时，游戏可能弹出实验性功能警告窗口；这是预期行为，测试时可以忽略并继续进入存档。
- 带 `piercing_weapon` 的物品在生存模式中无法正常破坏方块，因此只适合专用交互物品。
- `piercing_weapon` 检测物品必须位于主手，因为魔咒槽位配置为 `mainhand`。
- `deals_knockback:false` 可以避免检测物品产生不需要的击退。
- `minimum_attack_charge=0.0f` 允许快速连点；若需要攻击冷却，应删除或提高该值。
- 数据包无法检测未命中实体、且未使用 `piercing_weapon` 检测物品的任意空手左键。

## 相关条目

- `t0519_interaction_entity_click_detector`：不依赖专用手持物品的左右键跟随实体检测系统
