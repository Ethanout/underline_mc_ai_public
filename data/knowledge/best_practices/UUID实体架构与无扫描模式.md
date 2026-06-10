# UUID 实体架构与无扫描模式

## 世界实体模式（固定 UUID，零扫描）

最极致的实体访问优化：在 `#load` 中用**固定 UUID** 生成实体，此后通过 UUID 直接访问——零 `@e` 扫描。

```mcfunction
# #minecraft:load
summon minecraft:item ~ ~ ~ {
  Item:{id:"minecraft:stone",Count:1b},
  UUID:[I;0,0,0,1],
  Tags:["mypack.world","mypack.persistent"],
  PickupDelay:32767,
  Age:-32768
}

# 直接通过 UUID 访问——零实体迭代
execute as 00000000-0000-0000-0000-000000000001 run function mypack:tick
data get entity 00000000-0000-0000-0000-000000000001
```

### 为什么用 item 实体？
- 有 `Owner`/`Thrower` NBT，支持 `on origin` 追溯
- `PickupDelay:32767` = 永远不会被捡起
- `Age:-32768` = 永远不会消失
- 可存储额外数据

### UUID 辅助
在 NBT 中用 `uuid("hex-string")` 自动转换：
```json
{UUID:uuid("dab4d1cd-223b-41bd-8084-59d890d935e4")}
```

## `on origin` 模式
追溯事件的来源实体：
```mcfunction
# 射出去的箭→追溯到射箭的玩家
execute as @e[type=arrow] on origin run say Shot by this player!

# 物品的 Thrower→追溯到来源
execute as @e[type=item,tag=interact] run data modify storage t:tmp owner set from entity @s Item.tag.Owner
```

## OhMyDat：O(1) 实体私有存储
核心思路：实体 ID → 4位 base-4 数 → 8维数组索引。最大 4^8=65,536 实体。
```
数据访问: arr[-4][-4][-4][-4][-4][-4][-4][-4] = 实体的私有空间
注册:     function #oh_my_dat:please
存取:     data modify storage oh_my_dat: _[-4][-4][...].hp set value 20
```

## entity_score ID 系统（轻量版）
```mcfunction
scoreboard objectives add ID dummy

# 分配唯一 ID
execute as @a unless score @s ID = @s ID store result score @s ID run scoreboard players add #new ID 1

# 通过 ID 链接实体和玩家
scoreboard players operation @e[tag=pet] ID = @p ID
execute as @e[tag=pet] if score @s ID = @p ID run say Found master!
```
