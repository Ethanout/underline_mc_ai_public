scoreboard players operation #result u.variable *= #-1 u.constant
execute unless score #remainder u.variable matches 0 run scoreboard players remove #result u.variable 1
scoreboard players operation #remainder u.variable *= #-1 u.constant
scoreboard players operation #remainder u.variable %= z u.variable
