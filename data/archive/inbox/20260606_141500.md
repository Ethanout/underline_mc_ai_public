
# 对于mcf的语言规范

以下所有规定只是君子协议，用于理清思路，让文件夹结构干净可读，并尽可能的包容大部分开发者的习惯。

这些不是硬性规定，仅为我制定的规范，编译器不会对这些做任何检查。

## 命名原则
1. 简短优先。
2. 宁长勿短。不能因简短产生歧义。

## 核心概念
- 字段
- 特殊字段
- 方法编写规范
- 临时变量

## 字段
### 字段和存放位置
一个字段（也称类）是一组命名和数据形式的约定。任何符合约定的数据、实体或方块，都可以视为该字段的对象。
字段可以分散存放在不同位置。
如字段test可以存放在以下位置：
```
score(@s test) self位置
score(test <namespace>) 假玩家变量位置
storage(<namespace>:io temp.test) (any) 临时交换位置（具体为不影响接口的跨方法位置，见下文）
storage(<namespace>:io test) (any) 跨方法接口位置
storage(<namespace>:stack test) 形式为(list<compound>) 跨方法接口位置（变量栈）
storage(<namespace>:stat test) (compound) 纯静态数据容器，可以存放test的模板，常量等内容，一般禁止编辑
storage(<namespace>:data test) (compound) 动态数据容器，用于存放需要跨tick的类内变量
entity/block(?.test) (any) 对象位置；不限制实体或方块的类型，只要其中一部分数据符合 `test` 的约定，就视为 `test` 对象
tag(<namespace>.test)
function <namespace>:test/method

# process_0仅为演示，实际不用数字，应该根据子过程的功能或者特点来命名
function <namespace>:test/method/process_0
function <namespace>:test/method/process_1

# 当逻辑链引用_subprocess时，建议让函数的前半部分命名保持一致
function <namespace>:test/method/process_1_subprocess
function <namespace>:test/method/process_1_subprocess_subsubprocess

# 当逻辑链内出现环时，建议在命名中加入loop
function <namespace>:test/method/process_2
function <namespace>:test/method/process_2_loop

# 复杂嵌套
function <namespace>:test/method/process_3
function <namespace>:test/method/process_3_loop_a
function <namespace>:test/method/process_3_loop_b

# 原则上，只有大量的宏函数穷举允许使用第四层
function <namespace>:test/method/process_macro/lots_of_enum_0
function <namespace>:test/method/process_macro/lots_of_enum_1
```

其中实体 tag 必须手动添加命名空间前缀：
```
tag(<namespace>.test)
tag(<namespace>.test.a)
```

### 字段的相关关系（属性和继承）
和字段相关的关系有两种，一种是属性，一种是继承。同名变量只能选择其一，不能既是属性，又是继承。

属性和继承的区别：
- 形式上，前者主要体现在变量，后者主要体现在文件结构。
- 含义上，前者表示字段的内部变量，在逻辑上一般表示字段的一部分。后者一般表示字段的个性化和特殊化。如：pos.x为属性，character.knight为继承。
- 表示字段的一种完整类型时使用继承；只表示字段的一部分数据时使用属性。

假设test内有a属性：
```
score(@s test.a)
score(test.a <namespace>)
storage(<namespace>:io temp.test.a) (any)
storage(<namespace>:io test.a) (any)
storage(<namespace>:stack test[0].a)
storage(<namespace>:stat test.template_name.a) (compound)
storage(<namespace>:data test.something_internal) (compound)
tag(<namespace>.test.a)
function <namespace>:test/method/process
```
假设test内有b继承：
```
score(@s test.b)
score(test.b <namespace>)
storage(<namespace>:io temp.test.b) (any)
storage(<namespace>:io test.b) (any)
storage(<namespace>:stack test.b[0])
storage(<namespace>:stat test.b.template_name) (compound)
storage(<namespace>:data test.b.something_internal) (compound)
tag(<namespace>.test.b)
function <namespace>:test.b/method/process
```

### 复合字段
当一个字段和其他变量相关时，这个字段就成为复合字段。

