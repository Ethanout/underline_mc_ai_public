scoreboard players remove #t1 u.variable 8
tellraw @a {"storage": "u.math:constant", "nbt": "__error__[{value:8}].text", "interpret": true, "color": "red"}
