scoreboard players operation vec_a.scaler u.variable = vec_a.x u.variable
scoreboard players operation vec_a.scaler u.variable *= vec_a.x u.variable
scoreboard players operation #t2 u.variable = vec_a.y u.variable
scoreboard players operation #t2 u.variable *= vec_a.y u.variable
scoreboard players operation #t3 u.variable = vec_a.z u.variable
scoreboard players operation #t3 u.variable *= vec_a.z u.variable
scoreboard players operation vec_a.scaler u.variable += #t2 u.variable
scoreboard players operation vec_a.scaler u.variable += #t3 u.variable
function u.math:vec_a.scaler/__sqrt
scoreboard players operation vec_a.x u.variable *= #10000 u.constant
scoreboard players operation vec_a.y u.variable *= #10000 u.constant
scoreboard players operation vec_a.z u.variable *= #10000 u.constant
scoreboard players operation vec_a.x u.variable /= vec_a.scaler u.variable
scoreboard players operation vec_a.y u.variable /= vec_a.scaler u.variable
scoreboard players operation vec_a.z u.variable /= vec_a.scaler u.variable
