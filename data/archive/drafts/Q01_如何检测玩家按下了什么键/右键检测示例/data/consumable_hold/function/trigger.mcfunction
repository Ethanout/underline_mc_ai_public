advancement revoke @s only consumable_hold:consumed

say 1

#需要在下一tick检测玩家返还的物品
tag @s add sample_consume_temp
schedule function consumable_hold:return 1t