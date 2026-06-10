---
id: t0290
title: Smithed 命名空间前缀约定
title_en: Smithed Namespace Prefix Convention
layer: technique
source_url: "https://github.com/Alumopper/mcf-skill/blob/main/mcf-datapack/SKILL.md"
source_type: mcf_skill
wiki_covers_this: false
tags: ["interoperability", "namespacing", "multi-pack"]
verified_in_game: false
---

## 核心洞见

在多包环境中，所有包特定标识符（计分板、存储、实体标签）都必须使用包前缀，否则不同包之间必然发生冲突。

## 代码示例

```mcfunction
scoreboard objectives add tcc.dummy dummy
data merge storage tcc:data {foo: "bar"}
tag @s add tcc.custom_entity
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

计分板目标使用点分隔前缀（如 tcc.dummy），存储路径使用冒号分隔（如 tcc:data），实体标签使用点分隔前缀（如 tcc.custom_entity）。这些前缀确保不同包的同名标识符不会互相覆盖。

## 注意事项

- 常见误解：开发者常认为只要使用自己的命名空间（如 tcc:）就足够安全，但计分板目标和实体标签是全局的，没有命名空间机制，必须手动加前缀。
