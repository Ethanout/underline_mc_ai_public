---
id: t0474
title: "自定义标签检测物品"
title_en: "detect_item_with_custom_tag"
layer: technique
source_url: "https://minecraftcommands.github.io/wiki/questions/detectitem"
source_type: "mcc_wiki"
source_issue: "questions/detectitem"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["item detection", "custom tag", "NBT", "data pack"]
verified_in_game: false
---

## 核心洞见

通过给物品附加自定义 NBT 标签（如 awesome_stick:true）来唯一标识物品，比检测物品名称更可靠、更简洁。

## 代码示例

```mcfunction
# 1.13 - 1.20.4
give @s minecraft:stick{awesome_stick:true,display:{Name:'{"text":"Awesome Stick"}'}}

# 1.20.5+
give @s minecraft:stick[minecraft:custom_data={awesome_stick:true},minecraft:custom_name='"Awesome Stick"']

# 检测示例（1.20.5+ execute if items）
execute as @a if items entity @s container.* minecraft:stick[minecraft:custom_data~{awesome_stick:true}]

# 检测示例（1.20.4 及以下，目标选择器）
@a[nbt={Inventory:[{id:"minecraft:stick",tag:{awesome_stick:true}}]}]
```

## 文件结构

（待补充）

## 用法

构建完数据包即可在游戏内测试效果，无需额外调用。

## 使用场景

['需要唯一标识自定义物品（如任务道具、特殊武器），防止玩家通过铁砧重命名伪造。', '在命令或数据包中快速检测玩家是否持有特定物品，而不依赖易变的物品名称或 ID。']

## 机制原理

Minecraft 物品数据支持自定义 NBT 标签（如 `awesome_stick:true`），这些标签不会在游戏内自然生成，只能通过命令或数据包赋予。检测时只需检查该标签是否存在，无需解析复杂的 JSON 文本名称，避免了因语言、格式化差异导致的误判。在 1.20.5+ 中，自定义数据存储在 `minecraft:custom_data` 组件中，支持子谓词匹配（`~`），可灵活检测部分匹配。

## 注意事项

- 始终使用自定义标签而非物品名称进行检测，因为名称检测需要处理 JSON 文本格式，且不同版本格式不同（如 1.20.2 后 JSON 文本自动简化为纯文本）。
- 在 1.20.5+ 中，使用 `execute if items` 时推荐用子谓词匹配（`~`）而非精确匹配（`=`），以避免因其他组件差异导致检测失败。
- 在谓词中检测主手物品时，若未检测物品 ID，需同时检测物品数量（count），以规避 MC-229882 漏洞。