#### 复合字段的冲突
常见的冲突有以下2种形式：
- 字段和子字段的冲突
- 属性和继承的冲突

这些位置的名称通常不会发生冲突，保持原名能够让常用代码更短、更容易阅读：
```
score(@s test.b)
score(test.b <namespace>)
storage(<namespace>:io temp.test.b) (any)
storage(<namespace>:io test.b) (any)
tag(<namespace>.test.b)
```
长期结构化存储需要处理冲突：
```
storage(<namespace>:stack test[0].a)
storage(<namespace>:stat test.template_name.a) (compound)
storage(<namespace>:data test.something_internal) (compound)
```

#### 字段和子字段的冲突
在记分板、tag 和 `io` 等不需要处理冲突的位置中，允许字段本身和它的属性或继承同时存值。最典型的情况为：
```
#load
scoreboard objectives add is_q.trigger dropped:stone
scoreboard objectives add is_q dummy

#player/tick
# 为了保持逻辑干净，我们希望把killed_by_zombie的重置逻辑提前
execute if score @s is_q.trigger matches 1.. run function player/tick/q_triggered
# 其他依赖is_q的逻辑...

#player/tick/killed_by_zombie_triggered
scoreboard players set @s is_q.trigger 0
scoreboard players set @s is_q 1
```

在 `stack`、`stat` 和 `data` 中，可能会发生冲突，如：
```
storage(<namespace>:data test) 1b
storage(<namespace>:data test.a) 2b
```
NBT 节点 `test` 不能同时既是 `1b`，又是包含 `a` 的 compound。此时应把字段本身的值放入特殊子字段 `value`：
```
storage(<namespace>:data test.value) 1b
storage(<namespace>:data test.a) 2b
```

#### 属性和继承的冲突
属性和继承同名时，只在 `stack`、`stat` 和 `data` 等长期结构化存储中处理冲突。

假设 `character` 有父类型属性，同时存在 `knight` 和 `mage` 继承。记分板、tag、`io`、`ins` 等不冲突的位置可以继续使用简短命名：
```
score(@s character.health)
score(@s character.knight.health)
score(@s character.mage.health)
tag(<namespace>.character.knight)
storage(<namespace>:io character.health)
```

只有在长期结构化存储中，为父类型属性创建 `default` 或 `dummy` 继承：
```
storage(<namespace>:data character.default.health)
storage(<namespace>:data character.default.mana)
storage(<namespace>:data character.knight.health)
storage(<namespace>:data character.knight.armor)
storage(<namespace>:data character.mage.health)
storage(<namespace>:data character.mage.mana)
```

静态模板和变量栈同理：
```
storage(<namespace>:stat character.default.template_name)
storage(<namespace>:stat character.knight.template_name)
storage(<namespace>:stack character.default[0])
storage(<namespace>:stack character.knight[0])
```

因此，`default` 不是所有位置都必须遵守的命名层级，而是解决长期嵌套数据结构冲突时才使用的工具。

没有实际结构冲突时，优先使用更简洁的名称。


## 特殊字段
特殊字段主要用于标记，不强制使用。
常见的标记有：自动方法、私有方法和长期变量。
判断名称是否冲突时，应忽略特殊标记。例如，`__tick__` 和 `tick` 被视为同一字段，不应分别实现不同功能。如果特殊字段只增加一层调用，并且两者功能完全相同，则允许同时创建：
```mcfunction
# __tick__.mcfunction
function <namespace>:tick
```

不同标记的形式如下：
```
__tick__       # 自动方法：双下划线包围
__validate     # 私有方法：前面加双下划线
__id__         # 长期变量：双下划线包围
```

### 自动方法
自动方法是预期由游戏特性或游戏内入口调用的函数，使用双下划线包围。如：
- `__load__`、`__tick__`等函数标签入口。
- `__etick__`、`__ritck__`、`__5tick0__`等函数标签分发的二级入口。
- 进度奖励、附魔触发等游戏机制入口。
- 预期从聊天框调用的命令、测试和调试入口。

