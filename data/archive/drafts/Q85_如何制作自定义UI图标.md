---
id: q85-如何制作自定义UI图标
layer: pattern
version_min: "1.16"
confidence: medium
verified_in_game: false
source: llm_draft
tags: ["ui", "custom-ui", "item-frame", "bossbar", "title", "actionbar", "armor-stand", "map-art"]
generated_by: fill_empty_q.py
---

# 如何制作自定义UI图标

## 一、核心挑战

Minecraft 原版数据包无法直接渲染自定义纹理或模型到 HUD 上。所有 UI 图标必须通过**游戏内已有的渲染机制**间接实现。核心挑战在于：

1. **无原生 UI API**：没有 `draw_texture` 或 `render_image` 命令
2. **渲染层限制**：只能利用物品展示框、盔甲架、Bossbar、Title/Actionbar 等现有系统
3. **交互性差**：原版 UI 图标无法响应点击事件（除非使用物品展示框+玩家交互检测）

## 二、方案一：物品展示框 + 地图画（最灵活，支持交互）

### 原理

利用物品展示框（Item Frame）显示地图，地图上可以绘制任意像素图案。通过 `@e[type=minecraft:item_frame]` 选择器检测玩家与展示框的交互（右键/左键），模拟 UI 按钮点击。

**版本要求**：1.16+（物品展示框支持 `fixed` 标签防止旋转）

### 完整实现

#### 1. 创建地图画

