# 100 问解答 — 基于知识库与官方文档

> **说明**：每条解答后标注来源。**[归档]** = 本地知识库 `归档/`；**[Wiki]** = `zh.minecraft.wiki`；**[DPI]** = `datapack-index` / `cr-019.github.io/datapack-index/`；**[DPW]** = `datapack.wiki`。
> 未标注「版本信息缺失」或「找不到交叉验证」的条目为多来源交叉验证过的内容。

---

## 一、输入与按键

### 1. 如何检测玩家按下某个键？

**可检测的键**（谓词 `input`，1.20.5+）：

```json
// data/<namespace>/predicate/is_jumping.json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "type_specific": {
      "type": "minecraft:player",
      "input": { "jump": true }
    }
  }
}
```

字段：`sneak`, `sprint`, `jump`, `left_click`, `right_click`, `forward`, `backward`, `left`, `right`。用法：`execute if predicate ns:is_jumping`。

**右键物品**（`used:carrot_on_a_stick` / `used:firework_star` 等可交互物品）：

```mcfunction
scoreboard objectives add click_rmb used:carrot_on_a_stick
execute as @a if score @s click_rmb matches 1.. run say 右键了
```

**注意**：F 键（交换物品/使用盾牌）和 Q 键（丢弃物品）没有直接谓词，需通过进度 `inventory_changed` / `item_used_on_block` 等间接检测。 **[归档-按键检测.md]** **[Wiki-谓词]** **[归档-弹药冷却.md]**

### 2. 如何区分"按住"和"按一下"？

**减半状态机法**（半减检测上升沿/下降沿）：

```mcfunction
# 简化写法（完整版在 按键检测.md）
scoreboard players operation @s state /= 2 const
execute if predicate my:input/jump run scoreboard players add @s state 4
execute if score @s state matches 2 run function my:on_press       # 刚按下
execute if score @s state matches 3 run function my:while_hold     # 正在按住
execute if score @s state matches 1 run function my:on_release     # 刚松开
```

**前后帧法**（两个记分板对比上一刻和这一刻）：

```mcfunction
execute if score @s rmb_prev matches 0 if score @s rmb_now matches 1 run say 刚按下
execute if score @s rmb_prev matches 1 if score @s rmb_now matches 1 run say 按住中
execute if score @s rmb_prev matches 1 if score @s rmb_now matches 0 run say 松开
scoreboard players operation @s rmb_prev = @s rmb_now
scoreboard players set @s rmb_now 0
```

原理：每 tick 通过谓词检测更新 `rmb_now`，对比上一刻状态判定变化。 **[归档-按键检测.md]**

### 3. 如何做组合输入？

组合示例：Shift+右键 → 两步骤检测

```mcfunction
execute if predicate ns:is_sneaking if predicate ns:is_right_click run function ns:special_skill
```

用两个谓词（或一个复合 `"all_of"` 谓词）同时检测。**注意**：原版不提供原生"同时按下"事件，组合输入最快也只能延迟 1 tick（50ms）判定，这是 MC 命令体系的固有限制。 **[归档-按键检测.md]** **[Wiki-谓词]**

### 4. 如何避免输入被原版行为干扰？

**右键替代方案**：使用 `carrot_on_a_stick` 或 `firework_star` 等物品，原版行为固定为"挥动"（无副作用），完全可用作物键。

**Shift 替代方案**：用 `used:carrot_on_a_stick` 彻底避免与原版交互冲突。如果必须用原版交互键（攻击/使用），需配合 `adventure` 模式 + `CanDestroy`/`CanPlaceOn` 限制。

**限制物品交互**：检测武器时用 `adventure` 模式 + `CanDestroy` 为空 → 玩家无法破坏/放置方块，但右键仍会触发进度。 **[归档-弹药冷却.md]** 无法 100% 拦截所有原版行为，以下交互无法完全避免：吃肉/喝药（物品含 `food`/`consumable` 组件时）、开门/拉杆（玩家在范围内时）。

> **找不到交叉验证**：1.21.5+ 的 `consumable` 组件配合 `use_remainder` 能否完全替代原版交互尚无定论。

### 5. 如何限制玩家在某些状态下不能操作？

记分板状态标记 + 条件拦截：

```mcfunction
# 硬直时禁止攻击
execute as @a[scores={stun=1..}] at @s run ...
# 在 tick 函数开头 return
execute if score @s stun matches 1.. run return run ...
```

