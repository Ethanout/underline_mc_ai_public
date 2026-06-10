execute store result storage u.math:variable context.x double 0.0001 run scoreboard players get p.x u.variable
execute store result storage u.math:variable context.y double 0.0001 run scoreboard players get p.y u.variable
execute store result storage u.math:variable context.z double 0.0001 run scoreboard players get p.z u.variable
execute store result storage u.math:variable context.w double 0.0001 run scoreboard players get p.w u.variable
execute in overworld as 1552e63e-d542-4802-b8cc-92caddbcaab5 run function u.math:p/unitize_large/teleport with storage u.math:variable context
function u.math:p/unitize_large/choose_longest_axis
function u.math:p.scaler/__mult_1000_div_small_qtemp
scoreboard players operation p.temp u.variable = p.scaler u.variable
scoreboard players operation p.scaler u.variable = p.x u.variable
scoreboard players operation p.scaler u.variable *= #10 u.constant
function u.math:p.scaler/__mult_1000_div_small_qtemp
scoreboard players operation p.x u.variable = p.scaler u.variable
scoreboard players operation p.scaler u.variable = p.y u.variable
scoreboard players operation p.scaler u.variable *= #10 u.constant
function u.math:p.scaler/__mult_1000_div_small_qtemp
scoreboard players operation p.y u.variable = p.scaler u.variable
scoreboard players operation p.scaler u.variable = p.z u.variable
scoreboard players operation p.scaler u.variable *= #10 u.constant
function u.math:p.scaler/__mult_1000_div_small_qtemp
scoreboard players operation p.z u.variable = p.scaler u.variable
scoreboard players operation p.scaler u.variable = p.w u.variable
scoreboard players operation p.scaler u.variable *= #10 u.constant
function u.math:p.scaler/__mult_1000_div_small_qtemp
scoreboard players operation p.w u.variable = p.scaler u.variable
scoreboard players operation p.scaler u.variable = p.temp u.variable
