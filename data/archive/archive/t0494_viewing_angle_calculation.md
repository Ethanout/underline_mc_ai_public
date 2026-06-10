---
id: t0494
title: "视角角度计算"
title_en: "viewing_angle_calculation"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/lookat"
source_type: "mcc_wiki"
source_issue: "questions/lookat"
version_min: "1.19.50"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["数学", "三角函数", "视线检测", "distance参数"]
verified_in_game: false
---

## 核心洞见

execute 视线检测的 `distance` 参数与视角宽容度之间存在精确的三角函数关系（`r = 2 × sin(α/2)`），可以互相换算——这套视线检测本身也是通过 execute 的来回移动判断的。

## 代码示例

```mcfunction
# ── 完整视线检测命令 ──────────────────────────────────────
# 通用格式：检测玩家是否看向 <实体选择器 / 坐标>
execute as @a at @s anchored eyes facing <entity / coordinates> anchored feet positioned ^ ^ ^1 rotated as @s positioned ^ ^ ^-1 if entity @s[distance=..0.1] run <命令>

# 示例1：看向最近带有 tag "target" 的牛的眼睛
execute as @a at @s anchored eyes facing entity @e[type=cow,tag=target,limit=1,sort=nearest] eyes anchored feet positioned ^ ^ ^1 rotated as @s positioned ^ ^ ^-1 if entity @s[distance=..0.1] run say 看向了牛

# 示例2：看向坐标 10 20 30
execute as @a at @s anchored eyes facing 10 20 30 anchored feet positioned ^ ^ ^1 rotated as @s positioned ^ ^ ^-1 if entity @s[distance=..0.1] run say 看向了那个位置

# 示例3：同时以目标实体的视角执行命令（在目标实体处执行）
# 在 facing entity 后加 at <原始选择器>
execute as @a at @s anchored eyes facing entity @e[type=cow,limit=1] eyes at @e[type=cow,limit=1] anchored feet positioned ^ ^ ^1 rotated as @s positioned ^ ^ ^-1 if entity @s[distance=..0.1] run say 我在看牛，也在牛的位置执行

# ── 角度 ↔ distance 换算 ──────────────────────────────────
# distance = 2 × sin(视角宽容度 / 2)
# 视角宽容度 = 2 × arcsin(distance / 2)
#
# 常用参考：
# distance=0.1 ≈ 5.73°（约 6°）
# distance=0.5 ≈ 28.96°（约 29°）
# distance=1.0 = 60°
# distance=2.0 = 180°（全方向）
```

## 文件结构

（无特定文件结构，单条命令即可使用）

## 用法

将命令放入 tick 函数或命令方块中，替换 `<entity / coordinates>` 为目标，替换末尾 `run <命令>` 为触发逻辑。`distance` 参数控制检测宽容度，建议保持在 0.5 以下。

## 使用场景

- 检测玩家是否看向特定实体（NPC 交互、怪物锁定）
- 检测玩家是否看向特定坐标（机关触发、区域检测）
- 精确控制视线检测灵敏度时根据公式计算 distance

## 机制原理

这套视线检测通过 execute 的来回移动实现：

1. `anchored eyes` — 将执行原点移到玩家眼部
2. `facing <目标>` — 将执行朝向旋转到目标方向
3. `positioned ^ ^ ^1` — 沿目标方向前进 1 格
4. `rotated as @s` — 将朝向恢复为玩家原始朝向
5. `positioned ^ ^ ^-1` — 沿玩家原始朝向后退 1 格
6. `if entity @s[distance=..r]` — 检测最终位置是否在玩家眼部附近

若玩家确实看向目标，两次移动的合向量接近零，最终位置回到眼部附近；若没有看向目标，最终位置会偏离。

**distance 与角度的关系**：设视角偏差为 α，前进 1 格后位置偏移 sin(α)，后退 1 格沿原方向，两次位移的向量差大小为 `2 × sin(α/2)`。因此 `distance = 2 × sin(α/2)`。

## 注意事项

- `anchored eyes` 后必须跟一个 `positioned ^ ^ ^` 子命令才能正确生效（MC-169665 的影响）
- 此方法仅适用于检测是否看向**特定目标**（实体或坐标），不适用于通用射线检测
- distance 必须在 0~2 之间，distance=2 意味着全方向均命中
- 建议 distance 保持 0.5 以下以获得合理精度
