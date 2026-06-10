# Beet 数据包 Skill

指导 AI 使用 beet 生成/管理 Minecraft 数据包，特别是用于自动验证的临时测试数据包。

---

## 1. 项目结构

```
data/temp_datapacks/       ← 自动生成的临时测试数据包（gitignore 建议加上）
  test_<technique_id>/     ← 每个测试一个目录
    pack.mcmeta
    data/<namespace>/
      function/
        test_<id>.mcfunction
  ...

验证用的数据包命名空间建议用 `test_<id>`，避免冲突。
```

## 2. Beet 配置 (pyproject.toml)

```toml
[tool.beet]
require = ["bolt"]
data_pack = { load = ["data/temp_datapacks/test_XXX"] }
pipeline = ["mecha"]
output = "data/temp_datapacks"

[tool.beet.meta.bolt]
entrypoint = ["test:module"]

[tool.beet.meta.generate_namespace] = "test"
```

## 3. Beet Python API

### 3.1 DataPack

```python
from beet import DataPack, Function, FunctionTag

dp = DataPack(pack_format=71, description="Test datapack")

# 添加函数（用命名空间:路径）
dp["test:hello"] = Function(["say hello", "say world"])

# 添加函数并打标签
dp["test:hello"] = Function(["say hello"], tags=["minecraft:load"])

# 添加标准标签
dp.zog("data/minecraft/tags/functions")["tick"] = FunctionTag(["test:tick"])

# 保存到目录
dp.save("data/temp_datapacks/test_001/")

# 保存为 zip
dp.save("data/temp_datapacks/test_001.zip")
```

### 3.2 Context & Plugin

```python
from beet import Context, Function

def my_plugin(ctx: Context):
    ctx.data["test:run"] = Function(["say running..."], tags=["minecraft:load"])
```

### 3.3 pack.mcmeta

```python
from beet import DataPack

dp = DataPack(pack_format=71, description="Test datapack")
# pack_format 71 = Minecraft 1.21.5, 81 = 1.21.7
```

### 3.4 Tags

```python
from beet import FunctionTag

# 给标签添加值
tag = FunctionTag()
tag.append("test:my_func")

# 或者直接在添加函数时指定
dp["test:run"] = Function(["say hi"], tags=["minecraft:load"])
```

## 4. Bolt 模板语言

Bolt 是嵌入在 mcfunction/json 中的 Python 模板语言。文件以 `--` 前缀命名。

```
src/data/mg/function/--listener.mcfunction
```

```bolt
from mg:generic import run_mainhand_data_command

$foo = "bar"

#item:
    function my_func
```

Bolt 入口在 beet.json / pyproject.toml 的 `meta.bolt.entrypoint` 配置：
```toml
[tool.beet.meta.bolt]
entrypoint = ["test:module"]
```

## 5. Link 系统

### 关键命令（只需一个 --data-pack 参数）

```bash
# 1. 链接到世界的数据包目录
beet link --data-pack "D:\path\to\world\datapacks"
# → 自动推导: world = 上一级, minecraft = saves/的上级, resource_pack = minecraft/resourcepacks
# → 配置保存到 .beet_cache/link/index.json
```

### 用户存档路径（AI 需要先问用户）

AI **必须**先问用户 Minecraft 存档的数据包目录路径，不能猜。例如：
```
你的存档路径是什么？
比如: C:\Users\xxx\AppData\Roaming\.minecraft\saves\我的世界\datapacks
```
拿到路径后再执行 `beet link --data-pack "用户路径"`。

此路径可以存进 `modules/config.py`，例如：
```python
MINECRAFT_SAVES_DIR = Path(r"C:\Users\xxx\AppData\Roaming\.minecraft\versions\1.21.11-Fabric 0.18.4\saves")
```
然后用 `MINECRAFT_SAVES_DIR / "我的世界" / "datapacks"` 构造完整路径。

# 2. 构建并自动 link（记住上次的 link 配置）
beet build

# 3. 构建 + 一步到位 link
beet build -l "世界名称"

# 4. 清除 link
beet link -c

# 5. 文件变更自动构建 + link
beet watch --link "世界名称"
```

### Windows 注意事项

- 路径含中文时，`--minecraft` 和 `--resource-pack` 参数可能有编码问题
- **只传 `--data-pack` 就够了**，其他路径会自动推导
- 推导链：`--data-pack DIR` → `world = DIR.parent` → `minecraft = world.parent.parent` → `resource_pack = minecraft/resourcepacks`

## 6. 自动验证测试数据包模式

典型的验证用临时数据包结构：

```python
from beet import DataPack, Function

def make_test_datapack(technique_id: str, setup_commands: list[str],
                        verify_commands: list[str]) -> DataPack:
    dp = DataPack(pack_format=71, description=f"Test: {technique_id}")

    # 设置：初始化测试环境
    dp[f"test:{technique_id}/setup"] = Function(setup_commands)

    # 验证：执行测试并存储结果到 storage
    verify = verify_commands + [
        'data modify storage test:result result set value "passed"',
        'scoreboard players set #status ok 1',
    ]
    dp[f"test:{technique_id}/verify"] = Function(verify)

    # 入口函数
    dp[f"test:{technique_id}"] = Function([
        f"function test:{technique_id}/setup",
        f"function test:{technique_id}/verify",
        'say Test complete. Check storage test:result',
    ])

    # 自动加载（可选）
    dp.zog("data/minecraft/tags/functions")["load"] = FunctionTag([f"test:{technique_id}"])

    return dp
```

### 验证流程

1. `make_test_datapack("id", setup_cmds, verify_cmds)` → 生成数据包到 `data/temp_datapacks/test_id/`
2. 通过 mineflayer 用 `/reload` 加载，然后 `/function test:id`
3. 用 `data get storage test:result result` 读取结果
4. 清理 `data/temp_datapacks/test_id/`

## 7. 已知问题

- `beet link --minecraft` / `--resource-pack` 在 Windows 上有中文路径编码问题，只传 `--data-pack`
- beet 需要 `[tool.beet]` 节配置才能运行 CLI 命令（`beet build` 等），但 Python API (`from beet import DataPack`) 不需要
- 临时数据包用完记得删除，否则会堆积在 `data/temp_datapacks/`
- `pack_format` 版本: 71=1.21.5, 81=1.21.7, 86=1.21.9
