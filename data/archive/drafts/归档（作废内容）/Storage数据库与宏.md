# Storage 数据库与宏

用 Storage 作为数据容器，配合 NBT 路径列表筛选实现简单的键值数据库。

## 什么是 Storage

Storage 是全局 NBT 容器，由数据包通过 `data modify storage ...` 操作：
- **跨维度**：所有维度共享同一份数据
- **持久化**：重启后读取最后一次保存的值（存档保存时会序列化到 level.dat）
- **全局访问**：任何函数、任何维度都可读写

## Storage vs 实体 vs 计分板

| 容器 | 持久化 | 跨维度 | 数据类型 |
|------|:---:|:---:|----------|
| 实体 NBT | 否（重启重置） | 否 | NBT 任意结构 |
| 计分板 | 是 | 是 | 32 位整数 |
| Storage | 是（存档时保存） | 是 | NBT 任意结构（含列表/复合） |

## 基本操作

```mcfunction
# 写
data modify storage ns:db player set value "Steve"
data modify storage ns:db scores set value [100, 200, 300]

# 读
data get storage ns:db

# 合并
data modify storage ns:db merge value {level:5}
```

## NBT 路径：列表筛选

```json
{
  "data": [
    { "id": 1, "name": "Steve", "scores": [10, 20] },
    { "id": 2, "name": "Alex",  "scores": [15, 25] }
  ]
}
```

```mcfunction
# 按 id 筛选修改
data modify storage ns:db data[{id:2}].name set value "Alex2"

# 按条件添加（没有匹配项时新建）
data modify storage ns:db data[{id:3}] set value {id:3,name:"New"}
```

## 宏语法参考

宏允许函数接收来自 Storage 的动态参数。

### 定义宏函数

文件：`data/<namespace>/function/<path>.mcfunction`
```mcfunction
$say 玩家 $(player) 的等级为 $(level)
$scoreboard players set $(player) xp $(level)
```

### 调用宏

```mcfunction
data modify storage ns:io player set value "Steve"
data modify storage ns:io level set value 10
function ns:path/to/macro with storage ns:io
```

### 宏参数规则
- 行首 `$` 标记该行为宏行
- `$(键名)` 会被替换为 Storage 中对应的值
- `function ... with storage <id>` 将整个 Storage 传入宏

### 宏与 NBT 路径

```mcfunction
# 通用写宏
$data modify storage ns:db $(path) set value $(value)

# 调用
data modify storage ns:io path set value "data[{id:2}].name"
data modify storage ns:io value set value "Alex"
function ns:macro/write with storage ns:io
```

## 宏易错点

1. `$` 必须在行首，不能在中途：`$data modify ...` 正确，`data $modify ...` 错误
2. `function ... with storage ...` 传入整个 Storage 根：`with storage ns:io`（不是 `ns:io.path`）
3. `$()` 里只能写键名，不能写路径：`$(id)` 正确，`$(data.id)` 错误
4. `$()` 不能嵌套：`$($(key))` 不支持
