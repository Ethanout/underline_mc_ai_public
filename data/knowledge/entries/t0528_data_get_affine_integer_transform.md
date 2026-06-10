---
id: t0528
title: "data get 实现整数仿射变换"
title_en: "data_get_affine_integer_transform"
layer: technique
source_url: "manual:pasted-text.txt"
source_type: manual
version_min: "1.13"
version_max: ""
wiki_covers_this: false
confidence: low
tags: ["data_get", "execute_store", "integer", "rounding", "affine_transform"]
verified_in_game: false
---

## 核心洞见

利用 `/data get` 的缩放参数与 `execute store result ... int <scale>` 的两次缩放和取整，可以在特定条件下用一条命令实现形如 `x*a-b` 的整数变换。

## 示例

目标计算 `x*3-5`，选择外层缩放 `b=5`、内层缩放约 `a/b=0.6`：

```mcfunction
# x 为正数
execute store result storage io var int 5 run data get storage io var .5999999999

# x 为负数
execute store result storage io var int 5 run data get storage io var .6000000001
```

## 机制原理

`data get` 的缩放和 `execute store result ... int` 的存储都会涉及数值缩放与整数取整。通过让内层系数略小于或略大于精确比值，可以利用正负数取整方向差异人为引入一个单位偏移，再由外层缩放把偏移放大为目标常数。

## 注意事项

- 来源明确指出 `x=0` 不适用。
- 正数和负数必须使用不同的微小偏移。
- 浮点精度、溢出和取整规则可能使部分输入失败，必须先枚举测试目标输入范围。

