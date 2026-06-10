execute store result storage u.math:variable context.pos1[0] double 0.000000003725290298461914 run scoreboard players get vec_a.x u.variable
execute store result storage u.math:variable context.pos1[1] double 0.000000003725290298461914 run scoreboard players get vec_a.y u.variable
execute store result storage u.math:variable context.pos1[2] double 0.000000003725290298461914 run scoreboard players get vec_a.z u.variable
data modify entity 1552e63e-d542-4802-b8cc-92caddbcaab5 Pos set from storage u.math:variable context.pos
execute in overworld positioned 0.0 0.0 0.0 facing entity 1552e63e-d542-4802-b8cc-92caddbcaab5 feet positioned ^ ^ ^1 run tp ~0.000005 ~0.000005 ~0.000005
data modify storage u.math:variable context.pos1 set from entity 1552e63e-d542-4802-b8cc-92caddbcaab5 Pos
execute store result score vec_a.x u.variable run data get storage u.math:variable context.pos1[0] 10000
execute store result score vec_a.y u.variable run data get storage u.math:variable context.pos1[1] 10000
execute store result score vec_a.z u.variable run data get storage u.math:variable context.pos1[2] 10000
