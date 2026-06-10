execute if score z u.variable matches ..-2 run return run function u.math:__error__/invalid
execute store result score #y u.variable store result score #t2 u.variable run scoreboard players operation #t1 u.variable = z u.variable
function u.math:z/sqrt/process
scoreboard players operation #t2 u.variable /= z u.variable
scoreboard players operation z u.variable += #t2 u.variable
scoreboard players operation z u.variable /= #2 u.constant
scoreboard players operation #y u.variable /= z u.variable
execute if score #y u.variable < z u.variable run scoreboard players remove z u.variable 1
