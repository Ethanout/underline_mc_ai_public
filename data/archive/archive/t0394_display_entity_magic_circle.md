---
id: t0394
title: "展示实体法阵"
title_en: "display_entity_magic_circle"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202507/5/content"
source_type: "feature_article"
source_issue: "202507"
version_min: "1.21.5"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["展示实体", "模型映射", "染色", "魔法阵", "资源包"]
verified_in_game: false
---

## 核心洞见

利用物品展示实体的模型映射与染色功能，可以动态组合多层旋转纹理，实现可编程的魔法阵效果。

## 代码示例

```mcfunction
function sklibs:skmagic/new {config:{elements:[{model:"d2.2.1",id:"1",size:6f,distance:8f,color:[1,1,0.5],rotate_step:[15,0.5]},{model:"d2.2.2",id:"1",size:6f,distance:8f,color:[1,1,1],rotate_step:[15,-0.5]}]}}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术基于 Minecraft 1.21.5 引入的物品展示实体（item display entity）的模型映射（model predicate）和染色（tint）机制。物品展示实体可以显示一个物品模型，并通过 `item` NBT 指定物品 ID 和组件（components）。通过资源包中的 `items/` 目录下的物品模型映射文件（如 `acacia_button.json`），可以为同一个物品（如金合欢按钮）定义多个模型变体，每个变体通过 `when` 条件（如 `d2.2.1`）区分。在数据包中调用 `sklibs:skmagic/new` 函数时，传入的 JSON 参数包含 `elements` 数组，每个元素指定 `model`（对应映射中的 `when` 值）、`size`（缩放）、`distance`（距离）、`color`（RGB 染色值）和 `rotate_step`（每 tick 旋转角度）。函数内部会生成多个物品展示实体，每个实体对应一层纹理，设置其 `item` 为金合欢按钮并附加 `minecraft:custom_model_data` 组件以匹配模型映射，同时设置 `transformation` 为平移（沿 Z 轴负方向移动 `distance` 格）和缩放（`size` 倍），并应用 `interpolation_duration` 和 `teleport_interpolation_duration` 实现平滑旋转。每 tick 通过 `execute store success` 累加旋转角度，实现各层独立旋转。染色通过 `item` 的 `minecraft:dyed_color` 组件实现，将 RGB 值转换为整数颜色。这种方法的特殊之处在于：1）利用物品展示实体而非粒子，性能更好且不受视距限制；2）通过模型映射实现纹理复用，无需为每层创建独立物品；3）染色功能允许动态调整颜色，无需额外纹理。

## 注意事项

- 模型映射文件中的 `when` 值必须与数据包调用时传入的 `model` 字段完全一致，否则无法显示纹理
- 染色颜色值范围为 0.0~1.0，超出范围可能导致颜色异常或实体不可见
- 每层纹理需要独立的模型文件，且所有模型文件必须使用同一个基础物品（如 acacia_button）的映射
- 旋转角度 `rotate_step` 是每 tick 的增量，过大会导致旋转不平滑，过小则旋转太慢
- 常见误解：开发者可能认为魔法阵需要粒子系统或自定义实体渲染，或者使用盔甲架+地图画等复杂方式实现。
