scoreboard players operation #x_scale3 fptrick_impulse = #x fptrick_impulse
execute if score #x fptrick_impulse matches 1.. run scoreboard players operation #x_scale3 fptrick_impulse *= #-1 fptrick_impulse
execute store result score #x_scale2 fptrick_impulse store result score #x_scale1 fptrick_impulse run scoreboard players operation #x_scale0 fptrick_impulse = #x_scale3 fptrick_impulse
scoreboard players operation #x_scale3 fptrick_impulse /= #-16777216 fptrick_impulse
scoreboard players operation #x_scale2 fptrick_impulse /= #-65536 fptrick_impulse
scoreboard players operation #x_scale2 fptrick_impulse %= #256 fptrick_impulse
scoreboard players operation #x_scale1 fptrick_impulse /= #-256 fptrick_impulse
scoreboard players operation #x_scale1 fptrick_impulse %= #256 fptrick_impulse
scoreboard players operation #x_scale0 fptrick_impulse %= #-256 fptrick_impulse

scoreboard players operation #y_scale3 fptrick_impulse = #y fptrick_impulse
execute if score #y fptrick_impulse matches 1.. run scoreboard players operation #y_scale3 fptrick_impulse *= #-1 fptrick_impulse
execute store result score #y_scale2 fptrick_impulse store result score #y_scale1 fptrick_impulse run scoreboard players operation #y_scale0 fptrick_impulse = #y_scale3 fptrick_impulse
scoreboard players operation #y_scale3 fptrick_impulse /= #-16777216 fptrick_impulse
scoreboard players operation #y_scale2 fptrick_impulse /= #-65536 fptrick_impulse
scoreboard players operation #y_scale2 fptrick_impulse %= #256 fptrick_impulse
scoreboard players operation #y_scale1 fptrick_impulse /= #-256 fptrick_impulse
scoreboard players operation #y_scale1 fptrick_impulse %= #256 fptrick_impulse
scoreboard players operation #y_scale0 fptrick_impulse %= #-256 fptrick_impulse

scoreboard players operation #z_scale3 fptrick_impulse = #z fptrick_impulse
execute if score #z fptrick_impulse matches 1.. run scoreboard players operation #z_scale3 fptrick_impulse *= #-1 fptrick_impulse
execute store result score #z_scale2 fptrick_impulse store result score #z_scale1 fptrick_impulse run scoreboard players operation #z_scale0 fptrick_impulse = #z_scale3 fptrick_impulse
scoreboard players operation #z_scale3 fptrick_impulse /= #-16777216 fptrick_impulse
scoreboard players operation #z_scale2 fptrick_impulse /= #-65536 fptrick_impulse
scoreboard players operation #z_scale2 fptrick_impulse %= #256 fptrick_impulse
scoreboard players operation #z_scale1 fptrick_impulse /= #-256 fptrick_impulse
scoreboard players operation #z_scale1 fptrick_impulse %= #256 fptrick_impulse
scoreboard players operation #z_scale0 fptrick_impulse %= #-256 fptrick_impulse

# tellraw @s ["x_scale:[",{score:{name:"#x_scale3",objective:fptrick_impulse}},",",{score:{name:"#x_scale2",objective:fptrick_impulse}},",",{score:{name:"#x_scale1",objective:fptrick_impulse}},",",{score:{name:"#x_scale0",objective:fptrick_impulse}},"]"]
# tellraw @s ["y_scale:[",{score:{name:"#y_scale3",objective:fptrick_impulse}},",",{score:{name:"#y_scale2",objective:fptrick_impulse}},",",{score:{name:"#y_scale1",objective:fptrick_impulse}},",",{score:{name:"#y_scale0",objective:fptrick_impulse}},"]"]
# tellraw @s ["z_scale:[",{score:{name:"#z_scale3",objective:fptrick_impulse}},",",{score:{name:"#z_scale2",objective:fptrick_impulse}},",",{score:{name:"#z_scale1",objective:fptrick_impulse}},",",{score:{name:"#z_scale0",objective:fptrick_impulse}},"]"]
# tellraw @s ["before:",{nbt:Motion,entity:"@s"}]

execute store success score #left_x_sign fptrick_impulse if entity @s[y_rotation=-54.735607..54.735607]
execute if entity @s[y_rotation=125.2644..-125.2644] run scoreboard players set #left_x_sign fptrick_impulse -1
execute store success score #left_z_sign fptrick_impulse if entity @s[y_rotation=35.264393..144.7356]
execute if entity @s[y_rotation=-144.7356..-35.264393] run scoreboard players set #left_z_sign fptrick_impulse -1

execute if entity @s[x_rotation=-90..-89.994514] run loot replace entity @s saddle loot fptrick_impulse:mc-303789
execute if entity @s[x_rotation=-89.99451..-45] run loot replace entity @s saddle loot fptrick_impulse:xrot_-89_-45
execute if entity @s[x_rotation=-44.999996..44.999996] run loot replace entity @s saddle loot fptrick_impulse:xrot_-44_44
execute if entity @s[x_rotation=45..90] run loot replace entity @s saddle loot fptrick_impulse:xrot_45_90


# tellraw @s ["after:",{nbt:Motion,entity:"@s"}]

