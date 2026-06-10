---
id: q81-如何防止UI与原版冲突
layer: pattern
version_min: "1.13"
confidence: high
verified_in_game: false
source: llm_draft
tags: ["UI", "conflict", "bossbar", "title", "scoreboard", "tellraw", "priority", "coordination"]
generated_by: fill_empty_q.py
---

# 如何防止UI与原版冲突

## 问题背景

在 Minecraft 数据包开发中，"UI" 通常指通过 `tellraw`、`title`、`bossbar`、`scoreboard` 等机制向玩家展示的交互界面。当多个数据包或原版功能同时使用这些机制时，会产生冲突：
- 多个 `bossbar` 同时显示，遮挡屏幕
- 多个 `title` 叠加，文字混乱
- `scoreboard` 侧边栏被覆盖
- 聊天栏被多个数据包的 `tellraw` 刷屏

核心挑战：**Minecraft 没有原生的 UI 层叠/优先级系统**，所有 UI 元素都是全局的，数据包之间无法自动协调。

---

## 方案一：Bossbar 独占 + 优先级协商

### 原理

利用 `bossbar` 的 `visible` 属性和 `max` 值，为每个数据包分配一个唯一的 `bossbar id`，并通过一个全局的 `scoreboard` 记录当前活跃的 UI 层。数据包在显示 UI 前，先检查当前是否有更高优先级的 UI 正在显示，如果没有则显示自己的 UI，并标记为活跃。

### 完整实现

#### 1. 初始化 (Load)

```mcfunction
# load.mcfunction
# 创建全局 UI 优先级 scoreboard
scoreboard objectives add ui_priority dummy
# 创建全局 UI 活跃标记
scoreboard objectives add ui_active dummy

# 初始化 bossbar（每个数据包使用不同的颜色和 id）
bossbar add namespace:ui_bossbar {"text":"UI Title"}
bossbar set namespace:ui_bossbar color green
bossbar set namespace:ui_bossbar max 100
bossbar set namespace:ui_bossbar visible false
```

#### 2. 显示 UI 函数

```mcfunction
# function namespace:ui/show.mcfunction
# 参数：玩家 @s，优先级值（通过 scoreboard 传入）
# 假设优先级值存储在 scoreboard ui_priority 中

# 检查当前是否有更高优先级的 UI 活跃
execute if score @s ui_priority < @s ui_active run return fail

# 如果没有冲突，显示自己的 UI
bossbar set namespace:ui_bossbar players @s
bossbar set namespace:ui_bossbar visible true
bossbar set namespace:ui_bossbar value 50

# 标记当前 UI 为活跃
scoreboard players operation @s ui_active = @s ui_priority
```

#### 3. 隐藏 UI 函数

```mcfunction
# function namespace:ui/hide.mcfunction
bossbar set namespace:ui_bossbar visible false
bossbar set namespace:ui_bossbar remove @s

# 清除活跃标记
scoreboard players set @s ui_active 0
```

### 陷阱与注意事项

1. **Bossbar 数量限制**：Minecraft 最多支持 256 个 bossbar（`/bossbar list` 上限）。如果数据包数量多，需要合理分配。
2. **优先级协商需要全局约定**：所有数据包必须使用相同的 `scoreboard` 名称和优先级规则，否则无法协调。
3. **玩家断开重连后状态丢失**：`bossbar` 的 `players` 列表不会持久化，需要在玩家加入时重新设置。
4. **Bossbar 无法显示复杂 UI**：只能显示进度条和标题文本，不适合需要多行文本或交互的 UI。

---

## 方案二：Title 独占 + 时间窗口协商

### 原理

利用 `title` 的 `times` 参数（淡入、停留、淡出）和 `clear` 命令，通过一个全局的 `scoreboard` 记录当前 title 的显示状态。数据包在显示 title 前，先检查当前是否有其他 title 正在显示，如果有则等待或放弃。

### 完整实现

#### 1. 初始化 (Load)

```mcfunction
# load.mcfunction
scoreboard objectives add title_active dummy
scoreboard objectives add title_priority dummy
```

#### 2. 显示 Title 函数

```mcfunction
# function namespace:ui/show_title.mcfunction
# 参数：玩家 @s，优先级值（通过 scoreboard 传入）

# 检查当前是否有更高优先级的 title 活跃
execute if score @s title_priority < @s title_active run return fail

# 设置 title 显示参数
title @s times 10 60 10
title @s title {"text":"UI Title","color":"gold"}

# 标记当前 title 为活跃，并设置超时时间（ticks）
scoreboard players operation @s title_active = @s title_priority
schedule function namespace:ui/clear_title 80 replace
```

#### 3. 清除 Title 函数

```mcfunction
# function namespace:ui/clear_title.mcfunction
title @s clear
scoreboard players set @s title_active 0
```

### 陷阱与注意事项

1. **Title 无法持久显示**：Title 有固定的淡入/停留/淡出时间，无法像 bossbar 那样持续显示。
2. **多个 title 会叠加**：如果两个数据包同时发送 title，后发送的会覆盖前一个，但淡出效果可能重叠。
3. **时间窗口协商不精确**：如果两个数据包在同一个 tick 内发送 title，无法通过 scoreboard 检测到冲突。
4. **`schedule` 函数可能被覆盖**：如果多个数据包都使用 `schedule` 来清除 title，后调用的会覆盖前一个。

