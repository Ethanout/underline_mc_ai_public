# AI 微调

## 基础属性修改
```mcfunction
# 生成时指定 AI
summon minecraft:zombie ~ ~ ~ {
  NoAI:true,                            # 完全无 AI
  PersistenceRequired:true,             # 不消失
  CanPickUpLoot:false,
  CanBreakDoors:false
}

# 运行时修改属性
attribute @s generic.movement_speed base set 0.5
attribute @s generic.max_health base set 200.0
attribute @s generic.attack_damage base set 10.0
attribute @s generic.follow_range base set 64.0
attribute @s generic.armor base set 20.0
attribute @s generic.armor_toughness base set 8.0
attribute @s generic.knockback_resistance base set 1.0

# 攻击目标属性
execute as @e[type=zombie] run data modify entity @s target set from entity @p UUID
```

## 特殊行为修改
```mcfunction
# 僵尸改为中立/被动
summon minecraft:zombie ~ ~ ~ {IsBaby:1b,HandItems:[{},{id:"poppy",count:1}]}

# 苦力怕闪电激活
data modify entity @s powered set value 1b

# 村民职业
summon minecraft:villager ~ ~ ~ {VillagerData:{level:99,profession:"minecraft:armorer",type:"minecraft:plains"}}

# 蜘蛛状态效果
data modify entity @s ActiveEffects append value {Id:14b,Amplifier:1b,Duration:1000000,ShowParticles:0b}
```

## 铁傀儡修改
```mcfunction
# 玩家召唤的铁傀儡（中立）
summon minecraft:iron_golem ~ ~ ~ {
  PlayerCreated:1b,
  Tags:["player_golem"]
}
```

## 鱼桶实体（1.20.5+）
```mcfunction
summon minecraft:cod ~ ~ ~ {
  FromBucket:1b
}
```
备注：1.20.5+ 起，从桶里放出的鱼不再使用 `BucketVariantTag`，其属性由物品组件直接决定。

## 消除狼的主动攻击行为

狼会主动攻击骷髅或玩家攻击的生物。通过修改 `follow_range` 消除敌意：

```mcfunction
# 高频执行（作用于目标狼）
execute if data entity @s AngryAt run attribute @s generic.follow_range modifier add anger -1 add_multiplied_total
execute unless data entity @s AngryAt run attribute @s generic.follow_range modifier remove anger
```

原理：`AngryAt` 存在时临时缩小追踪范围到负值，使狼无法锁定目标；愤怒解除后恢复。
