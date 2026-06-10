# `execute store` 模式与 mecha 验证

## `execute store result ... run execute if entity` ❌ 不要用

```mcfunction
execute store result score #count pvp.data run execute if entity @a[tag=init]
```

**问题**: 嵌套的 `run execute` 会导致大部分解析器（mecha、Spyglass）误判——它们会把下一行当作这个 execute 链的延续，而不是新命令。

**等价写法**（删掉 `run execute`，直接 `if`）：

```mcfunction
execute store result score #count pvp.data if entity @a[tag=init]
```

这样 execute 链直接以 `if entity` 结尾，`store result` 捕获匹配实体数量，整条命令一行结束。

## `execute if score X <op> Y` vs `matches`

虽然 `>=`、`<`、`=` 等运算符在 Minecraft 中有效，但 `matches` 更安全、更统一：

```mcfunction
execute if score #count pvp.data matches 0..1 run ...   // 0人或者1人
execute if score #count pvp.data matches 2.. run ...     // 2人及以上
execute if score #count pvp.data matches 10 run ...      // 恰好10人
```

`matches` 在 mecha/Spyglass 中兼容性更好，且语义更清晰。

## `data modify` 必须指定 NBT 路径

```mcfunction
data modify storage pvp:config set value {spawns:{...}}    // ❌ 缺少路径
data merge storage pvp:config {spawns:{...}}                // ✅ 初始化用 merge
data modify storage pvp:config Config set value {spawns:{...}}  // ✅ 有路径
```

`data modify` 格式：`data modify <来源> <路径> <动作> <值>`，`<路径>` 不可省略。初始化 storage 推荐用 `data merge`，修改特定路径用 `data modify`。

## `give` 物品组件建议写在一行

Minecraft 1.21.4 支持多行组件语法：

```mcfunction
give @s minecraft:stick[custom_name={"text":"Test"}]
```

但多行写法会导致 mecha 解析失败：

```mcfunction
give @s minecraft:stick[          // ← mecha 报错
  custom_name={"text":"Test"}
]
```

建议组件较少时写在一行，或用 `item replace` 替代。

## 用 mecha 做本地验证

```bash
pip install mecha
mecha -m <版本> <数据包路径>
```

示例：
```bash
mecha -m "1.21" ./pvp_arena
```

mecha 基于 beet 生态，能捕获语法错误、命令结构错误、组件拼写错误等。建议每次开发后运行一次，作为 CI 前置检查。
