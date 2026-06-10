execute store result score #y u.variable store result score #t2 u.variable run scoreboard players operation #t1 u.variable = q.scaler u.variable
function u.math:q.scaler/__sqrt/process
scoreboard players operation #t2 u.variable /= q.scaler u.variable
scoreboard players operation q.scaler u.variable += #t2 u.variable
scoreboard players operation q.scaler u.variable /= #2 u.constant
scoreboard players operation #y u.variable /= q.scaler u.variable
execute if score #y u.variable < q.scaler u.variable run scoreboard players remove q.scaler u.variable 1
