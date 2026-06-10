execute if score y u.variable matches -8589935..8589935 run return run function u.math:x/mult_1000_div_y/part_0
execute if score y u.variable matches -40000000..40000000 run return run function u.math:x/mult_1000_div_y/part_1
scoreboard players operation #t1 u.variable /= #1000 u.constant
scoreboard players operation x u.variable /= #t1 u.variable
