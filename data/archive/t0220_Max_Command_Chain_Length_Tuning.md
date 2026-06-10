---
id: t0220
title: 命令链长度上限调整
title_en: Max Command Chain Length Tuning
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-commands/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["debug", "performance", "safety"]
verified_in_game: false
---

## 核心洞见

通过降低 maxCommandChainLength 可以强制检测并避免意外的无限递归命令链，而不是依赖默认的 65536 上限。

## 代码示例

```mcfunction
gamerule maxCommandChainLength 256
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该规则控制单个游戏刻内函数/命令方块链可执行的最大命令数。降低该值（如 256）可以在开发阶段快速暴露递归或循环调用问题，避免服务器卡死。

## 注意事项

- 常见误解：开发者常认为这个值越大越好，或者默认值足够安全，不会主动调整。
