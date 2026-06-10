---
id: t0321
title: "面剔除连接纹理"
title_en: "cullface_connected_textures"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202605/3/content"
source_type: "feature_article"
source_issue: "202605"
version_min: "1.21.11"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["模型", "面剔除", "连接纹理", "cullface", "方块模型"]
verified_in_game: false
---

## 核心洞见

利用模型面剔除(cullface)机制，可以在不依赖Optifine等模组的情况下，仅通过原版模型系统实现连接纹理效果。

## 代码示例

```mcfunction
{
  "format_version": "1.21.11",
  "credit": "Made with Blockbench",
  "parent": "minecraft:block/cube_all",
  "textures": {
    "0": "block/diamond_block_down",
    "1": "block/diamond_block_left",
    "2": "block/diamond_block_right",
    "3": "block/diamond_block_surface",
    "4": "block/diamond_block_up",
    "particle": "block/diamond_block_down"
  },
  "elements": [
    {
      "name": "surface",
      "from": [0, 0, 0],
      "to": [16, 16, 16],
      "faces": {
        "north": {"uv": [0, 0, 16, 16], "texture": "#3"},
        "east": {"uv": [0, 0, 16, 16], "texture": "#3"},
        "south": {"uv": [0, 0, 16, 16], "texture": "#3"},
        "west": {"uv": [0, 0, 16, 16], "texture": "#3"},
        "up": {"uv": [0, 0, 16, 16], "texture": "#3"},
        "down": {"uv": [0, 0, 16, 16], "texture": "#3"}
      }
    },
    {
      "name": "cull_up",
      "from": [-0.003, 14.99998, -0.003],
      "to": [16.003, 15.99898, 16.003],
      "rotation": {"angle": 0, "axis": "y", "origin": [8, 8, 8]},
      "faces": {
        "north": {"uv": [0, 0, 16, 1], "texture": "#4", "cullface": "up"},
        "east": {"uv": [0, 0, 16, 1], "texture": "#4", "cullface": "up"},
        "south": {"uv": [0, 0, 16, 1], "texture": "#4", "cullface": "up"},
        "west": {"uv": [0, 0, 16, 1], "texture": "#4", "cullface": "up"},
        "up": {"uv": [0, 0, 16, 16], "texture": "#missing"},
        "down": {"uv": [0, 0, 16, 16], "texture": "#missing"}
      }
    },
    {
      "name": "cull_down",
      "from": [-0.003, 0.003, -0.003],
      "to": [16.003, 1.002, 16.003],
      "rotation": {"angle": 0, "axis": "y", "origin": [8, 8, 8]},
      "faces": {
        "north": {"uv": [0, 16, 16, 15], "texture": "#0", "cullface": "down"},
        "east": {"uv": [0, 16, 16, 15], "texture": "#0", "cullface": "down"},
        "south": {"uv": [0, 16, 16, 15], "texture": "#0", "cullface": "down"},
        "west": {"uv": [0, 16, 16, 15], "texture": "#0", "cullface": "down"},
        "up": {"uv": [0, 16, 16, 0], "texture": "#missing"},
        "down": {"uv": [0, 16, 16, 0], "texture": "#missing"}
      }
    },
    {
      "name": "cull_north",
      "from": [-0.002, 0.00102, -0.002],
      "to": [16.002, 1.00002, 16.002],
      "rotation": {"x": 90, "y": 0, "z": 0, "origin": [8, 8, 8]},
      "faces": {
        "north": {"uv": [0, 1, 16, 0], "texture": "#4", "cullface": "north"},
        "east": {"uv": [16, 0, 15, 16], "rotation": 90, "texture": "#2", "cullface": "north"},
        "south": {"uv": [0, 16, 16, 15], "texture": "#0", "cullface": "north"},
        "west": {"uv": [1, 0, 0, 16], "rotation": 90, "texture": "#1", "cullface": "north"},
        "up": {"uv": [0, 16, 16, 0], "texture": "#missing"},
        "down": {"uv": [0, 16, 16, 0], "texture": "#missing"}
      }
    },
    {
      "name": "cull_south",
      "from": [-0.002, 0.00102, -0.002],
      "to": [16.002, 1.00002, 16.002],
      "rotation": {"x": -90, "y": 0, "z": 0, "origin": [8, 8, 8]},
      "faces": {
        "north": {"uv": [0, 1, 16, 0], "texture": "#4", "cullface": "south"},
        "east": {"uv": [1, 0, 0, 16], "rotation": 90, "texture": "#1", "cullface": "south"},
        "south": {"uv": [0, 16, 16, 15], "texture": "#0", "cullface": "south"},
        "west": {"uv": [16, 0, 15, 16], "rotation": 90, "texture": "#2", "cullface": "south"},
        "up": {"uv": [0, 16, 16, 0], "texture": "#missing"},
        "down": {"uv": [0, 16, 16, 0], "texture": "#missing"}
      }
    },
    {
      "name": "cull_west",
      "from": [-0.001, 0.00102, -0.001],
      "to": [16.001, 1.00002, 16.001],
      "rotation": {"x": 0, "y": -90, "z": -90, "origin": [8, 8, 8]},
      "faces": {
        "north": {"uv": [16, 0, 15, 16], "rotation": 90, "texture": "#2", "cullface": "west"},
        "east": {"uv": [1, 0, 0, 16], "rotation": 90, "texture": "#1", "cullface": "west"},
        "south": {"uv": [1, 0, 0, 16], "rotation": 90, "texture": "#1", "cullface": "west"},
        "west": {"uv": [16, 0, 15, 16], "rotation": 90, "texture": "#2", "cullface": "west"},
        "up": {"uv": [0, 16, 16, 0], "texture": "#missing"},
        "down": {"uv": [0, 16, 16, 0], "texture": "#missing"}
      }
    },
    {
      "name": "cull_east",
      "from": [-0.001, 0.00102, -0.001],
      "to": [16.001, 1.00002, 16.001],
      "rotation": {"x": 0, "y": 90, "z": 90, "origin": [8, 8, 8]},
      "faces": {
        "north": {"uv": [1, 0, 0, 16], "rotation": 90, "texture": "#1", "cullface": "east"}
      }
    }
  ]
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术的核心是利用Minecraft模型系统中每个体素(elements)的cullface字段。cullface是一个枚举值，指定当方块某个方向存在完整面时，该面会被剔除（不渲染）。通过设计多个体素层叠：一个基础体素作为表面纹理（无cullface），多个边界体素分别设置不同方向的cullface（如cullface: "north"），并让边界体素略微超出基础体素范围（如from: [-0.003, 14.99998, -0.003]）。当相邻方向有完整面时，对应边界体素的面被剔除，露出基础体素；当无相邻面时，边界体素遮挡基础体素，形成边框效果。通过组合多个方向的边界体素，可以模拟出类似连接纹理的视觉连续性。关键推导：每个边界方向需要独立的体素，且边界体素的UV映射需精确对应纹理边缘（如UV从0到1像素范围），以避免z-fighting。

## 注意事项

- 边界体素的坐标需要略微超出基础体素范围（如-0.003到16.003），否则可能出现z-fighting导致闪烁
- 无法区分相邻方块是否为同一类型，只能检测是否有完整面，因此适用于所有完整方块
- 纹理UV映射需要精确对应边缘像素，否则连接处可能出现视觉断裂
- 在特定光影下，纯色区域的z-fighting可能仍然可见，需要采用边界填充法（将边界体素放在不同高度层）来避免
- 常见误解：开发者通常认为连接纹理必须通过Optifine的自定义纹理功能或复杂的方块状态系统来实现，而不知道可以利用cullface字段让方块在相邻完整面存在时自动隐藏对应面，从而模拟连接纹理。
