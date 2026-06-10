# 函数结构、IO 惯例与命名

## 模块化结构
```
mypack/
└── function/
    ├── load.mcfunction              # #minecraft:load 入口
    ├── tick.mcfunction              # #minecraft:tick 入口
    ├── help.mcfunction              # 自描述帮助
    ├── api/                         # 公有 API（调用方依赖此接口）
    │   ├── module_a.mcfunction
    │   └── module_b.mcfunction
    └── internal/                    # 私有实现（可随时更改）
        ├── _helper.mcfunction       # 下划线前缀=私有
        └── _core.mcfunction
```

## 命名与存储约定（可参考规范）

> 以下为推荐性规范，不强硬要求，但建议数据包内保持统一。如果项目已有规范，则遵循项目规范。

### 函数路径
```
namespace:class/method                                  # 类.方法
namespace:class/method/process                          # 类.方法.过程
namespace:class/method/process_subprocess0              # 类.方法.过程_子过程0，子过程（如if分支的下级）可以正常用函数名，不一定要加数字，但是必须保证能从名字看出调用关系
namespace:class/method/process_subprocess0_subprocess0  # 类.方法.过程_子过程1_子过程0
namespace:class/method/process_subprocess1              # 类.方法.过程_子过程1
namespace:class/method/process/enum                     # 类.方法.过程.穷举函数，无特殊情况不嵌套这么深
```

### Storage 空间分类
```
namespace:io <class>         - 暂存数据（tick 结束后视为销毁，不可跨 tick）
namespace:data <class>       - 内部数据（类跨 tick 的动态/静态数据）
namespace:ins <class>        - 构建数据列表（类似变量栈，[{...},{...},...]）
namespace:preset <class>     - 静态预设数据
```
`namespace:preset <class>.name` 一般是 `namespace:io <class>` 的其中一个预设。

### 计分板
两种形式，一种挂载在实体上，一种是全局的。
```
@s namespace.class            - 类的属性（挂载在实体上）
@s namespace.class.xxxx       - 子属性
@s namespace.class.xxxx.a     - 子属性的子属性
score class namespace         - 全局值（class 为假玩家名）
score class.xxx namespace
```

### 常量声明

所有常量在 `#minecraft:load` 中统一声明。

```mcfunction
# #minecraft:load
scoreboard objectives add num dummy
scoreboard players set 123 num 123   # 常用数值常量
scoreboard players set 0 num 0
scoreboard players set 1 num 1
scoreboard players set -1 num -1
```

### 假玩家命名规范
- `#` 前缀：内部计算变量/常量（`#tmp`, `#i`, `#result`）
- 无 `#` 前缀：接口变量，其他包可通过此名字读写

```mcfunction
# #minecraft:load
scoreboard objectives add ns dummy
scoreboard players set #TRUE ns 1
scoreboard players set #FALSE ns 0
scoreboard players set #HALF ns 500     # 500 = 0.5 (×1000)
scoreboard players set #PI ns 3141
```

### 记分板选择
- 推荐统用一个记分板（如 `num` 或命名空间 `ns`），避免散落一堆
- 不硬性要求，但如果散落多个记分板，建议在 `load` 开头集中列出全部 `scoreboard objectives add`

## 函数标签作为 API
```json
// data/mypack/tags/function/my_module.json
{ "values": ["mypack:api/my_module", "mypack:internal/_setup"] }
```
调用方用：`function #mypack:my_module`

## 函数文档约定
```mcfunction
# ============================================
# mypack:api/my_function
# 简短描述
#
# 输入：
#   Storage namespace:io class:
#     field (type): 描述
#   Score $score_name namespace.class: 描述
#
# 输出：
#   Return: 1=成功, 0=失败
#   Storage namespace:data class.result: 描述
# ============================================
```

## 自描述帮助系统
```mcfunction
# help.mcfunction
tellraw @a [{"text":"=== MyPack v1.0 ===","color":"gold"}]
tellraw @a [{"text":"  #mypack:module_a  - 描述","color":"gray"}]
tellraw @a [{"text":"  #mypack:module_b  - 描述","color":"gray"}]
```
运行：`function #mypack:help`

## 实体安全
```mcfunction
# ❌ 永远别这样——会杀自己/系统的实体
kill @e
# ✅ 用标签保护
kill @e[tag=!mypack.persistent]
```
创建持久实体时加标签：`Tags:["mypack.persistent"]`
