execute if score #y u.variable matches 0..19310 run return run function u.math:q.scaler/__sqrt/process_0
execute if score #y u.variable matches 19311..1705544 run return run function u.math:q.scaler/__sqrt/process_1
execute if score #y u.variable matches 1705545..39400514 run return run function u.math:q.scaler/__sqrt/process_2
execute if score #y u.variable matches 39400515..455779650 run return run function u.math:q.scaler/__sqrt/process_3
scoreboard players operation #t1 u.variable /= #100000 u.constant
scoreboard players add #t1 u.variable 26111
scoreboard players set q.scaler u.variable -2147483648
scoreboard players operation q.scaler u.variable /= #t1 u.variable
scoreboard players add q.scaler u.variable 91181