对输入阶段的拦截。对原版固有行为（如移动、跳跃、攻击键本身的物理效果）无法用数据包完全拦截——例如玩家在硬直期间仍然可以跳跃（除非应用 `jump_boost` 负效果或修改属性）。

> **版本信息缺失**：1.21.5+ 的 `component` 系统是否允许更精细的输入屏蔽，目前无足够资料。

### 6. 如何实现输入缓冲？

记分板时间戳 + 冷却期输入标记：

```mcfunction
# 玩家按键时标记缓冲
execute if score @s cooldown matches 0 if predicate ns:attack run scoreboard players set @s buffer 1

# 冷却结束 + 有缓冲 → 自动执行下一段连击
execute if score @s cooldown matches 0 if score @s buffer matches 1 run {
    scoreboard players set @s buffer 0
    function ns:combo_next
    scoreboard players set @s cooldown 5  # 连击间隔
}
```

> **找不到交叉验证**：输入缓冲（input buffering）在 MC 命令体系中缺少社区标准实现，以上为基于通用状态机原理的推导，实现细节需自行验证。

### 7. 如何实现按键冷却？

```mcfunction
# load
scoreboard objectives add cooldown dummy

# tick
scoreboard players remove @a[scores={cooldown=1..}] cooldown 1

# 检测可用状态
execute if score @s cooldown matches 0 if predicate ns:skill run {
    function ns:do_skill
    scoreboard players set @s cooldown 20  # 1秒(20tick)冷却
}
```

**物品冷却**（原生 `use_cooldown` 组件，1.20.5+）：

```mcfunction
give @s stick[use_cooldown={seconds:5}]
```

**[归档-变量与数学运算.md]** **[归档-弹药冷却.md]**

---

## 二、角色状态与流程控制

### 8. 如何判断玩家当前处于什么状态？

记分板做状态枚举（整数标记）：

```mcfunction
# 定义状态常数
scoreboard players set STATE_IDLE const 0
scoreboard players set STATE_ATTACK const 1
scoreboard players set STATE_HURT const 2
scoreboard players set STATE_DODGE const 3

# tick 检测
execute unless predicate ns:is_moving run scoreboard players operation @s state = STATE_IDLE const
execute if predicate ns:is_moving run scoreboard players operation @s state = STATE_MOVE const
```

> **找不到交叉验证**：`is_moving` 的可靠检测方法（位置变化 vs 速度 vs 按键）无标准推荐。通过 `position` 变化检测有 1 tick 延迟，通过按键检测无法捕获惯性滑行。

### 9. 如何防止状态互相打架？

**状态优先级系统**：

```mcfunction
# tick 开头：根据优先级覆盖（数字越大越优先）
# 死亡 > 受击 > 攻击 > 移动 > 空闲
execute if score @s health matches ..0 run scoreboard players set @s state 4
execute if score @s stun matches 1.. run scoreboard players set @s state 3
execute if score @s state matches 2 if score @s combo_timer matches 0 run scoreboard players set @s state 0
```

**注意**：MC 命令体系是顺序执行，不存在真正的并发，但同一 tick 内的多段逻辑仍可能互相覆盖。需确保每个 tick 只在一个位置设置状态（推荐在 `#tick` 开头统一判定）。 **[归档-按键检测.md]**

### 10. 如何做一个简单的状态机？

```mcfunction
# 状态定义
# 0 = idle, 1 = attack_windup, 2 = attack_active, 3 = attack_recovery

# tick 中状态转移
execute if score @s state matches 0 if predicate ns:attack run scoreboard players set @s state 1
execute if score @s state matches 1 run { scoreboard players add @s attack_timer 1; execute if score @s attack_timer matches 5 run scoreboard players set @s state 2; execute if ... }
execute if score @s state matches 2 run { # 伤害判定; scoreboard players set @s state 3; scoreboard players set @s attack_timer 0 }
execute if score @s state matches 3 run { scoreboard players add @s attack_timer 1; execute if score @s attack_timer matches 10 run scoreboard players set @s state 0 }
```

**[归档-按键检测.md]**（状态机思想在状态检测中已有体现）

### 11. 如何让某件事只执行一次？

**advancement revoke + 检测**：

```mcfunction
# 检测区：
execute as @p[scores={entered_boss_room=0}] if entity @s[x=-100,y=64,z=-100,dx=20,dy=10,dz=20] run {
    scoreboard players set @s entered_boss_room 1
    function ns:boss/on_enter
}
```

