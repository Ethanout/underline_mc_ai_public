execute if score #y u.variable matches 0..19310 run return run function u.math:x/sqrt/process_0
execute if score #y u.variable matches 19311..1705544 run return run function u.math:x/sqrt/process_1
execute if score #y u.variable matches 1705545..39400514 run return run function u.math:x/sqrt/process_2
execute if score #y u.variable matches 39400515..455779650 run return run function u.math:x/sqrt/process_3
scoreboard players operation #t1 u.variable /= #100000 u.constant
scoreboard players add #t1 u.variable 26111
scoreboard players set x u.variable -2147483648
scoreboard players operation x u.variable /= #t1 u.variable
scoreboard players add x u.variable 91181
