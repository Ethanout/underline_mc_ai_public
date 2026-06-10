---
id: t0297
title: 惰性加载与透明文件句柄
title_en: Lazy Loading and Transparent File Handles
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-datapack/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["beet", "lazy-loading", "file-handle", "performance"]
verified_in_game: false
---

## 核心洞见

Beet 的文件系统是惰性加载的，文件在访问前不会实际读取，且文件句柄在未加载、序列化、反序列化状态间自动转换，无需手动管理。

## 代码示例

```mcfunction
# 直接访问函数，Beet 自动加载
func = ctx.data.functions["demo:foo"]
# 修改后自动标记为需要重新序列化
func.lines.append("say modified")
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Beet 使用文件句柄抽象，文件在首次访问（如 `pack.functions["demo:foo"]`）时才从磁盘加载。句柄状态自动在未加载（Unloaded）、序列化（Serialized）、反序列化（Deserialized）间转换，开发者始终以 Python 对象形式操作，无需关心底层文件格式。

## 注意事项

- 常见误解：开发者通常认为构建工具会立即加载所有文件，导致大型项目启动缓慢，且需要手动处理文件格式转换。
