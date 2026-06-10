# 项目清理建议

## 📂 当前项目结构分析

### 核心功能文件（保留）

**Mineflayer 方案（主力）：**
- ✅ `minecraft_mineflayer_executor.py` - 核心执行器
- ✅ `minecraft_mineflayer_mcp.py` - MCP 服务器
- ✅ `knowledge_validator.py` - 知识库验证器
- ✅ `test_mineflayer.py` - 测试脚本
- ✅ `test_mineflayer.bat` - Windows 工具
- ✅ `validate_knowledge.bat` - Windows 工具

**OCR 方案（备用）：**
- ✅ `minecraft_executor.py` - OCR 执行器
- ✅ `minecraft_mcp_server.py` - OCR MCP 服务器
- ✅ `test_minecraft.py` - OCR 测试
- ✅ `test_minecraft.bat` - OCR Windows 工具

**配置和依赖：**
- ✅ `opencode.json` - MCP 配置
- ✅ `requirements_minecraft.txt` - Python 依赖
- ✅ `api/siliconflow.txt` - API Key

**知识库：**
- ✅ `knowledge/` - 知识库目录

**核心应用：**
- ✅ `app.py` - 主应用
- ✅ `start_ui.bat` - 启动脚本

### 可以清理的文件

**文档（太多重复）：**
- 🗑️ `COMPARISON_GUIDE.md` - 可以合并
- 🗑️ `IMPLEMENTATION_COMPLETE.md` - 可以合并
- 🗑️ `INTEGRATION_SUMMARY.md` - 可以合并
- 🗑️ `QUICKSTART_VALIDATION.md` - 可以合并
- 🗑️ `SOLUTION_SUMMARY.md` - 可以合并
- ✅ `README_VALIDATION.md` - 保留（主文档）
- ✅ `README_MINECRAFT.md` - 保留（OCR 文档）

**临时文件：**
- 🗑️ `test_mock.py` - 模拟测试，不需要
- 🗑️ `build.log` - 构建日志
- 🗑️ `build.err.log` - 错误日志
- 🗑️ `变量与数据.md` - 临时笔记

**生成的目录：**
- 🗑️ `__pycache__/` - Python 缓存
- ⚠️ `mineflayer_bot/node_modules/` - 依赖（很大，但需要）
- 🗑️ `minecraft_screenshots/` - 旧截图（可清理）

## 清理方案

我建议：
1. 合并文档为 1-2 个主文档
2. 移动不需要的文件到 `trash/`
3. 删除临时文件

要我执行清理吗？
