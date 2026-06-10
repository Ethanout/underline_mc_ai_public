---
id: t0382
title: "配方类型转化"
title_en: "recipe_type_transmute_mechanism"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202508/3/content"
source_type: "feature_article"
source_issue: "202508"
version_min: "1.20.3"
version_max: ""
wiki_covers_this: true
confidence: medium
tags: ["配方", "类型转化", "物品组件"]
verified_in_game: false
---

## 核心洞见

crafting_transmute配方类型允许将输入物品转化为另一种物品，同时可以自定义物品组件，实现类似锻造台但无需模板的升级机制。

## 代码示例

```mcfunction
{
  "type": "crafting_transmute",
  "input": "diamond_sword",
  "material": "netherite_block",
  "result": {
    "id": "netherite_sword",
    "components": {
      "!minecraft:repair_cost": {}
    }
  }
}
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

crafting_transmute是Minecraft 1.20.3引入的配方类型，它定义了一个输入物品（input）和一个消耗材料（material），合成后输出指定的结果物品（result）。与有序/无序配方不同，它不要求特定排列，只需在工作台中将输入和材料放在任意位置即可。result字段支持components子字段，可以自定义或清除物品组件（如使用!minecraft:repair_cost清除铁砧惩罚）。这种配方类型简化了物品升级逻辑，无需锻造模板或额外条件。

## 注意事项

- input和material字段可以使用数组指定多个物品，但数组和标签不能同时使用
- components中的!前缀用于清除组件，但必须确保组件名称正确，否则可能无效
- 常见误解：开发者可能认为只有锻造台或工作台有序/无序配方才能实现物品升级，或者需要复杂的命令系统来模拟转化。
