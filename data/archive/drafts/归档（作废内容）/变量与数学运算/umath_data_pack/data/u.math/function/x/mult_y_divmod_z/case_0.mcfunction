execute store result score #sign0 u.variable store result score #sign1 u.variable run scoreboard players set #sign2 u.variable 1
execute if score x u.variable matches ..-1 run function u.math:x/mult_y_divmod_z/case_0_when_negative_0
execute if score y u.variable matches ..-1 run function u.math:x/mult_y_divmod_z/case_0_when_negative_1
execute if score z u.variable matches ..-1 run function u.math:x/mult_y_divmod_z/case_0_when_negative_2
scoreboard players operation #t1 u.variable = x u.variable
execute store result score #t2 u.variable run scoreboard players operation #t1 u.variable /= z u.variable
execute store result score #t3 u.variable run scoreboard players operation x u.variable %= z u.variable
scoreboard players operation #t4 u.variable = y u.variable
scoreboard players operation #t4 u.variable /= z u.variable
scoreboard players operation y u.variable %= z u.variable
scoreboard players operation #t1 u.variable *= #t4 u.variable
scoreboard players operation #t1 u.variable *= z u.variable
scoreboard players operation #t2 u.variable *= y u.variable
scoreboard players operation x u.variable *= #t4 u.variable
execute store result score #t3 u.variable run scoreboard players operation y u.variable *= #t3 u.variable
scoreboard players operation #t3 u.variable /= z u.variable
scoreboard players operation x u.variable += #t1 u.variable
scoreboard players operation x u.variable += #t2 u.variable
scoreboard players operation x u.variable += #t3 u.variable
scoreboard players operation z u.variable *= #sign2 u.variable
scoreboard players operation y u.variable %= z u.variable
scoreboard players operation #sign0 u.variable *= #sign1 u.variable
execute if score y u.variable matches 0 run return run function u.math:x/mult_y_divmod_z/case_0_zero_remiander
execute if score #sign0 u.variable matches ..-1 run function u.math:x/mult_y_divmod_z/case_1_when_remainder_negative
scoreboard players operation x u.variable *= #sign0 u.variable
scoreboard players operation x u.variable *= #sign2 u.variable
execute if score x u.variable matches ..-1 run scoreboard players remove x u.variable 1
