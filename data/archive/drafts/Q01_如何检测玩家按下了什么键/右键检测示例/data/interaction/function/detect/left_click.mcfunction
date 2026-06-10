advancement revoke @s only interaction:left_click
say Left_click!
#简单的效果，到这里就可以结束了
#后面是用于定位指定的交互实体

#寻找击打目标
tag @s add click_temp
execute as @e[type=interaction,distance=..20] run function interaction:detect/lc_find
tag @s remove click_temp

