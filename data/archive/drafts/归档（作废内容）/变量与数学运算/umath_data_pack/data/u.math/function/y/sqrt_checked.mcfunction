execute if score y u.variable matches ..-2 run return run function u.math:__error__/invalid
execute store result score #y u.variable store result score #t2 u.variable run scoreboard players operation #t1 u.variable = y u.variable
function u.math:y/sqrt/process
scoreboard players operation #t2 u.variable /= y u.variable
scoreboard players operation y u.variable += #t2 u.variable
scoreboard players operation y u.variable /= #2 u.constant
scoreboard players operation #y u.variable /= y u.variable
execute if score #y u.variable < y u.variable run scoreboard players remove y u.variable 1