**用 tag 标记**更轻量：

```mcfunction
execute as @e[type=zombie,tag=!spawned] run function ns:on_spawn
```

**用 storage 全局标记**：

```mcfunction
# 只在首次加载时设置 gamerule
execute unless data storage ns:setup_done run {
    gamerule doDaylightCycle false
    data modify storage ns:setup_done set value true
}
```

**[归档-变量与数学运算.md]**（计时器部分） **[归档-玩家数据存取.md]**

### 12. 如何做延迟执行？

**方案 A：`/schedule` 命令**（推荐，1.15+）：

```mcfunction
# 5 tick 后造成伤害
schedule function ns:deal_damage 5t
```

**方案 B：计时器**：

```mcfunction
scoreboard players set @s delay_timer 5
# tick 中：
scoreboard players remove @a[scores={delay_timer=1..}] delay_timer 1
execute if score @s delay_timer matches 0 run function ns:deal_damage
```

**注意**：`/schedule` 的上下文是服务器控制台（`@s` 失效），需用 `execute as <target> at <target> run schedule function ...` 绑定执行者。或者用 storage 传参。 **[Wiki-/schedule]** **[归档-变量与数学运算.md]**

### 13. 如何做阶段流程？

记分板做阶段标记 + 进度触发：

```mcfunction
# 教程阶段 0~3
execute if score @s tutorial matches 0 if score @s has_moved matches 1 run scoreboard players set @s tutorial 1
execute if score @s tutorial matches 1 if score @s has_jumped matches 1 run scoreboard players set @s tutorial 2
```

破坏性更新警告：1.20.5+ 的 `execute on` 子命令改变了部分上下文链的行为，基于 `@s` 的阶段流程需验证上下文一致性。 **[归档-变量与数学运算.md]**

### 14. 如何处理失败和重试？

```mcfunction
# 玩家死亡 → 标记失败
execute as @a[scores={death_count=1..}] run {
    scoreboard players set @s phase 0          # 重置阶段
    scoreboard players set @s checkpoint 0     # 重置检查点
    execute at @s positioned -100 64 -100 run {
        execute as @s run tp @s -100 65 -100  # 传送回检查点
    }
    # 重置机关
    fill -100 64 -100 -80 64 -80 air
    # 重置敌人
    kill @e[type=!player,tag=boss_room]
}
```

> **找不到交叉验证**："重试"的完整框架（保存/恢复场景状态）无标准社区实现，以上为通用流程设计。

### 15. 如何做暂停感？

- 敌人暂停：用 `attribute @e[type=...] generic.movement_speed base set 0` + `NoAI 标记`
- 子弹暂停：停止 tick 函数的计时器更新，子弹位置不变
- 计时器暂停：条件执行 `execute unless score @s paused matches 1 run ...`

全局暂停需要将 `#tick` 标签中所有逻辑包裹在条件检测后执行。**[归档-变量与数学运算.md]**

---

## 三、移动与手感

### 16. 如何检测玩家是否在移动？

**方法 A**（位置变化检测，延迟 1 tick）：

```mcfunction
# load
scoreboard objectives add pos_x dummy
scoreboard objectives add pos_z dummy

# 存储当前位置（总比实测晚 1 tick）
execute store result score @s pos_x run data get entity @s Pos[0] 1000
execute store result score @s pos_z run data get entity @s Pos[2] 1000
```

**方法 B**（按键谓词，实时但有惯性误差）：

```mcfunction
execute if predicate ns:is_moving_key run ...  # forward/backward/left/right
```

> **找不到交叉验证**：MC 没有原生的"玩家是否正在移动"API，以上方法均有缺陷。方法 A 在转角处有 1~3 tick 延迟，方法 B 在惯性滑行/击退时无法覆盖。

### 17. 如何制作冲刺、闪避、击退、弹跳？

三种方案，各有优劣：

**A) 直接传送**（简单但穿墙）：

```mcfunction
tp @s ^ ^ ^5
```
穿墙，仅适合原型。

**B) player_motion**（末影水晶爆炸）：

https://github.com/MulverineX/player_motion

末影水晶爆炸推动玩家，稳定，但消耗略高，连续应用需 2~3 tick 冷却，网络不好有闪烁问题。

**C) fptrick_impulse**（附魔冲量，推荐）：

