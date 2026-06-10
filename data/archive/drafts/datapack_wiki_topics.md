# Minecraft 数据包开发参考（源自 datapack.wiki）

> 注意：以下内容汇总自 datapack.wiki 及 Minecraft Wiki。标注的 MC 版本为已验证信息的版本。

---

## 1. 函数 (Functions) 和函数标签 (Function Tags) — ticks / loads

**版本**: 1.13+（函数）；1.13+（函数标签）

### 函数文件

- 文件后缀 `.mcfunction`，位于 `data/<namespace>/function/<name>.mcfunction`
- 每行一条命令，**不带**前导 `/`
- `#` 开头为注释
- `\` 行尾续行
- 可用 `/function <namespace>:<path>` 调用
- 子文件夹：`data/<namespace>/function/sub/foo.mcfunction` → `function <namespace>:sub/foo`

**示例** (`data/example/function/hi.mcfunction`):
```
# 这是注释
give @a minecraft:apple
say Enjoy the apple!
```

### 函数标签（ticks & loads）

函数标签是 JSON 文件，位于 `data/minecraft/tags/function/`（注意必须是 `minecraft` namespace）。

- **`load.json`** — 世界加载 / `/reload` 时运行（先于玩家加入）
- **`tick.json`** — 每游戏刻（每秒 20 次）运行

**`data/minecraft/tags/function/load.json`**:
```json
{
  "values": [
    "example:load"
  ]
}
```

**`data/minecraft/tags/function/tick.json`**:
```json
{
  "values": [
    "example:tick"
  ]
}
```

> 注意：`tick/load` 的执行上下文：执行者是游戏服务器（`@s` 无效），位置是世界出生点。

**版本变更**: 1.21 起，文件夹从 `functions` → `function`，`tags/functions` → `tags/function`。

---

## 2. 宏 (Macros) — 参数化函数 / `$(var)` 语法

**版本**: 1.20.2+（pack_format 18+）

### 语法

- 宏函数中，以 `$` 开头的行可以使用 `$(<argument>)` 占位符
- 调用时通过 `/function` 传入 NBT 参数

### 示例

**`data/example/function/macro.mcfunction`**:
```
$give @s diamond $(count)
```

**调用**:
```
# 直接传参
function example:macro {count: 7}

# 从 storage 传参
data modify storage example:storage count set value 12
function example:macro with storage example:storage
```

> 注意：宏参数以 SNBT 形式传入，可在命令中任意位置使用 `$(name)`。

---

## 3. 战利品表 (Loot Tables) 和谓词 (Predicates)

### 战利品表 (Loot Tables)

**版本**: 1.13+

- 位于 `data/<namespace>/loot_table/<name>.json`（1.21+ 文件夹名为 `loot_table`，旧版为 `loot_tables`）
- 控制方块破坏、实体死亡、箱子生成、钓鱼等的掉落

**基本结构**:
```json
{
  "type": "minecraft:chest",
  "pools": [
    {
      "rolls": 1,
      "entries": [
        {
          "type": "minecraft:item",
          "name": "minecraft:diamond"
        }
      ]
    }
  ]
}
```

### 谓词 (Predicates)

**版本**: 1.15+（pack_format 5+）

- 位于 `data/<namespace>/predicate/<name>.json`
- 用于检查条件（玩家位置、手持物品、天气、时间等）
- 可在选中器 `@a[predicate=namespace:pred_name]` 或 `/execute if predicate` 中使用

**示例 — 检测玩家在沙漠村庄手持牛肉**:
```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "location": {
      "structures": "minecraft:village_desert"
    },
    "equipment": {
      "mainhand": {
        "items": "minecraft:beef"
      }
    }
  }
}
```

**常用条件类型**:
| 条件 | 功能 |
|------|------|
| `entity_properties` | 检查实体属性 |
| `location_check` | 检查位置（生物群系、维度、方块、光照） |
| `weather_check` | 检查天气 |
| `time_check` | 检查游戏时间 |
| `random_chance` | 随机概率 |
| `damage_source_properties` | 检查伤害来源 |
| `entity_scores` | 检查记分板分数 |
| `match_tool` | 匹配使用的工具 |
| `all_of` / `any_of` | 逻辑组合 |
| `inverted` | 逻辑非 |
| `reference` | 引用其他谓词文件 |

---

## 4. 进度 (Advancements) 作为事件监听器

**版本**: 1.13+

- 位于 `data/<namespace>/advancement/<name>.json`
- 可用作"事件监听器"：隐藏进度（不设 `display`），触发时运行函数

### 示例 — 检测玩家与交互实体互动

**`data/example/advancement/interacted_with_interaction.json`**:
```json
{
  "criteria": {
    "requirement": {
      "trigger": "minecraft:player_interacted_with_entity",
      "conditions": {
        "entity": {
          "type": "minecraft:interaction",
          "nbt": "{Tags:[\"my_interaction\"]}"
        }
      }
    }
  },
  "rewards": {
    "function": "example:rightclick_run"
  }
}
```

**`data/example/function/rightclick_run.mcfunction`**:
```
advancement revoke @s only example:interacted_with_interaction
say 我点击了交互实体！
```

### 关键要点

- `rewards.function` 中的函数以玩家为执行者（`@s` = 玩家）运行
- 必须用 `advancement revoke @s only ...` 撤销进度，以便同一事件再次触发
- 没有 `display` 字段 = 隐藏进度（玩家不可见）
- `criteria` 支持多种 trigger，如同一个进度可以定义多个 criteria，通过 `requirements` 控制逻辑组合（AND/OR）

**常用 trigger 示例**:
- `minecraft:tick` — 每刻触发
- `minecraft:player_interacted_with_entity` — 与实体交互
- `minecraft:entity_hurt_player` — 实体伤害玩家
- `minecraft:player_killed_entity` — 玩家杀死实体
- `minecraft:inventory_changed` — 背包变化
- `minecraft:impossible` — 永不触发（用作根进度）

---

## 5. 计划刻 (Schedule) 命令

**版本**: 1.15+（原 `/schedule`），1.16+ 完善

### 语法

```
/schedule function <function> <time> [append|replace]
/schedule clear <function>
```

- `<time>` 支持 `t`（刻, 默认）、`s`（秒）、`d`（天）
  - 1 秒 = 20 刻，1 天 = 24000 刻
- `append`：追加调度（允许多个）
- `replace`：替换已有的调度（默认）

### 示例

```
# 5 秒后运行函数
/schedule function example:my_func 5s

