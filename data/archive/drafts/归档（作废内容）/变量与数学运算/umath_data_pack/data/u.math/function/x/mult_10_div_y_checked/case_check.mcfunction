scoreboard players operation #t1 u.variable = x u.variable
scoreboard players operation #t1 u.variable %= y u.variable
scoreboard players operation #t1 u.variable *= #10 u.constant
scoreboard players operation #t1 u.variable /= y u.variable
scoreboard players operation x u.variable /= y u.variable
execute if score x u.variable matches 214748365.. run return run function u.math:__error__/overflow
execute if score x u.variable matches ..-214748365 run return run function u.math:__error__/overflow
scoreboard players operation x u.variable *= #10 u.constant
execute if score x u.variable matches 0.. if score #t1 u.variable matches 0.. run return run function u.math:x/mult_10_div_y_checked/case_check_0
execute if score #t1 u.variable matches ..0 run return run function u.math:x/mult_10_div_y_checked/case_check_1
scoreboard players operation x u.variable += #t1 u.variable