利用 `location_changed` 附魔触发器 + 浮点位溢出消除方向影响。性能好，连续应用仅需 1 tick 冷却，无闪烁问题。缺点：吃掉已有加速度（跳起瞬间）、打断物品使用。

局部坐标系动量（前进/左/上方向）可手写对应方向的附魔实现。

**[归档-如何给予玩家冲量移动.md]** 内含完整的 `fptrick_impulse` 数据包。

### 18. 如何让移动看起来平滑？

- 直接 `tp` 会穿模/抖动 → 不可接受
- `player_motion` 和 `fptrick_impulse` 通过 motion（速度向量）实现平滑位移
- 骑乘实体方案：让玩家骑乘 marker/盔甲架，通过移动实体带动玩家

> **找不到交叉验证**：MC 命令体系无法做到帧级插值，所有"平滑"方案本质上是 motion 物理或 tick 级微调。没有官方的 "smooth tp" 命令。

### 19. 如何限制玩家走出区域？

```mcfunction
# 空气墙（传送门）：每 tick 检测并传送回去
execute as @a[x=-200,dx=10] at @s run tp @s -195 ~ ~
# 替代：屏障方块、世界边界（worldborder）
worldborder center 0 0
worldborder set 200
```

> **找不到交叉验证**：没有标准化的"区域限制"数据包方案。屏障方块和 worldborder 是原生方案，传送回弹需要手动实现。

### 20. 如何做平台跳跃检测？

```mcfunction
# 检测是否站在地面上
execute if block ~ ~-0.1 ~ #minecraft:passable run ...  # 在空中
execute unless block ~ ~-0.1 ~ #minecraft:passable run ...  # 在地上

# 或者用 predicate
execute if predicate ns:is_on_ground
```

> **找不到交叉验证**：`is_on_ground` 在 1.21.5+ 的谓词系统中有无新增字段无资料验证。

### 21. 如何做二段跳？

```mcfunction
# load
scoreboard objectives add jumps dummy

# tick
# 落地重置跳跃次数
execute as @a if block ~ ~-0.1 ~ #minecraft:passable run scoreboard players set @s jumps 0

# 跳跃消耗
execute as @a if predicate ns:jump if score @s jumps matches 0 run { scoreboard players add @s jumps 1 }
execute as @a if predicate ns:jump if score @s jumps matches 1 run {
    scoreboard players add @s jumps 1
    function ns:double_jump  # fptrick_impulse 或其他冲量方法
}
```

**防止无限跳**的核心：`jumps` 记分板限制最大次数。**[归档-如何给予玩家冲量移动.md]**

### 22~24. 2D横版移动 / 惯性滑行 / 朝向移动

> **找不到交叉验证**：这些"游戏手感"级别的功能超出了 MC 命令体系的标准参考资料，涉及冲量附魔的局部坐标调整（fptrick_impulse 中有部分实现，但 2D 横版等无社区标准方案）。

---

## 四、视角与镜头

### 25~29. 视角控制 / 过场镜头 / 第三人称 / 镜头震动 / 防恶心

**命令支持**：

```mcfunction
# 强制旋转
execute as @s at @s run tp @s ~ ~ ~ facing <x> <y> <z>

# 限制旋转（每 tick 强制恢复）
tp @s ~ ~ ~ <fixed_yaw> <fixed_pitch>

# 第三人称（骑乘实体）
/ride @s mount <entity>
```

**镜头震动**：通过快速随机旋转 `tp @s ~ ~ ~ <yaw> <pitch>` 模拟，但强制 tp 会导致视角"闪烁/卡顿"而非平滑震动。

> **找不到交叉验证**：MC 没有原生镜头控制 API，所有视角控制都是基于强制 tp/旋转实现，体验受限于 20 tick/s 的更新率。过场镜头（缓动移动路径）没有社区标准实现，需要手动递归函数插值。

---

## 五、动画与表现

### 30~37. 播放角色动画 / 同步判定 / 多段攻击 / 中断 / 朝向 / 命中反馈

**展示实体动画**（1.19.4+）：

```mcfunction
summon item_display ~ ~ ~ {
    item:{id:"minecraft:diamond_sword"},
    teleport_duration:5,
    interpolation_duration:1,
    transformation:{left_rotation:[0,0,0,1],right_rotation:[0,0,0,1],translation:[0.0,0.5,0.0],scale:[2.0,2.0,2.0]}
}
```

修改 `transformation` 矩阵实现插值动画。详细参考 Animated Java 工具（DPI 推荐）。