使用外部工具（如 [MapPainter](https://mapPainter.rtfd.io/)）生成地图文件，或手动设置地图像素颜色。地图文件位于 `world/data/map_<id>.dat`。

#### 2. 放置展示框并加载地图

```mcfunction
# load.mcfunction - 在加载时放置展示框
summon minecraft:item_frame ~ ~ ~ {Facing:0b,Fixed:1b,Invulnerable:1b,Item:{id:"minecraft:filled_map",count:1,components:{"minecraft:map_id":1}}}
```

#### 3. 检测玩家交互（模拟点击）

```mcfunction
# tick.mcfunction - 每 tick 检测玩家与展示框的交互
execute as @a at @s if predicate <namespace>:looking_at_ui_button run function <namespace>:ui/button_click
```

`<namespace>/predicate/looking_at_ui_button.json`
```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "type_specific": {
      "type": "minecraft:player",
      "looking_at": {
        "type": "minecraft:item_frame",
        "nbt": "{Fixed:1b,Item:{id:\"minecraft:filled_map\"}}"
      }
    }
  }
}
```

**⚠️ 需验证**：`looking_at` 谓词在 1.20.5+ 中是否支持 `nbt` 字段。如果不行，需要改用 `@e[type=item_frame]` 射线检测。

#### 4. 处理点击事件

```mcfunction
# ui/button_click.mcfunction
# 假设展示框位置为 (x, y, z)
execute positioned <x> <y> <z> run function <namespace>:ui/button_handler
```

### 陷阱

- **地图 ID 冲突**：多个世界或数据包使用相同 map_id 会导致显示错乱。建议使用 `minecraft:map_id` 组件并确保 ID 唯一。
- **展示框碰撞箱**：展示框有碰撞箱，玩家可能被阻挡。可通过 `Marker:1b` 标签（1.17+）使其无碰撞箱，但此时 `looking_at` 谓词可能失效。
- **性能开销**：每 tick 对所有玩家执行 `looking_at` 谓词，开销中等。建议降低检测频率（如每 5 tick 一次）。
- **多玩家同步**：展示框是实体，所有玩家看到的是同一个。如果 UI 需要个性化，此方案不适用。

## 三、方案二：Bossbar + 颜色代码（简单，无交互）

### 原理

Bossbar 支持自定义名称（含颜色代码）和进度条。通过 `minecraft:bossbar` 命令创建多个 Bossbar，堆叠显示模拟 UI 图标。

**版本要求**：1.11+（Bossbar 命令引入）

### 完整实现

#### 1. 创建 Bossbar

```mcfunction
# load.mcfunction
bossbar add <namespace>:ui_icon_1 {"text":"⬛⬛⬛⬛⬛⬛⬛⬛","color":"gold","bold":true}
bossbar set <namespace>:ui_icon_1 max 100
bossbar set <namespace>:ui_icon_1 value 100
bossbar set <namespace>:ui_icon_1 visible true
bossbar set <namespace>:ui_icon_1 players @a
```

#### 2. 堆叠多个 Bossbar

由于 Bossbar 默认显示在屏幕中央上方，多个 Bossbar 会垂直堆叠。通过调整名称中的空格和颜色代码，可以模拟简单的图标（如进度条、状态指示器）。

```mcfunction
# 第二个 Bossbar，显示在下方
bossbar add <namespace>:ui_icon_2 {"text":"████████","color":"red"}
bossbar set <namespace>:ui_icon_2 max 100
bossbar set <namespace>:ui_icon_2 value 50
bossbar set <namespace>:ui_icon_2 visible true
bossbar set <namespace>:ui_icon_2 players @a
```

#### 3. 动态更新

```mcfunction
# tick.mcfunction
# 更新第二个 Bossbar 的值
execute store result bossbar <namespace>:ui_icon_2 value run scoreboard players get @p health
```

### 陷阱

- **最多显示 1 个 Bossbar**：原版限制每个玩家同时只能看到 1 个 Bossbar（1.16+ 改为最多 1 个）。**此方案实际上不可行**，因为多个 Bossbar 不会同时显示。
- **无法精确控制位置**：Bossbar 固定在屏幕中央上方，无法移动到角落或特定位置。
- **样式单一**：只能使用 Minecraft 聊天颜色代码，无法显示复杂图案。

## 四、方案三：Title/Actionbar + Unicode 字符（轻量，无交互）

### 原理

利用 Title 或 Actionbar 显示文本，使用 Unicode 字符（如方块字符 `█`、`▓`、`▒`、`░`）和颜色代码构建简单图标。

**版本要求**：1.11+（Title 命令），1.12+（Actionbar 命令）

### 完整实现

#### 1. 显示 Actionbar 图标

```mcfunction
# tick.mcfunction
title @s actionbar [{"text":"❤ ","color":"red"},{"text":"████████","color":"dark_red"},{"text":" ","color":"white"},{"text":"⚡ ","color":"yellow"},{"text":"████","color":"gold"}]
```

#### 2. 使用进度条模拟

```mcfunction
# 根据玩家血量动态生成进度条
# 假设血量百分比存储在 scoreboard health_pct 中
execute store result score #health_pct <namespace> run data get entity @s Health
scoreboard players operation #health_pct <namespace> *= 10
scoreboard players operation #health_pct <namespace> /= 20

# 生成进度条字符串（伪代码，实际需要函数递归或循环）
# 这里简化：直接使用固定字符串
title @s actionbar [{"text":"HP: ","color":"white"},{"text":"██████████","color":"green"}]
```

### 陷阱

- **字符宽度不一致**：不同字体、不同客户端下 Unicode 字符宽度可能不同，导致图标变形。
- **无法交互**：Title/Actionbar 文本不可点击，仅用于显示信息。
- **刷新频率**：Actionbar 每 tick 刷新可能导致闪烁，建议每 2-5 tick 更新一次。
- **长度限制**：Actionbar 最多显示约 40 个字符（取决于字体），复杂图标可能超出。

## 五、方案四：盔甲架 + 命名牌（3D UI，可交互）

### 原理

利用盔甲架（Armor Stand）显示自定义名称（通过命名牌），配合 `Marker` 标签使其无碰撞箱。盔甲架名称可以包含颜色代码和特殊字符，模拟 3D 空间中的 UI 标签。

**版本要求**：1.8+（盔甲架），1.13+（JSON 文本组件）

### 完整实现

#### 1. 生成盔甲架

```mcfunction
# load.mcfunction
summon minecraft:armor_stand ~ ~1 ~ {Marker:1b,Invisible:1b,Invulnerable:1b,NoGravity:1b,CustomNameVisible:1b,CustomName:'{"text":"[ 菜单 ]","color":"gold","bold":true}'}
```

#### 2. 检测玩家看向盔甲架

```mcfunction
# tick.mcfunction
execute as @a at @s if entity @s[distance=..5] facing entity <uuid> eyes run function <namespace>:ui/hover
```

**⚠️ 需验证**：`facing entity` 子命令在 1.13+ 中是否支持检测玩家视线方向。如果不行，需要使用射线检测（`raycast` 函数）。

#### 3. 交互检测

```mcfunction
# 使用 advancement 监听玩家与实体交互
# advancements/ui/interact.json
{
  "criteria": {
    "interact": {
      "trigger": "minecraft:player_interacted_with_entity",
      "conditions": {
        "entity": {
          "type": "minecraft:armor_stand",
          "nbt": "{CustomName:'{\"text\":\"[ 菜单 ]\"}'}"
        }
      }
    }
  },
  "rewards": {
    "function": "<namespace>:ui/interact_handler"
  }
}
```

### 陷阱

- **名称显示距离**：盔甲架名称默认在 64 格内可见，可通过 `Team` 选项调整。
- **多玩家同步**：每个玩家看到的盔甲架名称相同，无法个性化。
- **性能开销**：每 tick 检测所有玩家的视线方向，开销较高。建议降低频率或使用 `predicate` 优化。
- **交互触发**：`player_interacted_with_entity` 进度需要玩家右键实体，无法检测左键或悬停。

## 六、方案对比

| 方案 | 版本要求 | 交互性 | 个性化 | 性能开销 | 适用场景 |
|------|---------|--------|--------|---------|---------|
| 物品展示框+地图画 | 1.16+ | 高（可检测点击） | 低（全局共享） | 中 | 复杂 UI 面板、按钮菜单 |
| Bossbar | 1.11+ | 无 | 高（每个玩家独立） | 低 | **不可行**（仅显示 1 个） |
| Title/Actionbar | 1.11+ | 无 | 高 | 极低 | 状态指示器、简单进度条 |
| 盔甲架+命名牌 | 1.8+ | 中（可检测右键） | 低（全局共享） | 中高 | 3D 标签、悬浮提示 |

## 七、推荐方案

### 对于需要交互的复杂 UI

**首选：物品展示框 + 地图画**。虽然实现复杂，但支持点击检测，且地图画可以绘制任意图案。

### 对于仅显示信息的轻量 UI

**首选：Title/Actionbar + Unicode 字符**。实现简单，性能开销极低，适合显示血量、经验、状态等实时信息。

### 对于 3D 空间中的标签

**首选：盔甲架 + 命名牌**。适合在游戏世界中创建悬浮的 UI 元素（如 NPC 名称、地标标记）。

---