---

## 方案三：Scoreboard 侧边栏独占 + 动态切换

### 原理

利用 `scoreboard objectives setdisplay sidebar` 只能显示一个 objective 的特性，通过一个全局的 `scoreboard` 记录当前显示的 objective，数据包在切换侧边栏前，先检查当前是否有其他数据包的侧边栏正在显示。

### 完整实现

#### 1. 初始化 (Load)

```mcfunction
# load.mcfunction
scoreboard objectives add sidebar_owner dummy
scoreboard objectives add sidebar_priority dummy

# 创建自己的侧边栏 objective
scoreboard objectives add namespace:sidebar dummy {"text":"My Data Pack"}
```

#### 2. 显示侧边栏函数

```mcfunction
# function namespace:ui/show_sidebar.mcfunction
# 参数：玩家 @s，优先级值（通过 scoreboard 传入）

# 检查当前是否有更高优先级的侧边栏
execute if score @s sidebar_priority < @s sidebar_owner run return fail

# 设置侧边栏
scoreboard objectives setdisplay sidebar namespace:sidebar

# 标记当前侧边栏的拥有者
scoreboard players operation @s sidebar_owner = @s sidebar_priority
```

#### 3. 隐藏侧边栏函数

```mcfunction
# function namespace:ui/hide_sidebar.mcfunction
# 恢复默认侧边栏（通常是空的）
scoreboard objectives setdisplay sidebar

# 清除拥有者标记
scoreboard players set @s sidebar_owner 0
```

### 陷阱与注意事项

1. **侧边栏是全局的**：`setdisplay sidebar` 影响所有玩家，无法为单个玩家设置不同的侧边栏。
2. **Objective 数量限制**：Minecraft 最多支持 256 个 scoreboard objective。
3. **侧边栏内容更新**：需要定期更新侧边栏中的分数值，否则显示会过时。
4. **无法显示复杂 UI**：侧边栏只能显示文本和数字，不支持颜色、格式化等。

---

## 方案四：聊天栏独占 + 消息队列

### 原理

利用 `tellraw` 和 `team` 的 `collisionRule` 或 `seeFriendlyInvisibles` 等属性，通过一个全局的 `storage` 存储消息队列，数据包将消息写入队列，由统一的调度函数按顺序发送。

### 完整实现

#### 1. 初始化 (Load)

```mcfunction
# load.mcfunction
# 创建消息队列 storage
data merge storage namespace:ui {message_queue:[]}

# 创建调度函数
schedule function namespace:ui/process_queue 1t
```

#### 2. 添加消息到队列

```mcfunction
# function namespace:ui/add_message.mcfunction
# 参数：玩家 @s，消息 JSON（通过 storage 传入）
# 假设消息 JSON 存储在 storage namespace:ui temp_message

# 将消息添加到队列
data modify storage namespace:ui message_queue append from storage namespace:ui temp_message
```

#### 3. 处理队列

```mcfunction
# function namespace:ui/process_queue.mcfunction
# 检查队列是否为空
execute if data storage namespace:ui {message_queue:[]} run return

# 取出第一条消息
data modify storage namespace:ui current_message set from storage namespace:ui message_queue[0]

# 发送消息
execute as @a run tellraw @s {"nbt":"current_message","storage":"namespace:ui"}

# 移除已发送的消息
data remove storage namespace:ui message_queue[0]

# 继续调度
schedule function namespace:ui/process_queue 1t
```

### 陷阱与注意事项

1. **消息顺序可能混乱**：如果多个数据包同时添加消息，队列顺序可能不按预期。
2. **性能开销**：每 tick 处理队列会增加性能开销，尤其是队列很长时。
3. **消息丢失**：如果玩家在消息发送时不在线，消息会丢失。
4. **`tellraw` 无法控制显示位置**：消息会出现在聊天栏，可能被其他消息淹没。

---

## 方案对比

| 方案 | 版本要求 | 性能开销 | 适用场景 | 优点 | 缺点 |
|------|---------|---------|---------|------|------|
| Bossbar 独占 | 1.13+ | 低 | 需要持续显示的 UI（如进度条、状态指示） | 持久显示，支持颜色 | 数量有限，无法显示复杂内容 |
| Title 独占 | 1.11+ | 低 | 临时提示、通知 | 显示醒目，支持淡入淡出 | 无法持久，时间窗口不精确 |
| Scoreboard 侧边栏 | 1.13+ | 低 | 排行榜、状态面板 | 持续显示，支持多行 | 全局影响，无法个性化 |
| 聊天栏消息队列 | 1.15+ | 中 | 需要按顺序显示的消息 | 支持复杂 JSON，可控制顺序 | 性能开销，消息可能丢失 |

---

## 最佳实践建议

1. **优先使用 Bossbar**：对于需要持续显示的 UI，Bossbar 是最稳定的选择。
2. **避免同时使用多个 UI 机制**：如果可能，让所有数据包使用同一种 UI 机制，通过优先级协商避免冲突。
3. **使用全局约定**：所有数据包开发者应约定统一的 `scoreboard` 名称和优先级规则。
4. **考虑使用 `team` 属性**：通过 `team` 的 `collisionRule`、`seeFriendlyInvisibles` 等属性，可以控制玩家之间的交互，减少 UI 冲突。
5. **测试不同数据包组合**：在发布前，测试数据包与其他常见数据包的兼容性。

---
