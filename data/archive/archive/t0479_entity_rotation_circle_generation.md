---
id: t0479
title: "旋转实体画圆"
title_en: "entity_rotation_circle_generation"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/makecircle"
source_type: "mcc_wiki"
source_issue: "questions/makecircle"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["circle", "rotation", "local-coordinates", "command-blocks", "building"]
verified_in_game: false
---

## 核心洞见

利用实体旋转和局部坐标 ^ ^ ^ 可以自动生成完美圆形，无需手动放置方块

## 代码示例

```mcfunction
# 1. 召唤中心实体
/summon armor_stand ~ ~ ~

# 2. 标记实体
# Java 1.13+
/tag @e[type=armor_stand,sort=nearest,limit=1] add center
# Java 1.21+
/tag @n[type=armor_stand] add center

# 3. 放置方块（放在重复命令方块中）
execute as @e[tag=center] at @s run setblock ^ ^ ^10 stone

# 4. 旋转实体（放在连锁命令方块中）
execute as @e[tag=center] at @s run tp @s ~ ~ ~ ~ ~2.35
```

## 文件结构

（待补充）

## 用法

将第3步命令放入重复命令方块，第4步命令放入连锁命令方块（连接到重复命令方块），然后激活重复命令方块。实体将不断旋转并在前方放置方块，形成圆形。完成后关闭命令方块。

## 使用场景

['快速生成圆形建筑轮廓或装饰图案', '创建圆形粒子效果或实体阵列（替换 /setblock 为 /summon）', '生成环形结构或圆形填充区域（配合 /fill 命令）']

## 机制原理

该技术利用 Minecraft 的局部坐标系统 `^ ^ ^`，其中 `^ ^ ^X` 表示实体面向方向前方 X 格。通过让一个实体（如盔甲架）持续旋转，并在每个 tick 在其前方放置方块，实体旋转一周后，所有放置的方块就构成了一个圆形。旋转角度步长决定了圆形的精度：步长越小，圆形越平滑，但需要更多 tick 完成。步长可以通过公式 `deg = (180 * d) / (π * radius)` 计算，其中 d 是期望的方块间距（通常为1），radius 是圆的半径。由于 Minecraft 的方块是离散的，实际步长通常取计算值的一半以确保连续。

## 注意事项

- 对于超大圆形（直径数百格），Minecraft 内部角度计算精度有限（可能四舍五入到0.01°），会导致旋转跳跃、圆形不完整（原文表述需核实）
- Java 版建议使用 marker 实体代替盔甲架以获得更好性能
- 基岩版和 Java 版的实体选择器语法不同，需注意区分
- 此方法生成的圆形是离散方块近似，不是完美几何圆
