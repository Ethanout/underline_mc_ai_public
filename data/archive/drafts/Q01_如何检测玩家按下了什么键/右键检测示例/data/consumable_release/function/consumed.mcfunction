advancement revoke @s only consumable_release:consumed

say 你居然按完了……

#需要在下一tick检测玩家返还的物品
tag @s add sample_consume_temp
schedule function consumable_release:return 1t