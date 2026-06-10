execute store result storage u.math:variable context.x double 0.0001 run scoreboard players get q.x u.variable
execute store result storage u.math:variable context.y double 0.0001 run scoreboard players get q.y u.variable
execute store result storage u.math:variable context.z double 0.0001 run scoreboard players get q.z u.variable
execute store result storage u.math:variable context.w double 0.0001 run scoreboard players get q.w u.variable
execute in overworld as 1552e63e-d542-4802-b8cc-92caddbcaab5 run function u.math:q/unitize_large/teleport with storage u.math:variable context
function u.math:q/unitize_large/choose_longest_axis
function u.math:q.scaler/__mult_1000_div_small_qtemp
scoreboard players operation q.temp u.variable = q.scaler u.variable
scoreboard players operation q.scaler u.variable = q.x u.variable
scoreboard players operation q.scaler u.variable *= #10 u.constant
function u.math:q.scaler/__mult_1000_div_small_qtemp
scoreboard players operation q.x u.variable = q.scaler u.variable
scoreboard players operation q.scaler u.variable = q.y u.variable
scoreboard players operation q.scaler u.variable *= #10 u.constant
function u.math:q.scaler/__mult_1000_div_small_qtemp
scoreboard players operation q.y u.variable = q.scaler u.variable
scoreboard players operation q.scaler u.variable = q.z u.variable
scoreboard players operation q.scaler u.variable *= #10 u.constant
function u.math:q.scaler/__mult_1000_div_small_qtemp
scoreboard players operation q.z u.variable = q.scaler u.variable
scoreboard players operation q.scaler u.variable = q.w u.variable
scoreboard players operation q.scaler u.variable *= #10 u.constant
function u.math:q.scaler/__mult_1000_div_small_qtemp
scoreboard players operation q.w u.variable = q.scaler u.variable
scoreboard players operation q.scaler u.variable = q.temp u.variable
