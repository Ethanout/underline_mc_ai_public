# Minecraft 数据包知识库管理系统

> 用于管理、验证和查询 Minecraft 数据包相关技术知识

## 快速开始

### 1. 启动 Web UI

```bash
start_ui.bat
```

访问 http://localhost:8000

### 2. 验证知识库（可选）

```bash
cd scripts\validation
validate_knowledge.bat
```

## 项目结构

```
underline_mc_ai/
├── README.md                    # 本文件
├── app.py                       # Web UI 后端
├── start_ui.bat                 # 启动工具
├── opencode.json                # MCP 配置
├── requirements_minecraft.txt   # 依赖
│
├── knowledge/                   # 知识库 ⭐
│   ├── entries/                # 技术条目（tXXXX.md）
│   ├── best_practices/         # 最佳实践
│   ├── reference/              # 参考资料
│   └── rag_chroma_db/          # RAG 向量数据库
│
├── inbox/                       # 待处理条目
├── trash/                       # 已删除条目
│
├── scripts/                     # 功能脚本 ⭐
│   ├── validation/             # 命令验证系统
│   ├── ocr_backup/             # OCR 方案（备用）
│   ├── build_rag_index.py      # 构建索引
│   ├── audit_quality.py        # 质量审计
│   ├── dedup_entries.py        # 去重
│   └── ...                     # 其他维护脚本
│
├── sources/                     # 数据源
│   ├── datapack-wiki/
│   ├── mcf-skill/
│   └── raw/
│
├── static/                      # Web UI 静态文件
├── api/                         # API 密钥
└── docs/                        # 详细文档
```

## 主要功能

### 📖 知识库管理（Web UI）

```bash
start_ui.bat
```

- 浏览和��索技术条目
- 编辑和管理条目
- 审核待处理内容

### ✅ 命令验证

```bash
cd scripts\validation
validate_knowledge.bat
```

自动验证知识库中的 Minecraft 命令是否有效

详见：`scripts/validation/README.md`

### 🔧 维护工具

```bash
cd scripts

# 构建索引
python build_rag_index.py

# 质量审计
python audit_quality.py

# 去重条目
python dedup_entries.py
```

详见：`scripts/README.md`

## 知识库条目格式

```markdown
---
id: t0001
title: 技术标题
category: 分类
tags: [tag1, tag2]
difficulty: beginner|intermediate|advanced
version: "1.20+"
---

## 描述

技术说明...

## 示例

```mcfunction
# 命令示例
scoreboard objectives add test dummy
```

## 注意事项

...
```

## 工作流程

```
数据源 → 爬取 → inbox/ → 审核 → knowledge/entries/
                                        ↓
                                    构建索引
                                        ↓
                                  rag_chroma_db/
                                        ↓
                                    验证命令
                                        ↓
                                  validation_results/
```

## 安装依赖

```bash
pip install -r requirements_minecraft.txt
```

## 文档索引

- **项目总览** - 本文件
- **脚本工具** - `scripts/README.md`
- **命令验证** - `scripts/validation/README.md`
- **详细文档** - `docs/` 目录

## 开发

### 添加新条目

1. 使用 Web UI 添加到 inbox/
2. 审核后移动到 knowledge/entries/
3. 运行索引构建：`python scripts/build_rag_index.py`
4. 运行验证：`cd scripts/validation && python knowledge_validator.py`

### 维护知识库

```bash
# 质量检查
cd scripts
python audit_quality.py

# 去重
python dedup_entries.py

# 重建索引
python build_rag_index.py
```

## 常见问题

**Q: Web UI 无法启动？**
```bash
pip install fastapi uvicorn
```

**Q: 验证器无法连接？**
- 确保 Minecraft 服务器已启动
- 查看 `scripts/validation/README.md`

**Q: 如何备份知识库？**
```bash
# 备份 knowledge/ 目录
tar -czf knowledge_backup.tar.gz knowledge/
```
