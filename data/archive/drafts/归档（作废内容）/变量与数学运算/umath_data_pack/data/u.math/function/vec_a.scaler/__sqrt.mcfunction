execute store result score #y u.variable store result score #t2 u.variable run scoreboard players operation #t1 u.variable = vec_a.scaler u.variable
function u.math:vec_a.scaler/__sqrt/process
scoreboard players operation #t2 u.variable /= vec_a.scaler u.variable
scoreboard players operation vec_a.scaler u.variable += #t2 u.variable
scoreboard players operation vec_a.scaler u.variable /= #2 u.constant
scoreboard players operation #y u.variable /= vec_a.scaler u.variable
execute if score #y u.variable < vec_a.scaler u.variable run scoreboard players remove vec_a.scaler u.variable 1