# 100 刻后运行，追加
/schedule function example:another 100t append

# 1 游戏日后运行
/schedule function example:later 1d

# 清除调度
/schedule clear example:my_func
```

> 注意：调度执行时上下文继承自**服务器的执行环境**（`@s` 不指向任何实体，位置为世界出生点）。需要自行使用 `execute as` 等。

---

## 6. execute 命令的各种子命令

**版本**: 1.13+（原始语法），1.13+ 链式子命令，持续更新

**通用结构**: `/execute <子命令> ... <子命令> run <命令>`

### 上下文修改子命令

| 子命令 | 功能 | 示例 |
|--------|------|------|
| `as <entity>` | 更改执行者（`@s` 的目标） | `execute as @a run say hi` |
| `at <entity>` | 更改位置/旋转到实体位置 | `execute at @p run setblock ~ ~ ~ stone` |
| `positioned <pos>` | 更改位置（不改变旋转/维度） | `execute positioned 0 64 0 run ...` |
| `positioned as <entity>` | 更改位置到实体的位置 | `execute positioned as @s run ...` |
| `positioned over <heightmap>` | 将 y 设为高度图上方 | `execute positioned over world_surface run ...` |
| `align <axes>` | 对齐坐标（向下取整） | `execute align xyz run ...` |
| `anchored (eyes\|feet)` | 更改局部坐标锚点 | `execute anchored eyes run ...` |
| `facing <pos\|entity>` | 更改旋转朝向某位置 | `execute facing 0 0 0 run ...` |
| `rotated <rot\|as entity>` | 更改旋转 | `execute rotated ~10 0 run ...` |
| `in <dimension>` | 更改维度 | `execute in minecraft:the_nether run ...` |
| `on <relation>` | 根据关系更改执行者 | `execute on target run ...` |
| `summon <entity>` | 召唤实体并以它为执行者 | `execute summon marker run ...` |

**`on` 关系值**: `attacker`, `controller`, `leasher`, `origin`, `passengers`, `target`, `vehicle`

### 条件子命令

| 条件 | 功能 |
|------|------|
| `if block <pos> <block>` | 检查方块 |
| `if blocks <start> <end> <dest> (all\|masked)` | 比较两个区域 |
| `if data (block\|entity\|storage) <target> <path>` | 检查 NBT 数据 |
| `if dimension <dimension>` | 检查维度 |
| `if entity <target>` | 检查实体是否存在 |
| `if predicate <predicate>` | 检查谓词 |
| `if score <target> <obj> (matches <range>\|<op> <src> <srcObj>)` | 检查分数 |
| `if function <function>` | 运行函数并检查返回值 |
| `if biome <pos> <biome>` | 检查生物群系 |
| `if items (block\|entity) <target> <slot> <item>` | 检查物品 |
| `if loaded <pos>` | 检查区块是否加载 |
| `if stopwatch <id> <range>` | 检查计时器（1.21.11+） |

`unless` 为否定版。

### store 子命令

```
execute store (result|success) <target> ...
```

`target` 可以是：
- `block <pos> <path> <type> <scale>`
- `entity <target> <path> <type> <scale>`
- `storage <storage> <path> <type> <scale>`
- `score <target> <objective>`
- `bossbar <id> (value|max)`

**示例**:
```
execute store result entity @s Pos[1] double 1.5 run data get entity @s Pos[1]
execute store success score $foo obj run say hi
```

---

## 7. 记分板 (Scoreboard) 高级用法

**版本**: 1.13+

### 三种目标类型

#### 1. Dummy（虚拟目标）

只能通过命令修改：
```
scoreboard objectives add intelligence dummy
scoreboard players set @a intelligence 100
execute store result score Silabear intelligence run data get entity Silabear Health
```

可以用 **假玩家** 存储全局数值（用 `#`, `$`, `.` 等前缀）：
```
scoreboard players set #max intelligence 150
```

