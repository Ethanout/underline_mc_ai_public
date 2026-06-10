# 知识来源抓取

当前主要来源：

- `datapack.wiki`：通过公开 sitemap 抓取全部内容页面
- `Minecraft Commands Questions`：抓取 FAQ 索引下的全部问题页面
- 手动非结构化数据：原样导入 `data/inbox/*.md`
- `r/MinecraftCommands`：作为补充问答来源

## 抓取主要来源

```powershell
python -m modules.crawlers.knowledge_sources --source all
```

也可以单独运行：

```powershell
python -m modules.crawlers.knowledge_sources --source datapack_wiki
python -m modules.crawlers.knowledge_sources --source mcc_questions
python -m modules.crawlers.knowledge_sources --source manual
```

输出文件：

```text
data/sources/raw/datapack_wiki.json
data/sources/raw/mcc_questions.json
data/sources/raw/manual_notes.json
```

手动内容无需预先结构化。可以通过 Web UI 的“收件箱”输入，也可以直接在
`data/inbox/` 中创建 UTF-8 Markdown 文件。处理后的文件可移动到
`data/archive/inbox/`；导入器会同时读取 inbox 与归档，并保留外部文本导入记录。

聊天导出或其他临时文本文件也可以直接导入，不需要先移动文件：

```powershell
python -m modules.crawlers.knowledge_sources --source manual --manual-file "C:\path\notes.txt"
```

推荐处理流程：

1. 原文进入 `data/inbox/`，或通过 `--manual-file` 归档。
2. 只把有明确机制、命令或可验证结论的内容拆成 technique。
3. 工具链接、项目发布和前置库整理进 `data/knowledge/reference/`，不强行生成 technique。
4. 缺少实现细节的发现标记为 `confidence: low`，并写清验证缺口。
5. 游戏内验证完成后再设置 `verified_in_game: true`。