**资源包物品模型动画**（1.21.4+ 物品映射）：

```json
{
  "type": "minecraft:range_dispatch",
  "property": "minecraft:use_duration",
  "scale": 0.05,
  "entries": [
    { "threshold": 0.0, "model": { "type": "minecraft:model", "model": "ns:item/swing_0" } },
    { "threshold": 0.5, "model": { "type": "minecraft:model", "model": "ns:item/swing_1" } }
  ]
}
```

**同步判定**：在对应的 tick 计时器触发伤害函数，而非按键瞬间触发：

```mcfunction
# 攻击按键 → 设置状态为 attack（前摇）
# 5 tick 后 → 伤害判定
# 15 tick 后 → 结束
```

**朝向处理**：展示实体的 `billboard` 字段控制面向方式（`fixed`/`center`/`horizontal`/`vertical`）。

**命中反馈**：

```mcfunction
# 粒子
execute at @e[tag=target] run particle entity_effect{color:[1.0,0.0,0.0,1.0]} ~ ~1 ~ 0.2 0.2 0.2 0 5
# 击退（fptrick_impulse 库）
# 音效
playsound entity.player.hurt master @a ~ ~ ~ 1 1
```

**[归档-生成自定义实体.md]** **[归档-自定义物品模型与资源包.md]** **[归档-粒子系统.md]**

---

## 六、特效与反馈

### 38~45. 粒子特效 / 方向 / 范围提示 / 残影 / 拖尾 / 屏幕效果 / UI音效 / 性能

**粒子系统基础**：

```mcfunction
# 基本粒子
particle minecraft:flame ~ ~ ~ 0 0 0 0 1

# 带颜色实体效果
particle entity_effect{color:[1.0,0.5,0.0,1.0]} ~ ~ ~ 0 0 0 0 1

# 物品粒子
particle item minecraft:diamond ~ ~ ~ 0 0 0 0 1

# 粉尘（Dust）
particle dust{color:[1.0,0.0,0.0],scale:2.0} ~ ~1 ~ 0.5 0.5 0.5 0 10

# count=0 时 delta 变方向向量
particle minecraft:flame ~ ~ ~ ^1 ^0 ^0 0.1 0 force
```

**范围提示**：用粒子画圆 → 需要递归函数在多个位置上生成粒子。

**残影/拖尾**：用展示实体 + 逐渐 `teleport_duration` 淡出，或连续生成多个半透明粒子。

**屏幕效果**：用 `title @s times ...` + 颜色叠加，或资源包着色器。

**UI 反馈**：`playsound` + `title @s actionbar`。

**特效性能**：参考 **[归档-调试方法.md]** 中的 `F3+L` 分析器，粒子 `count` 不要超过 50/次，展示实体控制在 200 以内。

**[归档-粒子系统.md]**

---

## 七、数学与空间判断

### 46. 如何获取玩家面向方向？

```mcfunction
# 获取 yaw/pitch
execute store result score @s yaw run data get entity @s Rotation[0] 1000
execute store result score @s pitch run data get entity @s Rotation[1] 1000
```

**局部坐标方向**：`^ ^ ^` —— `^x` 向右，`^y` 向上，`^z` 向前。

**[DPI-命令/函数体系]** **[Wiki-/execute]**

### 47~48. 检测玩家前方目标 / 射线检测

**`on target` 子命令**（最快，1.20.5+）：

```mcfunction
execute as @a at @s on target run say 正在看 @s
```
不能检测方块，距离限制较死。

**精密射线检测**（MRCD - Minecraft Ray Casting Data-pack，DPI 推荐）：

递归函数 + `^ ^ ^` 步进 + 方块/实体检测：

```mcfunction
# raycast.mcfunction
particle portal ~ ~ ~ 0 0 0 0 1
execute if block ~ ~ ~ #minecraft:passable run function ns:raycast/loop

# loop.mcfunction
positioned ^ ^ ^0.1 run function ns:raycast/step

# step.mcfunction
execute as @e[type=!player,distance=..0.5,limit=1] run function ns:on_hit_entity
execute unless block ~ ~ ~ #minecraft:passable run function ns:on_hit_block
execute if score #dist tmp matches ..100 run function ns:raycast/loop
```

**[归档-获取玩家操作目标.md]**

### 49~51. 扇形 / 圆形 / 背后检测

**圆形**：`distance=..<半径>` 选择器。

**扇形**：

