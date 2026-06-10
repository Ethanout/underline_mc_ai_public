execute if score vec_a.scaler u.variable matches -2147483..2147483 run return run function u.math:vec_a.scaler/__mult_1000_div_small_temp/case_0
scoreboard players operation #t1 u.variable = vec_a.scaler u.variable
scoreboard players operation #t1 u.variable %= vec_a.temp u.variable
scoreboard players operation #t1 u.variable *= #1000 u.constant
scoreboard players operation #t1 u.variable /= vec_a.temp u.variable
scoreboard players operation vec_a.scaler u.variable /= vec_a.temp u.variable
scoreboard players operation vec_a.scaler u.variable *= #1000 u.constant
scoreboard players operation vec_a.scaler u.variable += #t1 u.variable
