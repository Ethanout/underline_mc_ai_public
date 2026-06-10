---
id: t0434
title: "减法排序法"
title_en: "scoreboard_ranking_by_subtraction"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202504/7/content"
source_type: "feature_article"
source_issue: "202504"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["排序算法", "计分板", "虚拟玩家", "小游戏"]
verified_in_game: false
---

## 核心洞见

通过递归减法将分数归零的顺序反向映射为排名，无需比较运算即可实现任意数量玩家的排序。

## 代码示例

```mcfunction
# 初始化（假设score已有分数）
scoreboard objectives add temp dummy
scoreboard objectives add ranked dummy
scoreboard objectives add .Result dummy
scoreboard objectives add .Opposite dummy
scoreboard objectives add .Ranked dummy

# 复制分数到temp
execute as @a run scoreboard players operation @s temp = @s score

# 递归减法循环（需在函数中重复执行直到所有temp为0）
# 每次循环：对所有temp>0的玩家减1，若某玩家temp变为0，则将其排名设为当前.Opposite值
scoreboard players remove @a[scores={temp=1..}] temp 1
# 检测刚归零的玩家（需在减法后立即执行）
execute as @a[scores={temp=0}] if score @s temp = @s temp run scoreboard players operation @s ranked = .Opposite
scoreboard players add .Opposite 1

# 当所有temp为0后，重置.Opposite为1，.Ranked设为最高分
scoreboard players set .Opposite 1
scoreboard players operation .Ranked = .Result

# 反向输出排名循环
# 当有玩家分数等于.Ranked时，将其排名设为.Opposite，然后.Ranked减1，.Opposite加1
execute as @a if score @s score = .Ranked run scoreboard players operation @s ranked = .Opposite
execute as @a if score @s score = .Ranked run scoreboard players add .Opposite 1
execute as @a if score @s score = .Ranked run scoreboard players remove .Ranked 1

# 当.Opposite等于.Result时结束，清除临时计分板
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用计分板减法操作的原子性和虚拟玩家作为临时存储。核心机制是：1) 将原始分数复制到临时计分板'temp'；2) 对所有玩家递归执行'temp -= 1'，最先归零的玩家分数最低（排名最后）；3) 通过虚拟玩家'.Ranked'记录当前最高分，'.Opposite'作为反向计数器（从1递增），当玩家分数等于'.Ranked'时，将其排名设为'.Opposite'的值（即排名从低到高为1,2,3...），然后'.Ranked'减1寻找下一名；4) 当'.Opposite'等于参与排名的总人数时结束。特殊之处在于：它用减法代替比较，用虚拟玩家代替实体存储中间状态，避免了实体查找开销，且时间复杂度为O(N*M)（N玩家数，M最大分数差），但通过反向映射将排名输出为递增整数。

## 注意事项

- 递归减法循环必须确保每次只减1，否则无法正确检测归零时刻
- 虚拟玩家名称前加'.'可避免与真实玩家混淆，但需注意计分板操作时虚拟玩家不会自动执行命令
- 如果分数范围极大（如百万级），减法循环次数会过多，需考虑优化或限制分数范围
- 常见误解：开发者通常认为排序必须使用比较或交换算法（如冒泡排序），或依赖实体坐标/计分板排序命令，但原版计分板没有直接排序接口。
