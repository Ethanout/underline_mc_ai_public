execute if score x u.variable matches -2147483..2147483 run return run function u.math:x/mult_1000_div_y/case_0
execute if score y u.variable matches -2147483..2147483 run return run function u.math:x/mult_1000_div_y/case_1
execute store result score #t5 u.variable store result score #t4 u.variable run scoreboard players operation #t2 u.variable = x u.variable
execute store result score #t1 u.variable run scoreboard players operation #t3 u.variable = y u.variable
scoreboard players operation #t2 u.variable *= #1000 u.constant
function u.math:x/mult_1000_div_y/part
execute if score #t4 u.variable matches 0.. run return run function u.math:x/mult_1000_div_y/case_correct_result
scoreboard players operation #t3 u.variable *= x u.variable
scoreboard players operation #t2 u.variable -= #t3 u.variable
execute if score y u.variable matches 0.. run return run execute if score #t2 u.variable >= y u.variable run scoreboard players add x u.variable 1
execute if score #t2 u.variable <= y u.variable run scoreboard players add x u.variable 1
