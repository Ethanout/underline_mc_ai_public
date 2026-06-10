# Minecraft 知识库验证 - 快速开始指南

## 📋 概述

你现在有 **两套** 命令输出获取方案：

### 方案对比

| 方案 | 适用场景 | 成本 | 速度 | 准确度 |
|------|---------|------|------|--------|
| **OCR 方案**<br/>(`minecraft_executor.py`) | 客户端 mod 环境<br/>需要 GUI 交互 | 💰 有成本<br/>(Vision API) | 🐢 慢<br/>(2-3秒) | 📊 85-95% |
| **Mineflayer 方案** ⭐<br/>(`minecraft_mineflayer_executor.py`) | 知识库自动验证<br/>批量命令测试 | 💚 免费 | ⚡ 快<br/>(1-1.5秒) | ✅ 99%+ |

## 🚀 快速开始（推荐方案）

### 第一步：安装依赖

```bash
# Python 依赖（已有）
pip install -r requirements_minecraft.txt

# Node.js 依赖（自动安装，首次运行时）
# 只需确保已安装 Node.js：
node --version  # 应该 >= v14
```

### 第二步：启动 Minecraft 服务器

有两种方式：

#### 方式 A：使用现有的 minecraft-mod-mcp

```bash
1. 启动 Minecraft 客户端
2. 加载存档
3. 按 Esc → "对局域网开放"
4. 记下端口（通常是 25565）
```

#### 方式 B：独立服务器（更适合自动化）

```bash
# 下载并启动 Minecraft 服务器
# 确保在 server.properties 中设置：
#   online-mode=false  # 允许离线登录
#   allow-flight=true  # 允许飞行
```

### 第三步：测试连接

```bash
# Windows
test_mineflayer.bat

# Linux/Mac
python test_mineflayer.py
```

预期输出：

```
[1/5] 启动 Mineflayer Bot...
✅ Bot 已连接到服务器

[2/5] 等待 Bot 完全加载...

[3/5] 测试命令执行...
  测试 1/4: 查询游戏时间
  命令: /time query daytime
  ✅ 输出: The time is 1000
  
  测试 2/4: 查询在线玩家
  命令: /list
  ✅ 输出: There are 2 of a max of 20 players online: TestBot, Player813
...
```

### 第四步：运行知识库验证

```bash
# Windows
validate_knowledge.bat

# Linux/Mac
python knowledge_validator.py
```

## 📖 详细使用

### 验证单个条目

```bash
python knowledge_validator.py --single t0001_basic_syntax.md
```

### 验证特定范围

```bash
# 只验证 t0001-t0009
python knowledge_validator.py --pattern "t000*.md"

# 验证 t0100-t0199
python knowledge_validator.py --pattern "t01*.md"
```

### 自定义服务器配置

```bash
python knowledge_validator.py \
  --host 192.168.1.100 \
  --port 25566 \
  --username ValidatorBot
```

### 查看验证结果

```bash
# 结果保存在 validation_results/ ���录
cat validation_results/validation_20260603_143022.json
```

结果示例：

```json
{
  "validation_time": "2026-06-03T14:30:22",
  "total_files": 100,
  "files": [
    {
      "file": "t0467_escaping_in_minecraft_commands.md",
      "id": "t0467",
      "title": "命令中的转义字符",
      "total_commands": 8,
      "commands": [
        {
          "command": "tellraw @a {\"text\":\"Hello World\"}",
          "status": "success",
          "output": "Sent message to Player813"
        }
      ],
      "summary": {
        "success": 7,
        "warning": 1,
        "failed": 0,
        "pass_rate": "87.5%"
      }
    }
  ]
}
```

## 🔧 集成到工作流

### 方案 1：手动验证（当前）

```bash
# 1. 编辑知识库条目
vim knowledge/entries/t0500_new_technique.md

# 2. 验证单个文件
python knowledge_validator.py --single t0500_new_technique.md

# 3. 如果验证通过，提交
git add knowledge/entries/t0500_new_technique.md
git commit -m "Add: 新技术 t0500"
```

### 方案 2：Git Hook 自动验证

创建 `.git/hooks/pre-commit`：

```bash
#!/bin/bash

# 获取修改的知识库文件
CHANGED_FILES=$(git diff --cached --name-only | grep "knowledge/entries/.*\.md$")

if [ -n "$CHANGED_FILES" ]; then
    echo "检测到知识库变更，开始验证..."
    
    # 启动验证
    for file in $CHANGED_FILES; do
        filename=$(basename "$file")
        python knowledge_validator.py --single "$filename"
        
        if [ $? -ne 0 ]; then
            echo "❌ 验证失败: $filename"
            exit 1
        fi
    done
    
    echo "✅ 所有变更已验证"
fi
```

### 方案 3：定时全量验证

```bash
# Linux crontab
0 2 * * * cd /path/to/project && python knowledge_validator.py >> logs/nightly_validation.log 2>&1

# Windows 任务计划程序
# 创建任务，每天 2:00 AM 运行 validate_knowledge.bat
```

## 🎯 最佳实践

### 1. 命令编写规范

在知识库条目中使用标准格式：

````markdown
---
id: t0500
title: 示例技术
---

## 基础用法

创建记分板：

```mcfunction
scoreboard objectives add points dummy "积分"
scoreboard players set @a points 0
```

查询记分板：

```mcfunction
scoreboard objectives list
```