#### 2. Criteria 自动统计

自动基于玩家统计更新：
```
scoreboard objectives add sneaking_duration minecraft.custom:minecraft.sneak_time
```

常用 criteria 前缀：`minecraft.custom:`, `minecraft.killed:`, `minecraft.mined:`, `minecraft.crafted:`, `minecraft.used:`, `minecraft.broken:`, `minecraft.picked_up:`, `minecraft.dropped:`

#### 3. Trigger（触发式）

玩家可用 `/trigger` 自行修改，无需 op：
```
scoreboard objectives add option trigger
scoreboard players enable @a option
```

玩家执行：
```
/trigger option          → 分数设为 1
/trigger option set 5   → 分数设为 5
/trigger option add 3   → 分数加 3
```

重新启用 trigger：
```
scoreboard players enable @a option
```

> 常用于创建自定义 UI / "聊天命令"。

### 1.20.3+ 新增：显示名称和数字格式

```
scoreboard objectives add money dummy
scoreboard objectives modify money displayname {"text":"金币"}
scoreboard objectives modify money numberformat {"text":"$%s"}
```

---

## 8. NBT 路径 (NBT Path)

**版本**: 1.13+

NBT 路径用于在 `/data` 等命令中定位 NBT 树中的特定位置。

### 语法

- 点号 `.` 分隔键名：`root.version`
- 方括号 `[]` 访问数组：
  - 按索引：`root.people[0]`
  - 按值匹配：`root.people[{name:"Aandeel"}]`

### 示例

假设 NBT 结构：
```snbt
{
  root: {
    version: 1,
    title: "Targets",
    people: [
      {name: "Silabear", age: 102},
      {name: "Aandeel", age: 100}
    ]
  }
}
```

| 路径 | 结果 |
|------|------|
| `root.version` | `1` |
| `root.title` | `"Targets"` |
| `root.people[0]` | `{name: "Silabear", age: 102}` |
| `root.people[0].name` | `"Silabear"` |
| `root.people[{name:"Aandeel"}].age` | `100` |

### NBT 存储 (Storage)

- 独立于实体/方块的全局 NBT 存储
- 命名空间 ID 如 `example:main`
- 无需初始化，首次 `/data` 访问即创建

**示例**:
```
data merge storage example:main {number: 1, message: "Hello!"}
data modify storage example:main other_number set from storage example:main number
data modify storage example:main compound.array append value 42
```

---

## 9. 数据包格式版本 (Pack Format / Version)

**版本对应表**（数据包格式）：

| pack_format | MC 版本 | 主要变化 |
|-------------|---------|----------|
| 4 | 1.13 - 1.14.4 | 初始版本 |
| 5 | 1.15 - 1.16.1 | 添加谓词 (predicates) |
| 6 | 1.16.2 - 1.16.5 | 自定义世界生成 |
| 7 | 1.17 - 1.17.1 | replaceitem → item 命令 |
| 8 | 1.18 - 1.18.1 | loot table 需要 type 字段 |
| 9 | 1.18.2 | locate 变更 |
| 10 | 1.19 - 1.19.3 | pack.mcmeta 支持 filter 段 |
| 12 | 1.19.4 | 伤害类型，标签系统变更 |
| 15 | 1.20 - 1.20.1 | 告示牌 NBT 变更 |
| 18 | 1.20.2 | **函数宏 (macros)**, 效果改用命名空间 ID |
| 26 | 1.20.3 - 1.20.4 | grass → short_grass |
| 41 | 1.20.5 - 1.20.6 | **物品组件系统** (item components) |
| 48 | 1.21 - 1.21.1 | 数据驱动的附魔，文件夹名改为单数 (loot_table, function, tags/item) |
| 57 | 1.21.2 - 1.21.3 | 属性前缀移除 |
| 61 | 1.21.4 | TNT minecart NBT 变更 |
| 71 | 1.21.5 | 文本组件在 NBT 中改为对象，大量组件/NBT 变更 |
| 80 | 1.21.6 | 云层高度，/datapack create，/version |
| 81 | 1.21.7 - 1.21.8 | 新增音乐唱片 |
| 88.0 | 1.21.9 - 1.21.10 | **pack_format 引入次版本号**，使用 min_format / max_format |
| 101.1 | 26.1 - 26.1.2 | 最新 |

