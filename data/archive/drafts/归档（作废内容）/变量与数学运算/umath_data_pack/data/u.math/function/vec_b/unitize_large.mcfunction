execute store result storage u.math:variable context.pos1[0] double 0.000000003725290298461914 run scoreboard players get vec_b.x u.variable
execute store result storage u.math:variable context.pos1[1] double 0.000000003725290298461914 run scoreboard players get vec_b.y u.variable
execute store result storage u.math:variable context.pos1[2] double 0.000000003725290298461914 run scoreboard players get vec_b.z u.variable
data modify entity 1552e63e-d542-4802-b8cc-92caddbcaab5 Pos set from storage u.math:variable context.pos
execute in overworld positioned 0.0 0.0 0.0 facing entity 1552e63e-d542-4802-b8cc-92caddbcaab5 feet positioned ^ ^ ^1 run tp ~0.000005 ~0.000005 ~0.000005
data modify storage u.math:variable context.pos1 set from entity 1552e63e-d542-4802-b8cc-92caddbcaab5 Pos
execute store result score #t u.variable store result score vec_b.temp u.variable run data get storage u.math:variable context.pos1[0] 10000
execute store result score #t1 u.variable run data get storage u.math:variable context.pos1[1] 10000
execute store result score #t2 u.variable run data get storage u.math:variable context.pos1[2] 10000
execute if score vec_b.temp u.variable matches ..-1 run scoreboard players operation vec_b.temp u.variable *= #-1 u.constant
execute if score #t1 u.variable matches ..-1 run scoreboard players operation vec_b.temp u.variable -= #t1 u.variable
execute if score #t1 u.variable matches 1.. run scoreboard players operation vec_b.temp u.variable += #t1 u.variable
execute if score #t2 u.variable matches ..-1 run scoreboard players operation vec_b.temp u.variable -= #t2 u.variable
execute if score #t2 u.variable matches 1.. run scoreboard players operation vec_b.temp u.variable += #t2 u.variable
scoreboard players operation vec_b.scaler u.variable = vec_b.x u.variable
execute if score vec_b.scaler u.variable matches ..-1 run scoreboard players operation vec_b.scaler u.variable *= #-1 u.constant
execute if score vec_b.y u.variable matches ..-1 run scoreboard players operation vec_b.scaler u.variable -= vec_b.y u.variable
execute if score vec_b.y u.variable matches 1.. run scoreboard players operation vec_b.scaler u.variable += vec_b.y u.variable
execute if score vec_b.z u.variable matches ..-1 run scoreboard players operation vec_b.scaler u.variable -= vec_b.z u.variable
execute if score vec_b.z u.variable matches 1.. run scoreboard players operation vec_b.scaler u.variable += vec_b.z u.variable
scoreboard players operation vec_b.x u.variable = #t u.variable
scoreboard players operation vec_b.y u.variable = #t1 u.variable
scoreboard players operation vec_b.z u.variable = #t2 u.variable
scoreboard players operation vec_b.scaler u.variable *= #10 u.constant
function u.math:vec_b.scaler/__mult_1000_div_small_temp
