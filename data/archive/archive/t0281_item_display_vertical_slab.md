---
id: t0281
title: "展示架竖半砖"
title_en: "item_display_vertical_slab"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202603/2/content"
source_type: "feature_article"
source_issue: "202603"
version_min: "1.21.9"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["resourcepack", "display_entity", "vertical_slab", "model_override"]
verified_in_game: false
---

## 核心洞见

通过修改台阶模型文件并利用展示架的物品显示变换，可以用纯资源包实现竖半砖效果，无需模组或数据包。

## 代码示例

```mcfunction
{
  "parent": "block/block",
  "textures": {
    "particle": "#side"
  },
  "elements": [
    {
      "from": [-0.01, -0.01, -0.01],
      "to": [16.01, 8.01, 16.01],
      "faces": {
        "down":  {"uv": [-0.01, -0.01, 16.01, 16.01], "texture": "#bottom", "cullface": "down"},
        "up":    {"uv": [-0.01, -0.01, 16.01, 16.01], "texture": "#top"},
        "north": {"uv": [-0.01, 8.01, 16.01, 16.01], "texture": "#side", "cullface": "north"},
        "south": {"uv": [-0.01, 8.01, 16.01, 16.01], "texture": "#side", "cullface": "south"},
        "west":  {"uv": [-0.01, 8.01, 16.01, 16.01], "texture": "#side", "cullface": "west"},
        "east":  {"uv": [-0.01, 8.01, 16.01, 16.01], "texture": "#side", "cullface": "east"}
      }
    }
  ],
  "display": {
    "on_shelf": {
      "rotation": [-90, 0, 0],
      "translation": [0, 0, -16],
      "scale": [4, 4, 4]
    }
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术基于Minecraft 1.21.9引入的展示架（item display）机制。展示架可以渲染物品，且物品的模型可以通过资源包中的`display`标签定义变换（旋转、平移、缩放）。原版台阶的模型文件`assets/minecraft/models/block/slab.json`定义了半砖的几何形状（从[0,0,0]到[16,8,16]）。通过修改该文件，添加`display.on_shelf`变换（旋转-90度、平移[0,0,-16]、缩放4倍），使台阶物品在展示架上渲染为竖立的半砖。同时，为了消除展示架边框与模型之间的深度冲突（z-fighting），将模型的`from`和`to`坐标微调为[-0.01,-0.01,-0.01]到[16.01,8.01,16.01]，并相应调整UV坐标，使模型略微包裹展示架。由于所有台阶都继承自`slab.json`，修改父模型即可对所有台阶生效。与直觉不同，这不是修改方块本身，而是修改物品在特定方块实体（展示架）上的显示方式，因此不改变方块的放置逻辑或碰撞箱。

## 注意事项

- 展示架上的物品使用实体渲染，受深度精度影响，稍远处可能出现深度冲突（z-fighting），且更远处不再渲染
- 大批量使用展示架可能影响渲染性能，因为每个展示架都需要独立上传VBO
- 模型微调后相邻展示架之间仍可能有微小重合部分，导致视觉瑕疵
- 常见误解：开发者通常认为竖半砖只能通过模组修改方块模型或数据包生成实体来实现，忽略了资源包可以修改物品在展示架上的渲染变换。