### pack.mcmeta 格式

**1.21.8 及之前**:
```json
{
  "pack": {
    "description": "示例数据包",
    "pack_format": 48
  }
}
```

**1.21.9+**（次版本号系统）:
```json
{
  "pack": {
    "description": "示例数据包",
    "min_format": 88,
    "max_format": 88
  }
}
```

---

## 10. 数据包目录结构

**版本**: 1.13+（1.21+ 文件夹名改为单数）

```
<数据包名称>/
├── pack.mcmeta              # 必需：元数据
├── pack.png                 # 可选：封面图标
└── data/
    └── <namespace>/
        ├── advancement/     # 进度 (1.21+)
        ├── function/       # 函数 .mcfunction
        ├── item_modifier/  # 物品修饰器
        ├── loot_table/     # 战利品表 (1.21+)
        ├── predicate/      # 谓词
        ├── recipe/         # 合成配方
        ├── structure/      # 结构模板 .nbt
        ├── tag/            # 标签
        │   ├── block/
        │   ├── entity_type/
        │   ├── fluid/
        │   ├── function/
        │   ├── item/
        │   └── ...
        ├── dimension/      # 自定义维度
        ├── dimension_type/ # 维度类型
        ├── enchantment/    # 数据驱动附魔 (1.21+)
        ├── damage_type/    # 伤害类型
        ├── worldgen/       # 世界生成
        │   ├── biome/
        │   ├── configured_feature/
        │   ├── placed_feature/
        │   ├── density_function/
        │   ├── noise/
        │   ├── noise_settings/
        │   ├── configured_carver/
        │   └── ...
        └── ...
```

> 注意：1.21+ 将 `loot_tables` → `loot_table`，`functions` → `function`，`tags/items` → `tags/item`，`advancements` → `advancement` 等。

---

## 11. 物品组件 (Item Components) — 1.20.5+

**版本**: 1.20.5+（pack_format 41+），取代了旧的 NBT 物品系统

### 概述

物品组件是附加在物品上的数据结构，用于控制物品的各种属性。**1.20.5+** 不再使用 `tag` 等旧 NBT 方式，全部改用组件系统。

### 命令中使用

```
/give @s minecraft:diamond[minecraft:item_name="\"超级钻石\""]
/give @s minecraft:iron_pickaxe[minecraft:tool={rules:[{blocks:"minecraft:stone",speed:8.0}],default_mining_speed:2.0,damage_per_block:1}]
```

### 常见组件

| 组件 ID | 功能 | 版本 |
|---------|------|------|
| `minecraft:item_name` | 自定义物品名称（文本组件） | 1.20.5+ |
| `minecraft:item_model` | 自定义物品模型 | 1.21.4+ |
| `minecraft:lore` | 物品 lore（文本组件列表） | 1.20.5+ |
| `minecraft:custom_data` | 自定义 NBT 数据 | 1.20.5+ |
| `minecraft:consumable` | 使物品可食用 | 1.20.5+ |
| `minecraft:food` | 食物属性 | 1.20.5+ |
| `minecraft:tool` | 挖掘工具属性 | 1.20.5+ |
| `minecraft:durability` | 耐久度 | 1.20.5+ |
| `minecraft:enchantments` | 附魔列表 | 1.20.5+ |
| `minecraft:attribute_modifiers` | 属性修饰器 | 1.20.5+ |
| `minecraft:equippable` | 可装备 | 1.21.2+ |
| `minecraft:weapon` | 武器属性 | 1.21.5+ |
| `minecraft:glider` | 滑翔翼（如鞘翅） | 1.21.2+ |
| `minecraft:blocks_attacks` | 格挡攻击 | 1.21.5+ |
| `minecraft:tooltip_display` | 控制提示显示 | 1.21.5+ |
| `minecraft:potion_contents` | 药水效果 | 1.20.5+ |
| `minecraft:written_book_content` | 成书内容 | 1.20.5+ |
| `minecraft:lock` | 容器锁（物品谓词） | 1.21.2+ |