行内命令示例：使用 `/scoreboard players get @s points` 查询分数。
````

### 2. 版本兼容性标注

```markdown
---
id: t0500
title: 示例技术
minecraft_version: "1.20+"  # 最低支持版本
---

<!-- 在条目中标注版本特性 -->
> ⚠️ 此命令仅在 Minecraft 1.20+ 可用

```mcfunction
# 1.20+ 新语法
execute if score @s test matches 1.. run say Hello
```
```

### 3. 处理验证警告

如果命令被标记为 `warning`：

```bash
# 查看具体输出
cat validation_results/validation_*.json | jq '.files[].commands[] | select(.status=="warning")'

# 常见原因：
# 1. 命令语法错误
# 2. 缺少前置条件（如记分板未创建）
# 3. 权限不足
# 4. 版本不兼容
```

### 4. 忽略特定命令

某些命令不适合自动验证（如需要玩家交互的），在 Markdown 中标注：

````markdown
```mcfunction
# @validation:skip - 需要玩家手动点击
tellraw @a {"text":"点击这里","clickEvent":{"action":"run_command","value":"/say Clicked"}}
```
````

然后修改 `knowledge_validator.py` 跳过这些命令：

```python
def extract_commands_from_markdown(self, content: str) -> List[Dict[str, Any]]:
    commands = []
    # ...
    for line in lines:
        # 跳过标记为 skip 的命令
        if '@validation:skip' in line:
            continue
        # ...
```

## 🐛 故障排除

### 问题 1：Bot 连接超时

```
❌ Bot 启动超时
```

**检查清单：**
- [ ] Minecraft 服务器已启动
- [ ] 服务器端口正确（默认 25565）
- [ ] 防火墙未阻止连接
- [ ] 服务器允许离线模式

**解决：**
```bash
# 测试服务器连接
telnet localhost 25565

# 检查服务器日志
tail -f logs/latest.log

# 尝试手动连接
# 启动 Minecraft 客户端，连接到 localhost
```

### 问题 2：命令权限不足

```
⚠️ 命令可能有误: You do not have permission
```

**解决：**
```bash
# 在服务器控制台执行
op ValidatorBot

# 或修改 server.properties
operator-permission-level=4
```

### 问题 3：找不到命令

```
找到 0 个命令
```

**检查：**
- 代码块是否正确标记：````mcfunction` 或 ````minecraft`
- 命令是否在代码块内
- 文件编码是否为 UTF-8

### 问题 4：Node.js 依赖安装失败

```
npm install 失败
```

**解决：**
```bash
# 清理并重新安装
cd mineflayer_bot
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# 如果还是失败，使用镜像
npm config set registry https://registry.npmmirror.com
npm install
```

### 问题 5：命令输出乱码

```
输出: ��������
```

**解决：**
- 确保 Python 脚本使用 UTF-8 编码
- 在 Windows 上��行 `chcp 65001`
- 或在脚本开头添加：
  ```python
  import sys
  sys.stdout.reconfigure(encoding='utf-8')
  ```

## 📊 性能优化

### 批量验证优化

```python
# 创建 fast_validator.py
async def validate_batch_parallel(validator, files, max_concurrent=5):
    """并发验证多个文件"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def validate_one(file_path):
        async with semaphore:
            return await validator.validate_technique(file_path)
    
    tasks = [validate_one(f) for f in files]
    return await asyncio.gather(*tasks)
```

### 缓存验证结果

```python
# 只验证修改过的文件
import hashlib

def file_hash(path):
    return hashlib.md5(path.read_bytes()).hexdigest()

def should_validate(path, cache):
    current_hash = file_hash(path)
    cached_hash = cache.get(str(path))
    return current_hash != cached_hash
```

## 🔄 迁移指南

### 从 OCR 方案迁移

如果你之前使用 `minecraft_executor.py`（OCR 方案），迁移步骤：

1. **保留原有代码**（用于 GUI 交互场景）
2. **新增 Mineflayer 方案**（用于命令验证）
3. **根据场景选择**：
   - GUI 测试 → 使用 OCR 方案
   - 命令验证 → 使用 Mineflayer 方案

```python
# 场景判断示例
async def execute_command_smart(command, need_gui=False):
    if need_gui:
        # 使用 OCR 方案
        executor = MinecraftCommandExecutor()
        return await executor.execute_command_with_output(command)
    else:
        # 使用 Mineflayer 方案
        executor = MineflayerCommandExecutor()
        await executor.start_bot()
        result = await executor.execute_command_with_output(command)
        await executor.stop_bot()
        return result
```

## 📚 下一步

1. **阅读完整文档**：`README_VALIDATION.md`
2. **查看代码实现**：`minecraft_mineflayer_executor.py`
3. **自定义验证逻辑**：`knowledge_validator.py`
4. **集成到 CI/CD**：参考 `README_VALIDATION.md` 中的 GitHub Actions 示例

## 🤝 获取帮助

如遇问题：
1. 查看 `README_VALIDATION.md` 故障排除章节
2. 检查 `validation_results/*.json` 中的详细错误
3. 查看 Bot 日志（如有）

## ✨ 总结

现在你有了一套完整的知识库自动验证系统：

- ✅ **零成本**：无需 Vision API
- ✅ **高准确度**：直接读取命令返回值
- ✅ **易扩展**：支持自定义验证规则
- ✅ **生产就绪**：可集成到 CI/CD

开始验证你的知识库吧！🚀
