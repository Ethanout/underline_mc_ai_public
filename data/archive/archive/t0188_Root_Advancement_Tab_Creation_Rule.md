---
id: t0188
title: 根进度标签页创建规则
title_en: Root Advancement Tab Creation Rule
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-advancement/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["advancement", "tab", "root", "display"]
verified_in_game: false
---

## 核心洞见

根进度（无parent字段）且包含display对象时，会自动创建一个标签页，其图标即为根进度的图标，且该标签页会在该进度树中任意进度被达成时出现。

## 代码示例

```mcfunction
{
  "display": {
    "title": { "text": "My Tab" },
    "icon": { "id": "minecraft:diamond" },
    "frame": "task"
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

系统检测到无parent字段的进度定义，且其display对象存在，则自动将其作为标签页根节点。标签页图标直接复用根进度的icon字段。标签页的可见性由该进度树中任意子进度的达成触发。

## 注意事项

- 常见误解：开发者常以为标签页需要额外配置或只有特定进度才能创建，实际上只要根进度有display就会自动生成标签页。