```mcfunction
# 粗略扇形检测（正前方 90°）
execute as @e[type=!player,distance=..10] at @s facing entity @p feet positioned as @p at @p positioned ^ ^ ^ rotated ~0 ~ positioned ^ ^ ^10 run execute if entity @s[distance=..15]
```

**背后**：

```mcfunction
execute as @e[type=!player,distance=..5] at @s rotated as @p run if entity @s[ry=180,ry=0] run say 在玩家面前
execute as @e[type=!player,distance=..5] at @s rotated as @p run unless entity @s[ry=-90,ry=90] run say 在玩家背后
```

**[归档-变量与数学运算.md]**（多边形检测部分） > **找不到交叉验证**：扇形和背后检测在社区中有多种变体实现，但不构成标准，需自行测试精确度。

### 52. 如何计算两个点之间的距离？

计分板运算欧几里得距离：

```mcfunction
# sqrt((x1-x2)² + (y1-y2)² + (z1-z2)²)
execute store result score #dx tmp run data get entity @s Pos[0] 1000
execute store result score #dy tmp run data get entity @s Pos[1] 1000
execute store result score #dz tmp run data get entity @s Pos[2] 1000
# 减目标位置 → 平方 → 求和 → 开方（用 sqrt 函数）
```

**更快方案**：直接用选择器 `distance=..<半径>`（底层是平方距离比较，性能更好）。 **[归档-变量与数学运算.md]**

### 53~54. 追踪弹 / 抛物线

**追踪弹**：展示实体作为弹体，每 tick 执行 `tp @s ^ ^ ^<speed>` + 朝向目标方向。

**抛物线**：

```mcfunction
# 每 tick 更新位置
# x += vx * dt, y += vy * dt + 0.5 * g * dt², vy += g * dt
execute store result score #vy tmp run data get entity @s Motion[1] 100  # 1.20.5+ 用 nbt
```

> **找不到交叉验证**：MC 命令体系中无原生抛物线 API，以上为物理模拟的通用推导。1.20.5+ 的 `Motion` 对玩家不可直接修改，对展示实体/物品等可用。

### 55~57. 螺旋/波浪/随机/相对坐标

**螺旋**（极坐标 → 直角坐标）：

```mcfunction
# 每 tick: angle += speed, x = center_x + r * cos(angle), z = center_z + r * sin(angle)
# 余弦近似见 变量与数学运算.md
cos(d) = 1 - 5 / ((180/d)² + 1)
```

**相对坐标**：直接用 `^ ^ ^` 局部坐标系统。 `^5 ^ ^` = 前方 5 格，`^-5 ^ ^` = 后方。 **[归档-变量与数学运算.md]**

---

## 八、战斗与判定

### 58~67. 伤害系统 / 命中盒 / 无敌帧 / 格挡 / 多目标 / 友方 / 投射物 / 锁定 / Boss / 伤害数字

**伤害检测 - 进度法**：

```json
{
  "criteria": { "a": { "trigger": "minecraft:entity_hurt_player" } },
  "rewards": { "function": "namespace:player_hurted" }
}
```
函数内：`execute on attacker run say 攻击者`。注意 `on attacker` 有约 100 tick 的记忆残留。 **[归档-攻击与受击检测.md]**

**全实体伤害检测 - 附魔法**（1.21+）：

给实体上鞍 + 自定义附魔 `effects: { minecraft:post_attack: [...] }`，注册 `entity_hurted` 触发器。注意：附魔定义不可热重载，需重进世界。

