execute if score x u.variable matches ..-2 run return run function u.math:__error__/invalid
execute store result score #y u.variable store result score #t2 u.variable run scoreboard players operation #t1 u.variable = x u.variable
function u.math:x/sqrt/process
scoreboard players operation #t2 u.variable /= x u.variable
scoreboard players operation x u.variable += #t2 u.variable
scoreboard players operation x u.variable /= #2 u.constant
scoreboard players operation #y u.variable /= x u.variable
execute if score #y u.variable < x u.variable run scoreboard players remove x u.variable 1
