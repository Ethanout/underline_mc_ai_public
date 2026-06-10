---
id: t0504
title: "随机数生成方法"
title_en: "random_number_generation_methods"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/randomnumber"
source_type: "mcc_wiki"
source_issue: "questions/randomnumber"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["random", "random-number", "uuid", "loot-table", "prng", "scoreboard"]
verified_in_game: false
---

## 核心洞见

Minecraft Java版有多种伪随机数生成方法，从1.20.2起/random命令是最优选择，旧版本可选用UUID、PRNG/LCG或战利品表等方法

## 代码示例

```mcfunction
# 方法1: /random命令（推荐，1.20.2+）
# 创建计分板
scoreboard objectives add random dummy
# 存储随机数到假玩家
/execute store result score #command random run random value 1..5
# 检查值
/execute if score #command random matches 1 run <command 1>
/execute if score #command random matches 2 run <command 2>
/execute if score #command random matches 3 run <command 3>
/execute if score #command random matches 4 run <command 4>
/execute if score #command random matches 5 run <command 5>
# 或使用范围
/execute if score #command random matches 1..3 run say 1, 2 or 3
/execute if score #command random matches 4..5 run say 4 or 5

# 方法2: UUID方法（旧版本）
summon area_effect_cloud ~ ~ ~ {Tags:["random_uuid"]}
execute store result score @s random run data get entity @e[type=area_effect_cloud,tag=random_uuid,limit=1] UUID[0] 1
scoreboard players operation @s random %= @s range
kill @e[type=area_effect_cloud,tag=random_uuid]

# 方法3: 战利品表方法（旧版本）
# 战利品表文件: data/example/loot_tables/random_loot_table.json
# 内容见下方JSON
# 命令:
execute store result score @s <OBJ> run loot spawn ~ ~ ~ loot example:random_loot_table

# 范围调整示例：从[-10,10]到[0,20]再偏移
# 假设RNG生成0-20，然后加-10得到-10到10
```

## 文件结构

- data/<namespace>/functions/random_example.mcfunction
- data/example/loot_tables/random_loot_table.json

## 用法

构建完数据包后，调用对应的函数或直接执行命令即可获取随机数。对于/random命令，直接运行execute store result score命令；对于UUID方法，运行包含summon和kill的完整命令序列；对于战利品表方法，运行loot spawn命令。随机数存储在指定的计分板中，可通过execute if score进行条件判断。

## 使用场景

['需要随机选择事件或物品时（如随机奖励、随机传送点）', '需要概率触发机制时（如1/10概率触发特殊效果）', '旧版本（1.20.2之前）中无法使用/random命令时，作为替代方案']

## 机制原理

文章介绍了多种伪随机数生成方法，核心机制各不相同：
1. /random命令（1.20.2+）：Minecraft内置的随机数生成命令，直接返回指定范围内的随机整数，是最简单高效的方法。
2. UUID方法：利用Minecraft生成实体时自动分配的UUID（128位整数）的随机性。通过summon实体、data get获取UUID[0]（32位整数部分），再用scoreboard operations的%=操作将其缩放到目标范围。UUID的生成基于伪随机算法，因此每次召唤实体都会得到不同的值。
3. 战利品表方法：利用execute store result与loot spawn命令的交互——loot spawn会返回生成的物品实体数量。通过设置战利品表的rolls范围为[min,max]，并让生成的物品数量为0（避免产生实际物品），即可将rolls次数作为随机数。
4. PRNG/LCG：使用线性同余生成器（LCG）算法，通过数学运算（乘法和取模）在计分板中生成伪随机数序列。
5. 范围调整：通过简单的数学变换（result + min = desired range）将任意RNG的输出范围映射到目标范围。

## 注意事项

- 所有方法生成的都是伪随机数，不是真正的随机数，但对大多数应用场景足够
- /random命令是1.20.2+版本的最佳选择，旧版本应使用其他方法
- UUID方法中，UUID[0]返回的是32位整数，使用%=操作后结果会变为0或正数
- 1.16之前版本UUID存储在UUIDLeast和UUIDMost中，需要使用缩放因子0.00000000023283064365386962890625（即1/2^32）来获取long的高32位
- 战利品表方法会短暂生成并立即移除物品实体，范围超过10000可能导致卡顿
- item rotation方法（方法4）已过时，不应使用
- running score方法（方法7）依赖时间，不适合需要同一tick内多次随机数的场景
- spreadplayers方法（方法6）存在边缘偏差问题，且区块加载不可靠