**濒死检测**：[Hit Match 方案](https://github.com/picarrow/hit-match) —— 在 storage 中用 UUID 追踪实体，按轮询频率分 tick 检查是否即将死亡。

**伤害系统**：1.20.5+ 的 `/damage` 命令：

```mcfunction
damage @e[type=!player,distance=..3] 10.0 minecraft:mob_attack at @s by @s
```

**无敌帧**：

```mcfunction
# tick 中
execute if score @s invuln matches 1.. run scoreboard players remove @s invuln 1
execute if score @s invuln matches 0 run ...
```

**投射物**：

```mcfunction
summon arrow ~ ~ ~ {item:{id:"minecraft:arrow"},HasBeenShot:true,Tags:["custom_proj"]}
# advancement 监听 projectile_landed
```

**伤害数字**：用 `text_display` 实体显示：

```mcfunction
summon text_display ~ ~1 ~ {
    text:{text:"-25",color:"red"},
    billboard:"center",
    teleport_duration:20,
    interpolation_duration:-1
}
```

> 伤害数字的自动上飘和消失需额外函数控制。**[归档-攻击与受击检测.md]** **[归档-生成自定义实体.md]**

---

## 九、敌人与行为

### 68~75. 发现玩家 / 追击 / 攻击 / 预警 / 硬直 / 死亡 / 穿墙 / 刷怪

**基础属性修改**：

```mcfunction
attribute @s generic.movement_speed base set 0.5
attribute @s generic.max_health base set 200.0
attribute @s generic.attack_damage base set 10.0
attribute @s generic.follow_range base set 64.0
attribute @s generic.armor base set 20.0
attribute @s generic.knockback_resistance base set 1.0

# 目标设定
execute as @e[type=zombie] run data modify entity @s target set from entity @p UUID
```

**消除狼的主动攻击**：

```mcfunction
execute if data entity @s AngryAt run attribute @s generic.follow_range modifier add anger -1 add_multiplied_total
execute unless data entity @s AngryAt run attribute @s generic.follow_range modifier remove anger
```

**自定义实体生成**（1.20.5+ 装备格式）：

```mcfunction
summon minecraft:zombie ~ ~ ~ {
    HandItems:[
        {id:"minecraft:diamond_sword",count:1,components:{"minecraft:enchantments":{"minecraft:sharpness":5}}},
        {}
    ],
    ArmorItems:[{id:"minecraft:diamond_boots"},{id:"minecraft:diamond_leggings"},{id:"minecraft:diamond_chestplate"},{id:"minecraft:diamond_helmet"}],
    Attributes:[
        {Name:"minecraft:max_health",Base:200.0},
        {Name:"minecraft:movement_speed",Base:0.5},
        {Name:"minecraft:attack_damage",Base:15.0},
        {Name:"minecraft:scale",Base:2.0}
    ],
    Health:200.0,
    PersistenceRequired:true
}
```

**防止穿墙**：自定义移动（`tp`/`motion`）无法保证碰撞检测，原生 AI + `follow_range` 是最稳定的选择。**数据包没有原生碰撞检测**。

**刷怪节奏**：用 `#tick` 中的计时器 + `@e[type=...,distance=..20]` 计数。

**[归档-AI微调.md]** **[归档-生成自定义实体.md]**

---

## 十、UI 与交互

### 76~82. 菜单 / 技能栏 / 血条 / 对话 / 提示 / 冲突 / 教程

**菜单**：用物品栏 UI（`container` 类型 `minecraft:chest` 的 `CustomName` + 物品摆放），或来自 `book`/`sign`/`tellraw` 的交互。

**技能栏**：hotbar 物品代表技能 + `used:carrot_on_a_stick` 检测右键 + `item_model` 显示图标 + `use_cooldown` 冷却。

**血条/能量条**：`bossbar` 命令：

```mcfunction
bossbar add hp "血量"
bossbar set hp color red
bossbar set hp max 100
bossbar set hp value 75
bossbar set hp players @a
```

**ActionBar** 实时显示：

```mcfunction
title @s actionbar {"text":"❤ HP: 75/100","color":"red"}
```

**对话系统**：用 `tellraw` 逐字显示 + `schedule` 延迟下一句，或用 `book` 显示选项。

**交互提示**：`execute if entity @s[x=-100,y=64,z=-100,distance=..3] run title @s actionbar ...`

**UI 冲突**：部分原版 UI 无法隐藏（如物品栏打开时），可切换 `adventure` 模式限制操作。

> 聊天类型（chat_type）属于注册表数据，不可 `/reload`，需重进世界。

**教程提示**：进度触发器 + 记分板阶段。

**[归档-文本与聊天.md]** **[归档-队伍与聊天格式.md]** **[归档-获取玩家操作目标.md]**

---

## 十一、资源包与模型

### 83~87. 模型替换 / 自定义外观 / UI图标 / 模型编号管理 / 音画同步

**物品模型**（1.21.4+ 独立物品定义）：

```mcfunction
give @s stick[item_model="ns:my_sword"]
```

资源包结构：

```
assets/<namespace>/
├── models/item/my_sword.json    # 模型
├── textures/item/my_sword.png   # 材质
└── items/my_sword.json          # 物品定义（大脑）
```

**模型映射类型**：`model`（固定）、`select`（枚举）、`condition`（布尔）、`range_dispatch`（数值分段，蓄力动画）、`composite`（复合，如身体+装备）。

**UI 图标**：通过 `text_display` 展示自定义文字，或用 `font` 字体位图创建特殊字符。

**模型编号管理**：官方无管理工具。社区用资源包目录结构命名约定（如 `ns:weapons/sword_iron`, `ns:skills/fireball_icon`）。

**音画同步**：通过同一计时器序列控制：

```mcfunction
# seq_tick.mcfunction
execute if score @s anim matches 6 run playsound item.sword.swipe master @a ~ ~ ~ 1 1
execute if score @s anim matches 9 run { function ns:deal_damage; playsound entity.player.attack.strong master @a ~ ~ ~ 1 1 }
```

**[归档-自定义物品模型与资源包.md]**

---

## 十二、关卡与场景

### 88~93. 区域检测 / 机关 / 重置 / 隐藏区域 / 动态场景 / 防破坏

**区域检测**：

```mcfunction
execute as @a[x=-100,dx=20,y=64,dy=10,z=-100,dz=20] run function ns:boss_room/enter
```

**机关**：`/setblock`, `/fill`, `/clone`, `/data merge block` 修改方块状态。

**场景重置**：

```mcfunction
# 用结构方块保存初始状态
structure save boss_room_initial -100 64 -100 -80 74 -80
# 重置时加载
structure load boss_room_initial -100 64 -100
```

**防破坏**：

```mcfunction
gamerule mobGriefing false          # 防苦力怕、末影龙破坏
# 限制玩家破坏
gamemode adventure @a
```

> 结构方块（`structure`）是推荐场景保存/恢复方案，但注意大型结构的性能消耗。**[Wiki-/structure]** **[归档-全局效果与世界规则.md]**

---

## 十三、时间、节奏与性能

### 94~100. 全局计时器 / 局部计时器 / 降频 / 实体上限 / 清理 / 多人兼容 / 调试

**全局计时器**：

```mcfunction
# 用 time query gametime
execute store result score #game_time tmp run time query gametime
execute if score #game_time tmp matches 1000..2000 run ...
```

**局部计时器**（每个实体独立的冷却）：

```mcfunction
data modify entity @s custom_data merge {cooldown:20}
# 用 data get entity @s custom_data.cooldown 读取
```

**降频/分 tick**：

```mcfunction
# 每 5 tick 运行一次
execute if score #mod clock matches 0 run function ns:heavy_task
# 错开不同任务
execute if score #mod clock matches 1 run function ns:other_task
```

**减少检测**：
- 用 `distance=..` 限制选择器范围
- 用 `tag` 标记已处理实体避免重复检测
- 不要在 `#tick` 中直接 `@e` 无限制扫描
- 用 predicate 替代 `execute if data`（更快）
- 用 `if items` 替代 `clear 0` 当合成格有物品时

**实体清理**：

```mcfunction
# 定时清理临时实体
schedule function ns:cleanup 100t
# cleanup.mcfunction
kill @e[tag=temp_effect,distance=..200]
```

**多人兼容**：
- 避免全局 state 变量 — 用 `@s` 个人记分板
- 用 ID 系统索引玩家数据
- 一个玩家触发的剧情用 `@s` 隔离

**调试方法**：

```mcfunction
# 侧边栏监视
scoreboard objectives setdisplay sidebar test

# tellraw 调试
tellraw @a [{"score":{"name":"@s","objective":"test"}}]

# 粒子标记
particle cloud ~ ~ ~ 0 0 0 0 0 force

# F3+L 火焰图（录制 10 秒 profiler）
# /tick sprint 压力测试
```

**[归档-变量与数学运算.md]** **[归档-调试方法.md]** **[归档-玩家数据存取.md]** **[归档-Storage数据库与宏.md]**

---

## 附录：各来源置信度汇总

| 来源 | 置信度 | 说明 |
|------|:---:|------|
| `知识库/归档/` | ~80% | 部分内容标注了 `<HAS_PROBLEM>`，如 UUID 随机数法的战利品表用法、LCG 随机数的范围说明等，使用前需自行验证 |
| `zh.minecraft.wiki` | 99%+ | 官方 Wiki，持续跟随快照更新，但命令页面可能落后于快照 |
| `datapack.wiki` | 99%+ | 社区维护的准确参考，1.20.5+ 内容较全 |
| `datapack-index` / cr-019.github.io | 99%+ | 索引了大量社区教程和实践，本身可信但需注意原始链接可能有"死链" |
