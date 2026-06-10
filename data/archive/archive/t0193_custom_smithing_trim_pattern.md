---
id: t0193
title: "自定义锻造纹饰"
title_en: "custom_smithing_trim_pattern"
layer: technique
source_url: "https://datapack.wiki/guide/adding-new-features/smithing-trims"
source_type: "datapack_wiki"
source_issue: ""
version_min: "1.20"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["datapack", "resourcepack", "smithing_trim", "custom_content"]
verified_in_game: false
---

## 核心洞见

通过数据包和资源包组合，可以添加完全自定义的锻造纹饰图案和颜色，无需模组。

## 代码示例

```mcfunction
{
  "asset_id": "<namespace>:example_template",
  "description": "Example Trim",
  "decal": false
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用Minecraft的`trim_pattern`和`trim_material`数据包文件，结合资源包中的`armor_trims.json`图集和纹理文件，实现自定义纹饰。核心机制是：1) 数据包定义纹饰图案（`trim_pattern`）和材料（`trim_material`），通过`recipe`文件将模板物品与图案关联；2) 资源包中的`armor_trims.json`使用`paletted_permutations`图集源，将灰度纹理与颜色调色板组合，生成不同材料颜色的纹饰纹理。游戏在运行时自动根据数据包和资源包内容加载这些自定义纹饰，无需修改游戏代码。特殊之处在于，纹饰纹理是灰度图，颜色由调色板动态替换，因此一个图案文件可对应多种材料颜色。

## 注意事项

- 资源包中的`armor_trims.json`必须使用`minecraft`命名空间，且路径为`assets/minecraft/atlases/armor_trims.json`
- 数据包修改后需要离开并重新加入世界才能生效，仅使用`/reload`命令无效
- 纹饰纹理必须是灰度图，且使用与`trim_palette.png`相同的颜色索引
- 常见误解：开发者可能认为锻造纹饰是硬编码的，只能使用原版已有的图案和颜色，无法通过数据包扩展。
