---
id: t0392
title: "跨帧数据持久化"
title_en: "cross_frame_data_persistence"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202508/2/content"
source_type: "feature_article"
source_issue: "202508"
version_min: "1.21.4"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["后处理", "帧缓冲", "数据持久化", "跨帧", "着色器"]
verified_in_game: false
---

## 核心洞见

利用后处理帧缓冲的 persistent 标记和双缓冲交换，实现跨帧数据存储，无需数据包或记分板。

## 代码示例

```mcfunction
// 后处理管线配置片段 (assets/minecraft/post_effect/transparency.json)
{
  "targets": {
    "final": {},
    "hidden_final": {},
    "cps_last_data": {"persistent": true},
    "cps_next_data": {}
  },
  "passes": [
    // ... 其他 pass ...
    {
      // 计算当前帧数据
      "vertex_shader": "minecraft:post/cps_main",
      "fragment_shader": "minecraft:post/cps_main",
      "inputs": [
        {"sampler_name": "In", "target": "final"},
        {"sampler_name": "CpsData", "target": "cps_last_data"}
      ],
      "uniforms": {},
      "output": "cps_next_data"
    },
    {
      // 将新数据复制到 persistent 缓冲供下一帧使用
      "vertex_shader": "minecraft:post/blit",
      "fragment_shader": "minecraft:post/blit",
      "inputs": [
        {"sampler_name": "In", "target": "cps_next_data"}
      ],
      "uniforms": {},
      "output": "cps_last_data"
    }
  ]
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

后处理渲染管线允许定义自定义帧缓冲（targets），其中设置 "persistent": true 的缓冲会在帧之间保留数据，不会自动清除。通过设计双缓冲策略：cps_last_data（persistent）存储上一帧的数据，cps_next_data（非 persistent）存储当前帧计算的新数据。在一帧结束时，将 cps_next_data 的内容复制到 cps_last_data（通过一个额外的渲染 pass 或直接交换引用），使得下一帧可以读取到上一帧的数据。这样，着色器可以访问历史帧的像素信息，从而实现时间序列分析（如 CPS 计数）。关键点在于：后处理管线中的每个 pass 可以指定多个输入缓冲和一个输出缓冲，通过合理编排 pass 顺序，可以实现数据的读取、计算和写入。

## 注意事项

- persistent 缓冲在分辨率变化或资源包重载时会重置，需要重新初始化
- 双缓冲交换必须确保在每一帧结束时完成，否则数据会错乱
- 多个 pass 的输入输出依赖关系需要正确配置，避免循环依赖
- 不同图形品质（如极佳、高品质）的管线不同，需要分别适配
- 常见误解：开发者通常认为原版无法在帧之间持久化数据，或只能通过实体、记分板等游戏内机制间接存储。
