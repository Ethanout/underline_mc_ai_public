---
id: t0400
title: "多输入编码提交"
title_en: "multi_input_trigger_encoding"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202511/4/content"
source_type: "feature_article"
source_issue: "202511"
version_min: "1.21.6"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["dialog", "trigger", "encoding", "bitwise", "input"]
verified_in_game: false
---

## 核心洞见

通过将多个输入控件的值编码为一个十进制数，可以用单条 /trigger set 命令提交对话框中的所有输入数据。

## 代码示例

```mcfunction
// 对话框定义中的“应用修改”按钮（JSON）
{
  "action": {
    "template": "trigger leap_of_crystal_realm.dialog.settings set $(animation)$(particle)$(sounds)",
    "type": "minecraft:dynamic/run_command"
  },
  "label": {
    "bold": true,
    "color": "black",
    "shadow_color": 0,
    "translate": "dialog.leap_of_crystal_realm.settings.apply"
  }
}

// tick 函数（mcfunction）
execute as @a unless score @s leap_of_crystal_realm.dialog.settings matches -1 run function leap_of_crystal_realm:dialog/settings/trigger

// trigger 处理函数（mcfunction）
#判断输入内容
scoreboard players operation #settings leap_of_crystal_realm.var = @s leap_of_crystal_realm.dialog.settings
scoreboard players set #bit leap_of_crystal_realm.var 0
function leap_of_crystal_realm:dialog/settings/bitwise/main
#重置分数
scoreboard players set @s leap_of_crystal_realm.dialog.settings -1
scoreboard players enable @s leap_of_crystal_realm.dialog.settings
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术的核心是利用十进制数的每一位来编码多个输入控件的值。在 Minecraft 中，/trigger set <value> 的 <value> 是一个整数，可以容纳多位数字。对于每个输入控件，将其可能的值（如 0 或 1）映射到十进制数的某一位上。例如，三个布尔输入（音效、粒子、动画）可以编码为一个三位十进制数：百位表示动画（0或1），十位表示粒子，个位表示音效。这样，玩家点击“应用修改”按钮时，执行命令 `trigger leap_of_crystal_realm.dialog.settings set $(animation)$(particle)$(sounds)`，其中 $(animation)、$(particle)、$(sounds) 是输入控件的值（0或1），拼接后形成一个三位十进制数（如 101 表示动画开、粒子关、音效开）。这个数被写入一个 trigger 记分项。在 tick 函数中，检测该记分项分数不为 -1（初始值）时，调用处理函数。处理函数通过按位操作（或更简单的数学运算）提取每一位的值：例如，用除以 100 取整得到百位，用除以 10 取整再模 10 得到十位，模 10 得到个位。这样，一个整数就携带了所有输入信息。与朴素实现（每个输入一个 trigger 记分项）相比，此方法避免了创建多个 trigger 记分项和复杂的监听逻辑；与将部分数据塞入记分项名称的方法相比，它不需要预创建大量记分项，且能轻松扩展更多输入（只需增加位数）。

## 注意事项

- 初始值不能为 0，因为所有输入都为 0 时分数为 0，需要区分未触发状态，因此使用 -1 作为初始值
- 输入控件的值必须限制为 0-9 的单个数字，否则拼接后的数字位数会混乱
- 当输入控件数量增加时，编码后的数字可能超过 2^31-1（Minecraft 整数上限），需要改用多进制或分块处理
- 常见误解：开发者通常认为每个输入控件都需要独立的 /trigger 记分项，或者需要将部分数据塞入记分项名称中，导致需要预创建大量记分项或无法处理多个输入。
