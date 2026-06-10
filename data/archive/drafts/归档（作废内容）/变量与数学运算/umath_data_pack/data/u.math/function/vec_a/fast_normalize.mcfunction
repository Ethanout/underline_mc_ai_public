scoreboard players operation vec_a.temp u.variable = vec_a.x u.variable
scoreboard players operation vec_a.temp u.variable *= vec_a.x u.variable
scoreboard players operation #t1 u.variable = vec_a.y u.variable
scoreboard players operation #t1 u.variable *= vec_a.y u.variable
scoreboard players operation #t2 u.variable = vec_a.z u.variable
scoreboard players operation #t2 u.variable *= vec_a.z u.variable
scoreboard players operation vec_a.temp u.variable += #t1 u.variable
scoreboard players operation vec_a.temp u.variable += #t2 u.variable
scoreboard players remove vec_a.temp u.variable 300000000
scoreboard players operation vec_a.temp u.variable /= #-20000 u.constant
scoreboard players operation vec_a.x u.variable *= vec_a.temp u.variable
scoreboard players operation vec_a.y u.variable *= vec_a.temp u.variable
scoreboard players operation vec_a.z u.variable *= vec_a.temp u.variable
scoreboard players operation vec_a.x u.variable /= #10000 u.constant
scoreboard players operation vec_a.y u.variable /= #10000 u.constant
scoreboard players operation vec_a.z u.variable /= #10000 u.constant
