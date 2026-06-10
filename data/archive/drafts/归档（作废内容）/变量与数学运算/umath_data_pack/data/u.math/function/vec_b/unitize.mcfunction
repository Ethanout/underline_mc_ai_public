scoreboard players operation vec_b.scaler u.variable = vec_b.x u.variable
scoreboard players operation vec_b.scaler u.variable *= vec_b.x u.variable
scoreboard players operation #t2 u.variable = vec_b.y u.variable
scoreboard players operation #t2 u.variable *= vec_b.y u.variable
scoreboard players operation #t3 u.variable = vec_b.z u.variable
scoreboard players operation #t3 u.variable *= vec_b.z u.variable
scoreboard players operation vec_b.scaler u.variable += #t2 u.variable
scoreboard players operation vec_b.scaler u.variable += #t3 u.variable
function u.math:vec_b.scaler/__sqrt
scoreboard players operation vec_b.x u.variable *= #10000 u.constant
scoreboard players operation vec_b.y u.variable *= #10000 u.constant
scoreboard players operation vec_b.z u.variable *= #10000 u.constant
scoreboard players operation vec_b.x u.variable /= vec_b.scaler u.variable
scoreboard players operation vec_b.y u.variable /= vec_b.scaler u.variable
scoreboard players operation vec_b.z u.variable /= vec_b.scaler u.variable
