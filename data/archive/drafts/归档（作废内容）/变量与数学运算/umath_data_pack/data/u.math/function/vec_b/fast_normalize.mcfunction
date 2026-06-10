scoreboard players operation vec_b.temp u.variable = vec_b.x u.variable
scoreboard players operation vec_b.temp u.variable *= vec_b.x u.variable
scoreboard players operation #t1 u.variable = vec_b.y u.variable
scoreboard players operation #t1 u.variable *= vec_b.y u.variable
scoreboard players operation #t2 u.variable = vec_b.z u.variable
scoreboard players operation #t2 u.variable *= vec_b.z u.variable
scoreboard players operation vec_b.temp u.variable += #t1 u.variable
scoreboard players operation vec_b.temp u.variable += #t2 u.variable
scoreboard players remove vec_b.temp u.variable 300000000
scoreboard players operation vec_b.temp u.variable /= #-20000 u.constant
scoreboard players operation vec_b.x u.variable *= vec_b.temp u.variable
scoreboard players operation vec_b.y u.variable *= vec_b.temp u.variable
scoreboard players operation vec_b.z u.variable *= vec_b.temp u.variable
scoreboard players operation vec_b.x u.variable /= #10000 u.constant
scoreboard players operation vec_b.y u.variable /= #10000 u.constant
scoreboard players operation vec_b.z u.variable /= #10000 u.constant
