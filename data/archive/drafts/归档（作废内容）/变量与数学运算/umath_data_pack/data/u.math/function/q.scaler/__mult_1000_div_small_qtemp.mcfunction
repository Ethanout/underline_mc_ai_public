execute if score q.scaler u.variable matches -2147483..2147483 run return run function u.math:q.scaler/__mult_1000_div_small_qtemp/case_0
scoreboard players operation #t1 u.variable = q.scaler u.variable
scoreboard players operation #t1 u.variable %= q.temp u.variable
scoreboard players operation #t1 u.variable *= #1000 u.constant
scoreboard players operation #t1 u.variable /= q.temp u.variable
scoreboard players operation q.scaler u.variable /= q.temp u.variable
scoreboard players operation q.scaler u.variable *= #1000 u.constant
scoreboard players operation q.scaler u.variable += #t1 u.variable
