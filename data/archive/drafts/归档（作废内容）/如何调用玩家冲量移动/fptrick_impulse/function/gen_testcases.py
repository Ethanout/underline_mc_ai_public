
def prevent_overflow(n):
    if n < -2147483648:
        return -2147483648
    if n > 2147483647:
        return 2147483647
    return n

def write_test(yrot,xrot,x,y,z,f):
    f.write(f'\n')
    f.write(f'tp @s ~ ~ ~ {yrot} {xrot}\n')
    f.write(f'data modify storage test t set value [0d,0d,0d]\n')
    f.write(f'execute store success score #t test run data modify storage test t set from entity @s Motion\n')
    f.write(f'execute if score #t test matches 1 run return run tellraw @s ["ERROR: MOTION RESET FAILED, TRY AGAIN ",{{nbt:t,storage:test}}]\n')
    f.write(f'function fptrick_impulse:launch_global\n')
    f.write(f'data modify storage test t set from entity @s Motion\n')
    f.write(f'execute store result score #x test run data get storage test t[0] 10000\n')
    f.write(f'execute store result score #y test run data get storage test t[1] 10000\n')
    f.write(f'execute store result score #z test run data get storage test t[2] 10000\n')
    f.write(f'execute unless score #x test matches {prevent_overflow(x-1)}..{prevent_overflow(x+1)} run return run tellraw @s ["TEST FAILED: X ({yrot},{xrot}) ",{{nbt:t,storage:test}}]\n')
    f.write(f'execute unless score #y test matches {prevent_overflow(y-1)}..{prevent_overflow(y+1)} run return run tellraw @s ["TEST FAILED: Y ({yrot},{xrot}) ",{{nbt:t,storage:test}}]\n')
    f.write(f'execute unless score #z test matches {prevent_overflow(z-1)}..{prevent_overflow(z+1)} run return run tellraw @s ["TEST FAILED: Z ({yrot},{xrot}) ",{{nbt:t,storage:test}}]\n')
    f.write(f'tellraw @s ["TEST PASSED: ({yrot},{xrot}) [{x},{y},{z}] ",{{nbt:t,storage:test}}]\n')

y_rotations = [
    "35.264393","54.735607",
    "54.73561","125.26439",
    "125.2644","144.7356",
    "144.73561","-144.73561",
    "-144.7356","-125.2644",
    "-125.26439","-54.73561",
    "-54.735607","-35.264393",
    "-35.26439","35.26439",
]
x_rotations = [
    "-89.99451","-45",
    "-44.999996","44.999996",
    "45","90",
]
mc_303789_xrots = [
    '-90','-89.994514'
]
mc_303789_yrots = [
    '90.00548','90.005486','90.00549','90.0055',
    '-90.00548','-90.005486','-90.00549','-90.0055',
    '45','-45','135','-135','0','180','90','-90',
]
inputs = [
    (20000,30000,40000),
    (-20000,-30000,-40000),
    (0,0,0),
    (2147483647,2147483647,2147483647),
    (-2147483648,-2147483648,-2147483648),
]

count = 0
with open('testcases.mcfunction','w') as f:
    f.write('scoreboard objectives add test dummy\n')
    for inputx,inputy,inputz in inputs:
        f.write(f'scoreboard players set #x fptrick_impulse {inputx}\n')
        f.write(f'scoreboard players set #y fptrick_impulse {inputy}\n')
        f.write(f'scoreboard players set #z fptrick_impulse {inputz}\n')
        for xrot in x_rotations:
            for yrot in y_rotations:
                write_test(yrot,xrot,inputx,inputy,inputz,f)
                count += 1
        for xrot in mc_303789_xrots:
            for yrot in mc_303789_yrots:
                write_test(yrot,xrot,inputx,inputy,inputz,f)
                count += 1
    f.write('\n')
    f.write('scoreboard players set #x fptrick_impulse 0\n')
    f.write('scoreboard players set #y fptrick_impulse 0\n')
    f.write('scoreboard players set #z fptrick_impulse 0\n')
    f.write('tp @s ~ ~ ~ ~ ~\n')
    f.write(f'tellraw @s "ALL {count} TESTS PASSED!"\n')
