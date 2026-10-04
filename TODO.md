# 当前待办

更新：2026-10-05。

## 工作区迁移

- [x] 归档旧知识控制台、Chroma RAG、爬取管线、验证器和生成数据。
- [x] 等待独立提取任务完成，再归档旧 `knowledge/`。
- [x] 检查 `../underline_wiki/` 中 43 份提取文档的原文哈希。
- [x] 将根启动器改为 QQ 采集器，移除旧运行依赖。

## Collector 实现

- [x] 接入 NapCat 事件、持久任务、群会话和工具权限。
- [x] 接入 DeepSeek 与 LangGraph，检查所选模型能力。
- [x] 实现群精华同步、消息读取与自动整理。
- [ ] 将查询接入 `../underline_wiki/`，不恢复旧 Chroma 数据库。
- [x] 群聊人格、记忆和情绪改由 MaiBot 负责；旧实现归档在 `apps/qqbot/archive/persona/`。
- [ ] 在真机上装好 MaiBot、NapCat 适配器和 underline_tools 插件，试 `/毯` 和插件查询。

新 wiki 的桌面程序、HTTP API 或 MCP 接入仍待实现。提取任务保留了人工来源文档，但没有找到游戏验证为真的标记。
