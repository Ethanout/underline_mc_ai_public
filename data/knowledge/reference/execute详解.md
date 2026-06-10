# /execute 详解

## 基本结构
```
execute <子命令1> <子命令2> ... run <命令>
```

## 修改子命令（可链式组合）

| 子命令 | 作用 |
|--------|------|
| `as <targets>` | 设置执行者（fork 到每个实体） |
| `at <targets>` | 设置位置+旋转+维度 |
| `positioned <pos>` | 设绝对位置 |
| `positioned as <targets>` | 设为目标位置 |
| `positioned over <heightmap>` | 设为目标上的高度（`world_surface`/`motion_blocking`/`ocean_floor`） |
| `rotated <yaw> <pitch>` | 设绝对旋转 |
| `rotated as <targets>` | 设为目标旋转 |
| `in <dimension>` | 设维度 |
| `facing <pos>` | 朝向坐标 |
| `facing entity <targets> (eyes\|feet)` | 朝向实体 |
| `align <axes>` | 坐标取整对齐（xyz组合） |
| `anchored (eyes\|feet)` | 设锚点 |
| `summon <entity>` | 召唤实体并以其身份执行 |
| `on <relation>` | 按关系选择（attacker/controller/leasher/origin/owner/passengers/target/vehicle） |

## 条件子命令

```
if|unless biome <pos> <biome>
if|unless block <pos> <block>
if|unless blocks <start> <end> <dest> (all|masked)
if|unless data block <pos> <path>
if|unless data entity <target> <path>
if|unless data storage <id> <path>
if|unless dimension <dimension>
if|unless entity <targets>
if|unless function <function>
if|unless items block <pos> <slots> <predicate>
if|unless items entity <targets> <slots> <predicate>
if|unless loaded <pos>
if|unless predicate <predicate>
if|unless score <t> <o> (=|<|>|<=|>=) <s> <so>
if|unless score <t> <o> matches <range>
if|unless stopwatch <id> <range>
```

`items` 的子谓词 `~`（包含匹配）vs `=`（精确匹配）：
```
# 精确匹配：必须有且仅此组件
execute if items entity @s weapon *[enchantments={levels:{unbreaking:1}}]
# 子谓词匹配：只需包含此部分
execute if items entity @s weapon *[enchantments~[{enchantment:"unbreaking"}]]
```

## 存储子命令
```
store (result|success) block <pos> <path> (byte|short|int|long|float|double) <scale>
store (result|success) bossbar <id> (value|max)
store (result|success) entity <target> <path> <type> <scale>
store (result|success) score <targets> <objective>
store (result|success) storage <id> <path> <type> <scale>
```
- `result`：存储命令的返回数值
- `success`：存储命令的成功次数（0 或 1）

## 常见模式
```mcfunction
# 以每个玩家身份在其位置执行
execute as @a at @s run function my:tick

# 条件+位置组合
execute if block ~ ~-1 ~ stone positioned ~ ~1 ~ run setblock ~ ~ ~ air

# 存储玩家数量
execute store result score #count total if entity @a

# 执行者→来源追溯
execute as @e[type=arrow] on origin run say I was shot by this player!

# 获取实体数据到 storage
execute store result storage my:tmp val int 1 run data get entity @s Health
```
