---
id: t0389
title: "字体图标资源包"
title_en: "font_icon_resource_pack"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202506/1/content"
source_type: "feature_article"
source_issue: "202506"
version_min: "1.16"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["字体", "资源包", "图标", "Unicode私用区", "bitmap字体"]
verified_in_game: false
---

## 核心洞见

利用 Minecraft 字体系统将 Unicode 私用区字符映射为像素图标，可在任何文本组件中嵌入图标。

## 代码示例

```mcfunction
{
"providers": [
{
"type": "space",
"advances": {
" ": 4
}
},
{
"type": "bitmap",
"file": "minecraft:font/test.png",
"height": 8,
"ascent": 7,
"chars": [
"\ue000\ue001\ue002\ue003\ue004\ue005\ue006\ue007\ue008\ue009\ue00a\ue00b\ue00c\ue00d\ue00e\ue00f",
"\ue010\ue011\ue012\ue013\ue014\ue015\ue016\ue017\ue018\ue019\ue01a\ue01b\ue01c\ue01d\ue01e\ue01f",
"\ue020\ue021\ue022\ue023\ue024\ue025\ue026\ue027\ue028\ue029\ue02a\ue02b\ue02c\ue02d\ue02e\ue02f",
"\ue030\ue031\ue032\ue033\ue034\ue035\ue036\ue037\ue038\ue039\ue03a\ue03b\ue03c\ue03d\ue03e\ue03f",
"\ue040\ue041\ue042\ue043\ue044\ue045\ue046\ue047\ue048\ue049\ue04a\ue04b\ue04c\ue04d\ue04e\ue04f",
"\ue050\ue051\ue052\ue053\ue054\ue055\ue056\ue057\ue058\ue059\ue05a\ue05b\ue05c\ue05d\ue05e\ue05f",
"\ue060\ue061\ue062\ue063\ue064\ue065\ue066\ue067\ue068\ue069\ue06a\ue06b\ue06c\ue06d\ue06e\ue06f",
"\ue070\ue071\ue072\ue073\ue074\ue075\ue076\ue077\ue078\ue079\ue07a\ue07b\ue07c\ue07d\ue07e\ue07f",
"\ue080\ue081\ue082\ue083\ue084\ue085\ue086\ue087\ue088\ue089\ue08a\ue08b\ue08c\ue08d\ue08e\ue08f",
"\ue090\ue091\ue092\ue093\ue094\ue095\ue096\ue097\ue098\ue099\ue09a\ue09b\ue09c\ue09d\ue09e\ue09f",
"\ue0a0\ue0a1\ue0a2\ue0a3\ue0a4\ue0a5\ue0a6\ue0a7\ue0a8\ue0a9\ue0aa\ue0ab\ue0ac\ue0ad\ue0ae\ue0af",
"\ue0b0\ue0b1\ue0b2\ue0b3\ue0b4\ue0b5\ue0b6\ue0b7\ue0b8\ue0b9\ue0ba\ue0bb\ue0bc\ue0bd\ue0be\ue0bf",
"\ue0c0\ue0c1\ue0c2\ue0c3\ue0c4\ue0c5\ue0c6\ue0c7\ue0c8\ue0c9\ue0ca\ue0cb\ue0cc\ue0cd\ue0ce\ue0cf",
"\ue0d0\ue0d1\ue0d2\ue0d3\ue0d4\ue0d5\ue0d6\ue0d7\ue0d8\ue0d9\ue0da\ue0db\ue0dc\ue0dd\ue0de\ue0df",
"\ue0e0\ue0e1\ue0e2\ue0e3\ue0e4\ue0e5\ue0e6\ue0e7\ue0e8\ue0e9\ue0ea\ue0eb\ue0ec\ue0ed\ue0ee\ue0ef",
"\ue0f0\ue0f1\ue0f2\ue0f3\ue0f4\ue0f5\ue0f6\ue0f7\ue0f8\ue0f9\ue0fa\ue0fb\ue0fc\ue0fd\ue0fe\ue0ff"
]
}
]
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Minecraft 从 1.16 快照 20w17a 开始支持在文本组件中指定字体。字体定义 JSON 的 bitmap provider 可以将一张图片中的像素区域映射到特定字符上。通过使用 Unicode 基本多文种平面私用区（U+E000 至 U+F8FF）的字符，可以安全地替换不会在正常文本中出现的码位。每个字符对应图片中的一个 16×16 像素区域（按 chars 数组的行列顺序排列）。当文本渲染时，Minecraft 会查找该字符对应的字体定义，用图片中的像素替代字符渲染。这样，图标就可以像普通字符一样插入到任何支持文本组件的地方（如物品名称、告示牌、聊天消息等）。与朴素实现（如使用物品模型或自定义实体）相比，这种方法无需额外实体或模型，且可以自由调整颜色（通过文本颜色标签），但图标本身必须是单色（由字体图片的像素颜色决定）。

## 注意事项

- 使用 Unicode 扩展平面私用区（U+E0000 以上）时，Minecraft 不支持 \u{} 转义，需要转换为两个码元，增加复杂度
- 图标在汉字和西文中的基线对齐可能不同，需要测试调整 ascent 值
- 讲述人功能会读出被替换的字符，可能造成无障碍体验问题
- 字体图片中每个图标的大小必须与 chars 数组中的行列数匹配，否则渲染会错位
- 常见误解：开发者可能认为图标只能通过物品模型或自定义实体实现，而不知道可以通过字体 bitmap 映射将图标嵌入文本。
