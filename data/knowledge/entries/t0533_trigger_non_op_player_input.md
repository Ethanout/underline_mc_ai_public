---
id: t0533
title: "trigger 接收非 OP 玩家输入"
title_en: "trigger_non_op_player_input"
layer: technique
source_url: "data/archive/inbox/20260606_140955.md"
source_type: manual
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: high
tags: ["trigger", "scoreboard", "player_input", "menu", "non_op"]
verified_in_game: false
---

## 核心洞见

`trigger` criteria 是原版中允许非 OP 玩家主动写入记分板值的安全输入通道，适合菜单、配置和聊天命令入口。

## 代码示例

```mcfunction
# load
scoreboard objectives add menu trigger

# 为玩家开放一次写入权限
scoreboard players enable @a menu

# 玩家执行：/trigger menu set 1
execute as @a[scores={menu=1}] run function mypack:menu/open
scoreboard players set @a[scores={menu=1..}] menu 0
scoreboard players enable @a menu
```

## 机制原理

普通 dummy 记分板只能由管理员命令或数据包修改。trigger objective 在被 `scoreboard players enable` 授权后，允许玩家通过 `/trigger` 修改自己的分数；一次触发后会自动失效，需要再次 enable。

## 注意事项

- 新加入玩家和每次使用后的玩家都需要重新 enable。
- 必须验证输入范围，避免玩家提交未定义值。
- trigger 只适合离散输入，不适合高频按键状态检测。

