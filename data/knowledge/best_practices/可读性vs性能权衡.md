# 可读性 vs 性能：trade-off 场景集

## 原则：代码首先是给人读的，其次是给机器跑的

### 场景 1：多条 if → 组合谓词
```mcfunction
# ❌ 可读性差，重复 fork
execute if entity @s[tag=fire] run ...
execute if entity @s[scores={x=1..}] run ...
execute if block ~ ~-1 ~ stone run ...

# ✅ 组合成谓词文件，一条命令解决
execute if predicate my:all_checks run ...
```

### 场景 2：NBT 缓存
```mcfunction
# ⚠️ 可读性好但性能差：读 3 次实体 NBT
execute if data entity @s SelectedItem{id:"stone"} run ...
execute if data entity @s SelectedItem{id:"dirt"} run ...
execute if data entity @s SelectedItem{id:"wood"} run ...

# ✅ 性能好但多一行：缓存到 storage
data modify storage t:tmp i set from entity @s SelectedItem
execute if data storage t:tmp i{id:"stone"} run ...
execute if data storage t:tmp i{id:"dirt"} run ...
```
**建议**：超过 3 次判断就做缓存。

### 场景 3：宏 vs 硬编码
```mcfunction
# ❌ 宏：灵活但每 tick 调用时有解析开销
$give @s $(item) 1

# ✅ 硬编码：快但不灵活
give @s diamond 1
```
**建议**：低频事件用宏；高频 tick 函数尽量硬编码。

### 场景 4：return run 提前退出
```mcfunction
# ⚠️ 所有条件都会评估
execute if score @s case matches 1 run say case1
execute if score @s case matches 2 run say case2
execute if score @s case matches 3 run say case3

# ✅ 匹配第一条后立即退出函数
execute if score @s case matches 1 run return run say case1
execute if score @s case matches 2 run return run say case2
execute if score @s case matches 3 run return run say case3
```

### 场景 5：for loop vs 展开
```mcfunction
# ✅ 递归循环——通用但慢
# mypack:loop
execute if score $i tmp matches 1.. run ...
scoreboard players remove $i tmp 1
execute if score $i tmp matches 1.. run function mypack:loop

# ⚠️ 展开——快但不灵活
execute ... run ...
execute ... run ...
execute ... run ...
```
**建议**：10 次以内手动展开；10 次以上用递归。

### 场景 6：事件 vs 轮询
```mcfunction
# ❌ 轮询：每 tick 检查，浪费
execute as @a if items entity @s weapon *[custom_data~{key:true}] run ...

# ✅ 事件：用 advancement 触发，只在发生时运行
```
**建议**：能用进度（advancement）做事件监听的，别用 tick 轮询。
