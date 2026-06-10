---
id: t0292
title: "字体冷却条UI"
title_en: "custom_ui_font_cooldown"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202512/0/content"
source_type: "feature_article"
source_issue: "202512"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["自定义UI", "字体", "title", "冷却条", "资源包"]
verified_in_game: false
---

## 核心洞见

利用自定义字体和 title actionbar 命令，可以将冷却进度条精确显示在快捷栏物品上方，实现原版不支持的 UI 效果。

## 代码示例

```mcfunction
# 资源包 font/cooldown/mini_bar/common.json 示例（简化）
{
  "providers": [
    {
      "type": "bitmap",
      "file": "cooldown/mini_bar/common.png",
      "ascent": -42,
      "height": 9,
      "chars": ["\u1000\u1001\u1002\u1003\u1004\u1005\u1006\u1007\u1008\u1009\u100a\u100b\u100c\u100d\u100e\u100f\u1010\u1011\u1012\u1013\u1014\u1015\u1016"]
    }
  ]
}

# 玩家 tick 函数中的命令（简化）
title @s actionbar [{"text":"","font":"cooldown/mini_bar/common"},{"storage":"oh_my_dat:","nbt":"_[-4][-4][-4][-4][-4][-4][-4][-4].Message.MainBar[]","interpret":true}]
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术通过资源包中的 `font` 文件定义自定义字符（如 `\u1000` 到 `\u1016`），每个字符对应冷却进度条的一个状态（如 0% 到 100%）。字符的 `char` 属性中的 `height` 和 `ascent` 字段可以控制字符的垂直偏移，例如设置 `ascent` 为 -42 可以使字符显示在快捷栏物品上方。在 tick 函数中，通过计算物品冷却时间与最大冷却时间的百分比，映射到对应的 unicode 字符，然后使用 `title @s actionbar` 命令将包含该字符的文本组件显示在 actionbar 位置。由于 actionbar 默认位于屏幕中央，通过调整字符的偏移和插入空格，可以精确定位到快捷栏、装备栏等位置。多个 UI 元素（如主冷却条、装备冷却条、效果状态）可以拆分为不同的文本组件，分别显示，避免挤压错位。

## 注意事项

- 字符的 `ascent` 偏移值需要根据目标位置精确调整，不同屏幕分辨率下可能显示位置有偏差。
- 多个 UI 元素必须拆分为独立的文本组件，否则空格调整坐标时会导致错位。
- 自定义字体字符的映射需要与资源包中的位图文件严格对应，否则会显示乱码。
- `title` 命令在 actionbar 上的显示有字符数限制，过多的 UI 元素可能导致显示不全。
- 常见误解：开发者通常认为自定义 UI 必须依赖模组或资源包中的复杂着色器，或者只能通过 bossbar 等有限方式实现，无法精确控制位置和样式。