### 在配方输出中使用（1.20.5+）:
```json
{
  "type": "minecraft:crafting_shaped",
  "pattern": ["ttt", " s ", " s "],
  "key": {
    "t": {"item": "minecraft:turtle_scute"},
    "s": {"item": "minecraft:stick"}
  },
  "result": {
    "id": "minecraft:iron_pickaxe",
    "count": 1,
    "components": {
      "minecraft:item_name": "{\"text\":\"海龟镐\"}",
      "minecraft:tool": {
        "rules": [{"blocks": "minecraft:turtle_egg", "speed": 6, "correct_for_drops": true}],
        "default_mining_speed": 3,
        "damage_per_block": 1
      }
    }
  }
}
```

> 完整组件列表见 [Minecraft Wiki Data component format](https://minecraft.wiki/w/Data_component_format#List_of_components)

---

## 12. 显示实体 (Display Entities) — 完整用法

**版本**: 1.19.4+（23w03a+）

### 三种类型

| 实体 | 功能 | 命令示例 |
|------|------|----------|
| `minecraft:item_display` | 显示物品 | `/summon item_display ~ ~ ~` |
| `minecraft:block_display` | 显示方块 | `/summon block_display ~ ~ ~` |
| `minecraft:text_display` | 显示文本 | `/summon text_display ~ ~ ~` |

### 通用 NBT 字段

```snbt
{
  billboard: "fixed",
  interpolation_duration: 0,
  start_interpolation: 0,
  transformation: {
    left_rotation: [0f, 0f, 0f, 1f],
    right_rotation: [0f, 0f, 0f, 1f],
    translation: [0.0f, 0.0f, 0.0f],
    scale: [1.0f, 1.0f, 1.0f]
  },
  shadow_radius: 0.0f,
  shadow_strength: 1.0f,
  glow_color_override: -1,
  view_range: 1.0f,
  teleport_duration: 0
}
```

**`billboard` 选项**:
| 值 | 行为 |
|----|------|
| `fixed` | 完全固定（不面向玩家） |
| `vertical` | 仅在垂直轴上旋转面对玩家 |
| `horizontal` | 仅在水平轴上旋转面对玩家 |
| `center` | 始终面向玩家（如传统告示牌） |

### item_display 特有

```snbt
{
  item: {id: "minecraft:diamond", count: 1},
  item_display: "ground"   // 渲染样式
}
```

**`item_display` 选项**: `none`, `thirdperson_lefthand`, `thirdperson_righthand`, `firstperson_lefthand`, `firstperson_righthand`, `head`, `gui`, `ground`, `fixed`

### block_display 特有

```snbt
{
  block_state: {Name: "minecraft:stone"}
}
```

### text_display 特有

```snbt
{
  text: '{"text":"你好世界"}',
  line_width: 200,
  text_opacity: -1,
  background_color: 1073741824,
  shadow: false,
  see_through: false,
  default_background: false,
  alignment: "center"
}
```

**`alignment` 选项**: `center`, `left`, `right`

### 使用示例

**显示钻石物品**:
```
/summon item_display ~ ~1 ~ {item:{id:"minecraft:diamond",count:1},billboard:"center",transformation:{scale:[2.0f,2.0f,2.0f]}}
```

**显示石头方块**:
```
/summon block_display ~ ~1 ~ {block_state:{Name:"minecraft:stone"},billboard:"fixed"}
```

**显示文本**:
```
/summon text_display ~ ~1 ~ {text:'{"text":"Hello!","color":"gold","bold":true}',billboard:"center",alignment:"center",line_width:400,shadow:true}
```

### 更改显示实体的物品/方块

```
/item replace entity @e[type=item_display,limit=1] weapon.mainhand with minecraft:emerald
/data modify entity @e[type=block_display,limit=1] block_state set value {Name:"minecraft:gold_block"}
```

### 关键版本细节

- 1.19.4 (23w03a) — 首次引入
- 1.20 (23w18a) — `item_display` 物品绕 Y 轴旋转 180°（修正）
- 1.21.5 — NBT 格式变更（`transformation` 使用浮点数组）

> 显示实体是**实体**，会被 `/kill @e` 清除，可以用 `@e[type=item_display]` 等选择。

---

*以上内容综合自 [datapack.wiki](https://datapack.wiki) 及 [Minecraft Wiki](https://minecraft.wiki)。*
