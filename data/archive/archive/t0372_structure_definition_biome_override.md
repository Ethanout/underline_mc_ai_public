---
id: t0372
title: "结构生物群系覆盖"
title_en: "structure_definition_biome_override"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202508/0/content"
source_type: "feature_article"
source_issue: "202508"
version_min: "1.18"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["worldgen", "structure-definition", "biome-override"]
verified_in_game: false
---

## 核心洞见

通过自定义结构定义文件，可以将原版结构（如村庄）生成到非原生生物群系（如海洋），实现海底村庄等创意效果。

## 代码示例

```mcfunction
{
  "type": "minecraft:jigsaw",
  "biomes": "#minecraft:is_ocean",
  "max_distance_from_center": 80,
  "project_start_to_heightmap": "OCEAN_FLOOR_WG",
  "start_height": {
    "absolute": 0
  },
  "size": 3,
  "spawn_overrides": {},
  "start_pool": "minecraft:village/plains/town_centers",
  "step": "surface_structures",
  "terrain_adaptation": "beard_thin",
  "use_expansion_hack": true
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

结构定义文件中的biomes字段指定生成群系（如#minecraft:is_ocean），覆盖原版限制。type设为jigsaw以支持拼图生成，project_start_to_heightmap设为OCEAN_FLOOR_WG使起始结构生成在海床上。但后续拼图部分可能因高度映射不一致而异常，因为拼图方块默认使用绝对高度而非地形高度，导致子结构生成位置偏离。

## 注意事项

- project_start_to_heightmap仅影响起始结构，子结构可能不遵循地形高度
- terrain_adaptation设置不当会导致结构浮空或埋入地下
- use_expansion_hack为false时可能限制垂直扩展
- 常见误解：开发者可能认为结构只能生成在其原定生物群系中，无法跨群系使用。
