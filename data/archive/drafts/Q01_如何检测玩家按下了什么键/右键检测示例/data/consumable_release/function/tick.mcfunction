execute as @a if score @s consume_use matches 0 if score @s consume_use_lt matches 1 if items entity @s weapon.* *[custom_data~{sample:1b,sample_type:3}] run function consumable_release:trigger


execute as @a run scoreboard players operation @s consume_use_lt = @s consume_use
execute as @a run scoreboard players set @s consume_use 0