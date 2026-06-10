---
id: t0280
title: 函数标签作为模块API
title_en: Function Tags as Module API
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-datapack/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["function-tag", "api", "modularity"]
verified_in_game: false
---

## 核心洞见

使用函数标签（function tag）作为模块的公共入口点，允许调用者通过标签名调用，而无需关心具体实现函数名。

## 代码示例

```mcfunction
json
// data/mypack/tags/function/my_module.json
{
  "values": [
    "mypack:api/my_module",
    "mypack:internal/_setup"
  ]
}
# 调用者
function #mypack:my_module
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

在数据包的 tags/function 目录下定义标签，其 values 列表包含公共API函数和可选的初始化函数。调用者使用 function #namespace:tag_name 即可触发整个模块。

## 注意事项

- 常见误解：开发者直接调用具体函数名，导致模块内部重构时破坏外部依赖。
