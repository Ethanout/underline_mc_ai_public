execute store result score q.temp u.variable run data get storage u.math:variable context.pos1[0] 100000
execute if score q.temp u.variable matches 57735.. store result score q.scaler u.variable run return run data get storage u.math:variable context.pos[0] 1000000
execute if score q.temp u.variable matches ..-57735 store result score q.scaler u.variable run return run data get storage u.math:variable context.pos[0] 1000000
execute store result score q.temp u.variable run data get storage u.math:variable context.pos1[1] 100000
execute if score q.temp u.variable matches 57735.. store result score q.scaler u.variable run return run data get storage u.math:variable context.pos[1] 1000000
execute if score q.temp u.variable matches ..-57735 store result score q.scaler u.variable run return run data get storage u.math:variable context.pos[1] 1000000
execute store result score q.temp u.variable run data get storage u.math:variable context.pos1[2] 100000
execute store result score q.scaler u.variable run return run data get storage u.math:variable context.pos[2] 1000000
