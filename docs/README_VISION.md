# Minecraft 截图视觉分析工具

使用 GLM-4.5V 等视觉模型分析 Minecraft 游戏截图，识别地面图案、建筑结构、红石电路等内容。

## 功能特性

- ✅ 支持任何兼容 OpenAI API 格式的视觉模型
- ✅ 自动编码图片为 base64
- ✅ 自定义分析提示词
- ✅ 支持 JSON 格式输出
- ✅ 环境变量配置

## 快速开始

### 1. 安装依赖

```bash
pip install requests
```

### 2. 配置环境变量

```bash
# Windows PowerShell
$env:Z_AI_API_KEY="your-api-key-here"
$env:Z_AI_BASE_URL="https://api.siliconflow.cn/v1/"
$env:Z_AI_VISION_MODEL="Pro/THUDM/glm-4v-flash"

# Linux/Mac
export Z_AI_API_KEY="your-api-key-here"
export Z_AI_BASE_URL="https://api.siliconflow.cn/v1/"
export Z_AI_VISION_MODEL="Pro/THUDM/glm-4v-flash"
```

### 3. 分析截图

```bash
# 基础用法
python vision_analyzer.py mc_screenshot.png

# 自定义提示词
python vision_analyzer.py mc_screenshot.png -p "识别地面上的文字图案"

# JSON 格式输出
python vision_analyzer.py mc_screenshot.png --json
```

## 使用示例

### 示例 1: 识别地面图案

```bash
python vision_analyzer.py C:/Users/26297/AppData/Local/Temp/opencode/mc_pattern.png \
  -p "请描述地面上用方块拼出的文字或图案，说明使用了什么颜色的方块"
```

**输出示例**：
```
=== 图片分析结果 ===
文件: C:/Users/26297/AppData/Local/Temp/opencode/mc_pattern.png
模型: Pro/THUDM/glm-4v-flash

截图显示地面用深绿色方块（可能是苔藓石或绿色混凝土）在灰色石砖地面上拼出了 "Hi" 字样。
字母 H 由两个竖条和一个横条组成，字母 i 由上方一个点和下方一个竖条组成。
```

### 示例 2: 分析红石电路

```bash
python vision_analyzer.py redstone_circuit.png \
  -p "分析这个红石电路的逻辑结构和功能"
```

### 示例 3: 识别 UI 界面

```bash
python vision_analyzer.py inventory.png \
  -p "列出背包中的所有物品及其数量"
```

### 示例 4: JSON 输出（用于脚本集成）

```bash
python vision_analyzer.py screenshot.png --json > result.json
```

## 命令行参数

```
位置参数:
  image                 截图文件路径

可选参数:
  -h, --help            显示帮助信息
  -p, --prompt PROMPT   分析提示词
  -m, --model MODEL     视觉模型名称（覆盖环境变量）
  -k, --api-key KEY     API Key（覆盖环境变量）
  -u, --base-url URL    API Base URL（覆盖环境变量）
  --max-tokens N        最���生成 token 数（默认 2000）
  --json                以 JSON 格式输出
```

## 支持的模型

只要是兼容 OpenAI Vision API 格式的模型都可以使用，例如：

| 提供商 | 模型名称 | 说明 |
|--------|----------|------|
| SiliconFlow | `Pro/THUDM/glm-4v-flash` | GLM-4V Flash（快速） |
| SiliconFlow | `Pro/THUDM/glm-4v-plus` | GLM-4V Plus（高质量） |
| OpenAI | `gpt-4-vision-preview` | GPT-4 Vision |
| OpenAI | `gpt-4o` | GPT-4o（多模态） |

## 集成到工作流

### 方法 1: PowerShell 脚本

```powershell
# analyze_mc_screenshot.ps1
$env:Z_AI_API_KEY="your-key"
$env:Z_AI_BASE_URL="https://api.siliconflow.cn/v1/"

# 截图并分析
$screenshot = "C:/Users/26297/AppData/Local/Temp/opencode/mc_latest.png"
python vision_analyzer.py $screenshot -p "分析 Minecraft 截图内容"
```

### 方法 2: Python 模块调用

```python
from vision_analyzer import VisionAnalyzer

analyzer = VisionAnalyzer(
    api_key="your-key",
    base_url="https://api.siliconflow.cn/v1/",
    model="Pro/THUDM/glm-4v-flash"
)

result = analyzer.analyze_image(
    image_path="screenshot.png",
    prompt="识别地面图案"
)

print(result)
```

### 方法 3: 与 minecraft-mod-mcp 联动

```python
# 1. 使用 minecraft-mod MCP 截图
# minecraft-mod_screenshot_to_file(path="temp.png")

# 2. 分析截图
import subprocess
result = subprocess.run(
    ["python", "vision_analyzer.py", "temp.png", "--json"],
    capture_output=True,
    text=True
)
analysis = json.loads(result.stdout)
print(analysis["result"])
```

## 常见问题

### Q: 为什么不直接用 zai-mcp-server？

A: `zai-mcp-server` 需要通过 MCP 协议调用，需要 opencode 的内部路由。这个独立脚本可以：
- 在命令行直接运行
- 集成到其他 Python 脚本
- 用于自动化测试
- 调试视觉模型输出

### Q: 支持哪些图片格式？

A: PNG、JPG、JPEG、WEBP 等常见格式都支持（取决于视觉模型）

### Q: 如何提高识别准确度？

1. 使用更清晰的提示词，明确要识别的内容
2. 截图时确保目标清晰可见
3. 使用更强的模型（如 glm-4v-plus）
4. 增加 `--max-tokens` 参数获取更详细的分析

### Q: API 调用失败怎么办？

检查：
1. API Key 是否正确
2. Base URL 是否正确（必须包含 `/v1/`）
3. 网络连接是否正常
4. 模型名称是否正确

## 许可证

MIT License
