scoreboard players set #t1 u.variable 0
execute store result score #t1 u.variable if score y u.variable matches ..2147483647 unless score y u.variable matches 0
execute if score #t1 u.variable matches 0 run return run function u.math:__error__/division_by_zero
execute if score x u.variable matches -214748364..214748364 run return run function u.math:x/mult_10_div_y/case_0
execute if score y u.variable matches -11..10 run return run function u.math:x/mult_10_div_y_checked/case_check
execute if score y u.variable matches -214748364..214748364 run return run function u.math:x/mult_10_div_y/case_1
execute if score x u.variable matches 0.. run return run function u.math:x/mult_10_div_y/case_2
scoreboard players operation #t2 u.variable = x u.variable
scoreboard players operation #t2 u.variable *= #10 u.constant
scoreboard players operation #t3 u.variable = y u.variable
scoreboard players operation #t1 u.variable = y u.variable
scoreboard players operation #t1 u.variable /= #10 u.constant
scoreboard players operation x u.variable /= #t1 u.variable
scoreboard players operation #t3 u.variable *= x u.variable
scoreboard players operation #t2 u.variable -= #t3 u.variable
execute if score y u.variable matches 0.. run return run execute if score #t2 u.variable >= y u.variable run scoreboard players add x u.variable 1
execute if score #t2 u.variable <= y u.variable run scoreboard players add x u.variable 1
