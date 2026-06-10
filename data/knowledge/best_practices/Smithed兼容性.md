# Smithed 兼容性与多包互操作

## 冲突类型
| 类型 | 症状 | 原因 |
|------|------|------|
| storage 冲突 | A 包修改了 B 包的 storage | 无命名空间隔离 |
| 函数覆盖 | 两个包写同路径文件 | pack 加载顺序决定谁赢 |
| 标签污染 | `#tick` 被注入无关函数 | 函数标签不加区分 |
| UUID 冲突 | 两个包用了相同 UUID | 未做 UUID 分配协调 |

## Smithed 方案

### Storage 隔离
```mcfunction
# ❌ 裸 storage（和所有人冲突）
data modify storage state value {players:[]}

# ✅ 带命名空间的 storage
data modify storage mypack:state value {players:[]}
```

### 函数 API 声明
```json
// data/mypack/tags/function/api.json
{
  "values": ["mypack:api/do_thing"]
}
```
其他包通过 `function #mypack:api` 调用，不依赖具体路径。

### UUID 注册
```mcfunction
# 请求分配 UUID
scoreboard players add $uuid.allocator bs.data 1
scoreboard players operation $my_uuid bs.data = $uuid.allocator bs.data
```
或者通过 UUID 命名空间前缀：`mypack_`。

## 多包互操作设计模式

### 事件总线
```json
// data/mypack/tags/function/events/player_attack.json
{ "values": [] }  // 空标签 = 事件插槽，其他包注入
```
```mcfunction
# 其他包注入
// data/other/tags/function/mypack/events/player_attack.json
{ "values": ["other:on_player_attack"] }
```

### 数据空间
```mcfunction
# ns 前缀约定：每个包用自己的命名空间前缀
data modify storage mypack:systems.registry append value {...}
```

### 互包函数调用
```mcfunction
# 用标签而非硬编码路径
execute if function #other_pack:api/check_available run function #other_pack:api/do_thing
```

### 互包数据访问（局限）
```mcfunction
# data modify from 可以从其他包 storage 读取（版本兼容）
# but 不保证数据结构兼容——需文档化数据格式
```

## 最佳实践
1. 所有 storage 路径以 `namespace:` 开头
2. 暴露的函数通过标签而非文件名引用
3. UUID 分配统一管理或使用 namespace 前缀
4. 用空标签做事件插槽，为其他包提供扩展点
5. 在 `#load` 中检测冲突并告警
