---
id: t0457
title: "反转命令方块成功"
title_en: "invert_command_block_success"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/blockinvert"
source_type: "mcc_wiki"
source_issue: "questions/blockinvert"
version_min: "1.8"
version_max: "1.20.4"
wiki_covers_this: false
confidence: medium
tags: ["command_block", "success_count", "conditional", "redstone_alternative"]
verified_in_game: false
---

## 核心洞见

通过检测命令方块的 SuccessCount 标签是否为 0，可以在命令方块失败时触发后续命令，实现逻辑反转。

## 代码示例

```mcfunction
# pre 1.13
testfor @a[r=5]
testforblock ~ ~ ~1 command_block * {SuccessCount:0}
say Nobody is within 5 blocks!

# 1.13+
<any command>
execute if block ~ ~ ~1 command_block{SuccessCount:0}
say Command didn't succed
```

## 文件结构

（待补充）

## 用法

在命令方块链中放置：第一个命令方块执行要检测的命令（如 testfor 或任意命令），第二个命令方块（位于第一个的相邻位置）使用 testforblock（1.13 前）或 execute if block（1.13+）检测第一个命令方块的 SuccessCount 是否为 0。第二个命令方块设置为条件制约（conditional），其后的命令在第一个失败时执行。

## 使用场景

['当需要根据命令是否失败来执行不同逻辑时，例如检测玩家是否在范围内，若不在则执行提示或替代操作。', '在命令方块链中实现条件分支，无需红石比较器或红石火把，减少延迟和复杂度。', '替代红石比较器+红石火炮的反向逻辑，避免红石更新带来的性能开销。']

## 机制原理

命令方块执行后，其 SuccessCount 标签会更新为成功执行的次数（通常为 0 或 1）。比较器读取该值输出红石信号强度。通过另一个命令方块使用 testforblock（1.13 前）或 execute if block（1.13+）检测该标签是否为 0，即可在第一个命令失败时触发后续命令。这利用了命令方块自身的 NBT 数据作为状态标志，避免了红石元件的使用。

## 注意事项

- 此方法仅适用于命令方块，不适用于函数（函数中应使用 execute unless 等条件）。
- 1.13+ 中推荐直接使用 execute unless 替代此模式，更简洁高效。
- 使用红石比较器+红石火炮反转信号的方法不推荐，因为红石更新频率低于命令方块执行频率，可能导致延迟或性能问题。
- 第二个命令方块的位置和类型必须与第一个匹配（如 chain_command_block），否则检测会失败。
