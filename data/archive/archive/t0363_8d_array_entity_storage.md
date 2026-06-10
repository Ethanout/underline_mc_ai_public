---
id: t0363
title: "八维数组实体存储"
title_en: "8d_array_entity_storage"
layer: technique
source_url: "https://cr-019.github.io/datapack-index/feature/archive/202601/a/content"
source_type: "feature_article"
source_issue: "202601"
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: medium
tags: ["数据存储", "多维数组", "实体数据", "storage"]
verified_in_game: false
---

## 核心洞见

通过将实体ID映射到命令存储的八维数组索引，可以为每个实体分配独立的、可自由读写的复杂数据空间，避免高频使用data命令操作实体NBT。

## 代码示例

```mcfunction
# 使用前执行please函数（函数的执行者必须是要存储数据的实体）
function #oh_my_dat:please
# 获取数据存储
data get storage oh_my_dat:_[-4][-4][-4][-4][-4][-4][-4][-4].DataName
# 修改数据存储
data modify storage oh_my_dat:_[-4][-4][-4][-4][-4][-4][-4][-4].DataName set value DataValue
# 删除数据存储
data remove storage oh_my_dat:_[-4][-4][-4][-4][-4][-4][-4][-4].DataName
```

## 用法

（待补充）

## 使用场景

（待补充）

## 机制原理

该技术利用命令存储（storage）支持多维数组的特性，构建一个八维数组作为数据容器。每个实体被分配一个唯一的ID（0~65536），通过数学映射将ID转换为八维数组的索引。例如，ID可以分解为8个维度上的坐标，每个维度范围0~3（因为4^8=65536），这样每个ID对应数组中的一个唯一位置。具体实现中，使用[-4][-4]...[-4]的索引语法访问数组末尾元素，通过计算得到实际索引。这样每个实体在storage中拥有一个独立的复合标签（可以包含任意NBT结构），通过data get/modify/remove命令即可读写，无需操作实体NBT。与朴素实现（直接使用实体NBT的data命令）相比，该技术避免了高频读写实体NBT带来的性能开销，因为storage操作比实体NBT操作快得多；与记分板相比，它支持存储任意复杂的数据结构（如列表、嵌套对象）。

## 注意事项

- 八维数组的维度大小必须精确匹配ID范围，否则会出现索引冲突
- 使用[-4]语法访问的是数组末尾，需要确保数组已正确初始化且索引计算正确
- 实体死亡或卸载后，其数据空间不会自动清理，需要配合gc机制回收
- storage中的数据不会随实体保存/加载，需要额外的持久化机制（如TSB中的时间戳备份）
- 常见误解：开发者通常认为存储实体私有数据只能使用记分板（仅整数）或实体NBT（高频读写性能差）。
