execute if score p.scaler u.variable matches -2147483..2147483 run return run function u.math:p.scaler/__mult_1000_div_small_qtemp/case_0
scoreboard players operation #t1 u.variable = p.scaler u.variable
scoreboard players operation #t1 u.variable %= p.temp u.variable
scoreboard players operation #t1 u.variable *= #1000 u.constant
scoreboard players operation #t1 u.variable /= p.temp u.variable
scoreboard players operation p.scaler u.variable /= p.temp u.variable
scoreboard players operation p.scaler u.variable *= #1000 u.constant
scoreboard players operation p.scaler u.variable += #t1 u.variable