#### 函数标签分发的二级入口
函数标签分发的二级入口，可以在 `tick` 前后添加修饰词。名称不限制，能表达含义即可。如：
```
# etick表示entity tick
execute as @e[tag=<namespace>.chara.knight] at @s run function <namespace>:chara.knight/__etick__

# 5tick0 表示每5tick周期内的第0次执行，5tick2 表示每5tick周期内的第2次执行
# 假设 5 <namespace> 已经在 #load 里声明
execute store result score 5time <namespace> store result score time <namespace> run time query gametime
scoreboard players operation 5time <namespace> %= 5 <namespace>

execute if score 5time <namespace> matches 0 run function <namespace>:__5tick0__
execute if score 5time <namespace> matches 2 run function <namespace>:__5tick2__

# rtick 表示 random tick
execute as @e[sort=random,limit=1] at @s run function <namespace>:entity/__rtick__

# 也可以用任何其他命名
execute as @e[...] at @s run function <namespace>:entity/__prefix_4tick2_suffix__
```

### 私有方法
中间过程不能被其他方法调用。当多个方法需要调用同一个中间过程时，应将其提升为私有方法。

私有方法供当前字段内的所有方法调用，但不对字段外开放。方法名前面加双下划线表示私有方法。

如：
```
# 对外开放的方法
function <namespace>:test/create
function <namespace>:test/update

# 仅供 create 使用的中间过程，update 不应调用
function <namespace>:test/create/validate
function <namespace>:test/create/write_data

# create 和 update 都可以调用的私有方法
function <namespace>:test/__validate
```

`test` 以外的字段不应直接调用 `test/__validate`。



### 长期变量
需要跨 tick 存储的假玩家变量可以标记为长期变量，表示不可随意修改。
最常见的情况是记分板 ID，如：
```
execute store result score @s id run scoreboard players add __id__ <namespace> 1
```

## 方法编写规范

### 头文档
头文档标准规范如下，任何部分都可以省略：
```
#> 函数调用名
#   自然语言说明
# @input
#   输入
# @output
#   输出
```
最简形式为：
```
#> 
#   说清楚函数干了什么。比如输入输出是什么，修改了哪些东西，有什么副作用。
```

### 方法输入
方法输入默认只读。方法需要修改输入时，必须在文档中说明。

## 临时变量
临时变量只用于当前过程或逻辑链，用完后不应继续依赖。

常见的临时变量有：
```
score(#temp <namespace>)                # 临时假玩家变量
score(@s <namespace>)                   # 当前执行者上的临时记分板变量
storage(<namespace>:io temp.test)       # 临时结构化数据
tag(<namespace>.this)                   # 临时标记当前对象
tag(<namespace>.init)                   # 临时标记刚创建的实体
```

调用普通方法后，临时变量的值可能仍然存在，但应视为内容未知，不得继续读取。私有方法除外。如：
```
#> class/method_1
scoreboard players set #a minecraft 1

function class/__method_2
# 这里可以使用 #a minecraft，私有方法不销毁

function class/method_3
# 这里不可以使用 #a minecraft


#> class/__method_2
# 这里不可以使用 #a minecraft


#> class/method_3
# 这里不可以使用 #a minecraft
```

普通方法不应直接作为其他方法的中间过程使用。如果确实需要调用，有2种方法：

1. 显式指定作用域（推荐）
```
#> class/method_1
# scoreboard players set #a minecraft 1（不使用临时变量）
# 使用全局变量
scoreboard players set class.a minecraft 1
function method_2
```
这里的 `class.a` 是显式指定的方法输入。按照方法输入的约定，`method_2` 不应修改它；如果需要修改，必须提前说明。

显式作用域不能避免递归或嵌套调用覆盖同一个变量。存在这类调用时，应改用变量栈。

2. 将公共的中间过程提升为私有方法
```
#> class/method_1
scoreboard players set #a minecraft 1
function class/method_2
# a用不了了
```
改为：
```
#> class/method_1
scoreboard players set #a minecraft 1
function class/__method_2

#> class/__method_2
function class/method_2
```
私有方法与调用者共用临时变量。使用时，不要覆盖调用者之后仍需使用的值。
