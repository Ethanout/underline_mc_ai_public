# Minecraft 命令执行器 - 使用说明

## 功能概述

这是一个增强版的 Minecraft MCP 服务器，集成了 `minecraft-mod-mcp` 和 SiliconFlow PaddleOCR-VL API，提供以下功能：

- ✅ 执行 Minecraft 命令
- ✅ **通过视觉识别获取命令输出**（核心功能）
- ✅ 获取玩家/世界信息
- ✅ 截图功能

## 前置要求

### 1. 安装依赖

```bash
pip install -r requirements_minecraft.txt
```

### 2. 设置环境变量

```bash
# Windows PowerShell
$env:SILICONFLOW_API_KEY = "your-api-key-here"

# Linux/Mac
export SILICONFLOW_API_KEY="your-api-key-here"
```

### 3. 启动 Minecraft

1. 确保已安装 `minecraft-mod-mcp` mod
2. 启动 Minecraft 客户端
3. 进入单人世界
4. 按 ESC → 点击 "对局域网开放" (Open to LAN)
5. 确保 mod 的 HTTP 服务器正在运行（默认端口 9876）

## 使用方式

### 方式 1: 在 OpenCode 中使用

配置已经完成，直接在 OpenCode 中调用工具：

```
请帮我查询 Minecraft 中的游戏时间
```

OpenCode 会自动调用 `execute_minecraft_command_with_output` 工具。

### 方式 2: 直接运行测试

```bash
python test_minecraft.py
```

### 方式 3: 在代码中使用

```python
import asyncio
from minecraft_executor import MinecraftCommandExecutor

async def main():
    executor = MinecraftCommandExecutor()
    
    # 执行命令并获取输出
    result = await executor.execute_command_with_output("time query daytime")
    print(f"输出: {result['output']}")
    
    # 获取玩家信息
    info = await executor.get_player_info()
    print(info)

asyncio.run(main())
```

## 可用工具

### 1. `execute_minecraft_command`
执行命令（不获取输出，速度快）

```python
await executor.execute_command("time set day")
```

### 2. `execute_minecraft_command_with_output` ⭐
执行命令并通过视觉识别获取输出（推荐）

```python
result = await executor.execute_command_with_output("time query daytime")
print(result['output'])  # 例如: "The time is 1000"
```

**参数：**
- `command`: 要执行的命令（可以带或不带 `/`）
- `wait_seconds`: 等待时间（默认 0.4 秒），调整以适应不同命令的响应速度

### 3. `get_player_info`
获取玩家信息（位置、生命值、维度等）

```python
info = await executor.get_player_info()
```

### 4. `get_world_info`
获取世界信息（时间、天气等）

```python
info = await executor.get_world_info()
```

### 5. `take_screenshot`
截图

```python
result = await executor.take_screenshot(save_to_file=True)
print(result['path'])
```

## 工作原理

命令输出识别流程：

```
1. 执行命令 → minecraft-mod-mcp HTTP API
   POST http://127.0.0.1:9876/api/cmd
   {"method": "execute_command", "params": {"command": "..."}}

2. 等待 0.4 秒 → 让输出显示在聊天栏

3. 截图 → 保存到 minecraft_screenshots/
   POST http://127.0.0.1:9876/api/cmd
   {"method": "screenshot_to_file", "params": {"path": "..."}}

4. 视觉识别 → SiliconFlow PaddleOCR-VL API
   读取截图中聊天栏的文字内容

5. 返回输出文本
```

## 成本估算

- SiliconFlow PaddleOCR-VL-1.5：**免费或极低成本**
- 比 Claude Vision 成本低得多
- 适合高频调用

## 故障排除

### 问题 1: 连接被拒绝
```
Error: Mod API call failed: Connection refused
```

**解决：**
- 确保 Minecraft 客户端已启动
- 确保已经 Open to LAN
- 检查 mod 是否正常加载（按 ESC 应该能看到 "MCP Take Over" 按钮）

### 问题 2: 截图文件未创建
```
Error: Screenshot file not created
```

**解决：**
- 检查 `minecraft_screenshots/` 目录权限
- 尝试手动创建该目录

### 问题 3: 视觉识别不准确
```
Output: [无输出]
```

**解决：**
- 增加 `wait_seconds` 参数（某些命令需要更长时间）
- 检查截图文件，确认聊天栏是否可见
- 调整游戏窗口大小，确保聊天栏在屏幕左下角

### 问题 4: API 密钥错误
```
Error: Invalid API key
```

**解决：**
- 检查环境变量 `SILICONFLOW_API_KEY` 是否正确设置
- 或在代码中直接传入：
  ```python
  executor = MinecraftCommandExecutor(siliconflow_api_key="your-key")
  ```

## 示例场景

### 场景 1: 查询游戏时间
```python
result = await executor.execute_command_with_output("time query daytime")
# 输出: "The time is 1000"
```

### 场景 2: 查询在线玩家
```python
result = await executor.execute_command_with_output("list")
# 输出: "There are 1/8 players online: Player813"
```

### 场景 3: 查询天气
```python
result = await executor.execute_command_with_output("weather query")
# 输出: "It is currently clear"
```

### 场景 4: 传送玩家
```python
# 先执行传送
await executor.execute_command("tp @s 0 100 0")
# 再获取新位置
info = await executor.get_player_info()
print(f"新位置: {info['data']['x']}, {info['data']['y']}, {info['data']['z']}")
```

## 文件结构

```
underline_mc_ai/
├── minecraft_executor.py          # 核心执行器类
├── minecraft_mcp_server.py        # MCP 服务器包装器
├── test_minecraft.py              # 测试脚本
├── requirements_minecraft.txt     # 依赖配置
├── README_MINECRAFT.md            # 本文档
├── opencode.json                  # OpenCode 配置
└── minecraft_screenshots/         # 截图保存目录（自动创建）
```

## 进阶使用

### 自定义等待时间

对于响应较慢的命令：

```python
# 数据包重载可能需要更长时间
result = await executor.execute_command_with_output(
    "reload",
    wait_seconds=1.0
)
```

### 批量执行命令

```python
commands = ["time set day", "weather clear", "difficulty peaceful"]
for cmd in commands:
    await executor.execute_command(cmd)
    await asyncio.sleep(0.1)
```

### 错误处理

```python
result = await executor.execute_command_with_output("invalid_command")
if not result["success"]:
    print(f"命令执行失败: {result['error']}")
elif "[无输出]" in result["output"]:
    print("命令可能无效或没有返回信息")
else:
    print(f"成功: {result['output']}")
```

## 注意事项

1. **成本控制**：每次调用 `execute_command_with_output` 都会使用 Vision API，有一定成本
2. **性能**：视觉识别需要 1-2 秒，不适合高频调用
3. **准确性**：依赖聊天栏文字清晰度，建议使用默认 GUI 比例
4. **权限**：某些命令需要管理员权限或作弊模式

## 贡献

如有问题或建议，欢迎提交 Issue。
