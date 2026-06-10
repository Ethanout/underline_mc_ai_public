scoreboard players operation #t1 u.variable = __error__ u.variable
scoreboard players operation #t1 u.variable %= #2 u.constant
execute if score #t1 u.variable matches 0 run scoreboard players add __error__ u.variable 1
