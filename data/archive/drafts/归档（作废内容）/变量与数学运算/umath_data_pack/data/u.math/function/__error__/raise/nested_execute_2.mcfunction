scoreboard players remove #t1 u.variable 4
tellraw @a {"storage": "u.math:constant", "nbt": "__error__[{value:4}].text", "interpret": true, "color": "red"}
