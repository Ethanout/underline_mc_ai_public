# u.math

## Basic Calculations

Fast mult div mod:
```mcfunction
#> 
#   Calculate x, y = x * y // z, x * y % z.
#
# @inputs
#   x = score(x, u.variable)
#   y = score(y, u.variable)
#   z = score(z, u.variable)
#
#   x, y, z >= 0
#   z <= 46341
#
# @outputs
#   score(x, u.variable)
#   score(y, u.variable)


scoreboard players set x u.variable 1234567
scoreboard players set y u.variable 7654321
scoreboard players set z u.variable 40000
function u.math:x/fast_mult_y_divmod_z

# x = 1234567 * 7654321 // 40000 = 236244302
# y = 1234567 * 7654321 % 40000 = 34007
scoreboard players get x u.variable
scoreboard players get y u.variable
```

Mult div mod:
```mcfunction
#> 
#   Calculate x, y = x * y // z, x * y % z.
#   It may have a bad performance if abs(z) >= 46342, the worst case costs about 270 scoreboards.
#
# @inputs
#   x = score(x, u.variable)
#   y = score(y, u.variable)
#   z = score(z, u.variable)
#
#   x, y, z >= -2147483647
#   if abs(z) >= 46342:
#       2*(abs(z)-1) + abs(x) <= 2174783647
#
# @outputs
#   score(x, u.variable)
#   score(y, u.variable)

# x = 1234567 * -7654321 // 100000 = -94497722
# y = 1234567 * -7654321 % 100000 = 85993
scoreboard players set x u.variable 1234567
scoreboard players set y u.variable -7654321
scoreboard players set z u.variable 100000
function u.math:x/mult_y_divmod_z
scoreboard players get x u.variable
scoreboard players get y u.variable
```

Scaled div mod:
```mcfunction
#> 
#   Calculate x = x // y, scaled by 10, 100 or 1000.
#
# @inputs
#   x = score(x, u.variable)
#   y = score(y, u.variable)
#   z = score(z, u.variable)
#
# @outputs
#   score(x, u.variable)

# x = 212345678 * 10 // 474747 = 4472
scoreboard players set x u.variable 212345678
scoreboard players set y u.variable 474747
function u.math:x/mult_10_divmod_y
scoreboard players get x u.variable

# x = 212345678 * 100 // 474747 = 44728
scoreboard players set x u.variable 212345678
scoreboard players set y u.variable 474747
function u.math:x/mult_100_divmod_y
scoreboard players get x u.variable

# x = 212345678 * 1000 // 474747 = 447281
scoreboard players set x u.variable 212345678
scoreboard players set y u.variable 474747
function u.math:x/mult_1000_divmod_y
scoreboard players get x u.variable
```

Square root:
```mcfunction
#> 
#   Calculate the floor of the arithmetic square root of x
#
# @inputs
#   x = score(x, u.variable)
#
#   x >= 0
#
# @outputs
#   score(x, u.variable)

# x = √12345678 = 3513
scoreboard players set x u.variable 12345678
function u.math:x/sqrt
scoreboard players get x u.variable
```

## Quarternions

Set values:
```mcfunction
#> 
#   Set x, y, z, w of the quaternion
# @outputs
#   score(quat.x, u.variable)
#   score(quat.y, u.variable)
#   score(quat.z, u.variable)
#   score(quat.w, u.variable)

# quat.x = quat.y = quat.z = quat.w = 0
function u.math:quat/zero
scoreboard players get quat.x u.variable
scoreboard players get quat.y u.variable
scoreboard players get quat.z u.variable
scoreboard players get quat.w u.variable

# quat.x = quat.y = quat.z = quat.w = 1
function u.math:quat/one
scoreboard players get quat.x u.variable
scoreboard players get quat.y u.variable
scoreboard players get quat.z u.variable
scoreboard players get quat.w u.variable

# quat.x = quat.y = quat.z = 0, quat.w = 1
function u.math:quat/default
scoreboard players get quat.x u.variable
scoreboard players get quat.y u.variable
scoreboard players get quat.z u.variable
scoreboard players get quat.w u.variable
```

## WIP...