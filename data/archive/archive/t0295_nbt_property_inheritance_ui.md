---
id: t0295
title: "NBT属性继承控件"
title_en: "nbt_property_inheritance_ui"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202604/5/content"
source_type: "feature_article"
source_issue: "202604"
version_min: "1.20"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["nbt", "property_inheritance", "ui_framework", "floating_ui"]
verified_in_game: false
---

## 核心洞见

通过物品展示实体的custom_data存储UI控件属性，子控件从父控件NBT读取配置实现属性继承

## 代码示例

```mcfunction
# 判断用户是否传入了min属性，如果没有则设置默认值0
execute unless data storage floating_ui:input temp.min run data modify storage floating_ui:input temp.min set value 0
execute store result score @s floating_ui.slider.min run data get storage floating_ui:input temp.min

# 子控件从父控件读取模型属性
data modify storage floating_ui:input temp.model set from entity @s item.components."minecraft:custom_data".data.left_icon
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

Floating UI框架将UI控件的所有属性存储在对应物品展示实体的NBT中，具体位于item.components."minecraft:custom_data".data下。当创建控件时，通过data modify从storage读取用户传入的属性值，写入实体的custom_data。子控件创建时，通过data get from entity @s ...从父控件实体读取属性值，实现属性继承。例如左侧图标控件从父控件读取left_icon模型路径：data modify storage floating_ui:input temp.model set from entity @s item.components."minecraft:custom_data".data.left_icon。这种设计的特殊之处在于：1) 属性直接绑定到实体，无需外部存储；2) 子控件通过实体引用自然继承父控件属性；3) 使用NBT路径语法可以精确访问嵌套属性。整数属性则通过计分板存储，利用execute store result实现NBT到计分板的双向转换。

## 注意事项

- NBT路径中的引号需要正确转义，特别是包含冒号的命名空间
- custom_data中的属性名不能与Minecraft保留字段冲突
- 计分板只能存储整数，浮点属性需要定点数转换
- 常见误解：开发者可能认为每个UI控件需要独立的配置文件或存储空间来管理属性
