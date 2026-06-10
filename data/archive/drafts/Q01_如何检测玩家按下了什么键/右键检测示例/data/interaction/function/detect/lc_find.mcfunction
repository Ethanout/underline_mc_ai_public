#寻找指定的实体
data modify storage sample lc.uuid set from entity @a[limit=1,tag=click_temp] UUID

execute store result score @s sample_interaction run data modify storage sample lc.uuid set from entity @s attack.player

execute if score @s sample_interaction matches 0 run tag @s add lc_hit

execute if entity @s[tag=lc_hit] run data modify entity @s attack.player set value [I;0,0,0,0]

#以交互实体为执行者执行指令，如say
execute if entity @s[tag=lc_hit] run say 1


tag @s remove lc_hit