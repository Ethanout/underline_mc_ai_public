# 项目 TODO

最后核对：2026-06-06

状态说明：

- `[x]` 已由客观文件状态或实际运行结果确认，不依赖“代码看起来已实现”的推断
- `[~]` 已有代码、配置、文档或局部产物，但尚未完成端到端验证或仍有明显缺口
- `[ ]` 尚未实现

## 根目录 / Web UI

涉及：`app.py`、`static/`、`start_ui.bat`

- [~] Web UI 已实现 inbox、techniques、trash、query、config 管理界面和 CRUD 请求，但尚未完成系统性回归测试
- [~] `app.py` 已接入 dispatcher，可启动任务、查询状态和发送取消信号；取消仍依赖任务主动响应
- [~] 已提供爬取/提取、验证、RAG 重建、RAG 查询 API，但部分后端流程尚未实际跑通
- [~] `app.py` 已明显瘦身，但仍保留较多文件读写和业务逻辑，尚未完全拆入模块
- [ ] 增加流式查询接口 `/api/query/stream`
- [ ] 增加 Dashboard，展示任务状态和知识库统计

## `modules/config.py` / 路径配置

- [x] 使用 `PROJECT_ROOT` 统一主要目录常量
- [~] 已统一 `app.py`、爬取流程和 RAG 数据库等主要路径，但尚未对全部入口做端到端路径验证
- [x] 增加 `TEMP_DATAPACKS_DIR`
- [x] 已消除 `modules/` 和 `app.py` 中的 `parent.parent...` 固定层级路径计算

## `modules/dispatcher.py` / 任务调度

- [~] 已实现同步和异步后台任务启动代码，尚无自动化测试
- [~] 已实现任务状态、结果、错误和取消信号；进度和日志尚未真正接入任务执行过程
- [~] 已接入 Web API，但尚未完成完整任务生命周期实测
- [~] 只有主要长任务接入取消信号，尚未覆盖所有模块

## `modules/crawlers/` / 数据爬取与旧提取流程

- [~] r/MinecraftCommands 抓取器已实测抓取 Java Help 帖子、分页获取可用评论、重建回复树并增量去重；公开归档可能缺失评论，且待扩大抓取并评估内容质量
- [~] Minecraft Wiki 爬虫已有深度链接扩展和版本日志过滤代码，但尚未重新做端到端抓取验证
- [~] datapack.wiki、MCC Questions 与手动非结构化笔记已有统一抓取/导入入口并生成原始数据；待评估扩大抓取后的提取质量
- [~] 手动收藏支持同时沉淀为 technique 与 reference 资源索引；目前仍依赖人工分类和质量审核
- [~] `crawl_and_extract.py` 已实现爬取与 LLM 提取流程代码，但尚未完成稳定性和结果质量验证
- [~] 主要流程提供 `run()` 和 `python -m modules.crawlers` 入口，但不能代表全部爬虫均已跑通
- [ ] 把提取策略改成更严格的“事实提取”，减少 LLM 编造
- [ ] 增加 few-shot 示例
- [ ] 拆成 fact-only -> 人工审核 -> synth-only 两步流程

## `modules/extractor/` / 结构化提取

- [~] `pipeline.py` 已实现 LLM 和规则提取路径，但尚未系统验证输出质量
- [~] 提取结构中已定义命令、数据包文件、交互测试需求和验证步骤字段，尚未打通后续流程
- [~] 已提供 `python -m modules.extractor` 入口，但只覆盖单个 inbox 文件结构化
- [~] `requires_datapack` 等字段存在于提取结果中，但尚未写入现有知识条目的 frontmatter
- [ ] 与验证调度器打通，根据提取结果自动选择命令、数据包或交互验证

## `modules/validator/` / 自动验证

- [~] Mineflayer 命令执行器、返回值读取和知识条目批量验证代码已实现
- [~] Web API 和 CLI 已可启动验证任务
- [ ] 在可用 Minecraft 服务端上完成 Mineflayer 实测，并生成 `validation_results/` 报告
- [ ] 批量验证命令类条目，并自动更新 `verified_in_game`
- [ ] 实现数据包验证：生成临时数据包 -> link/deploy -> `/reload` -> 执行并检查结果
- [ ] 将 Minecraft Mod MCP 的按键、鼠标、截图和 GUI 能力接入自动交互验证流程
- [ ] 实现验证失败后的 LLM 分析、修改和重新验证

## `modules/mcp_tools/vision/` / 视觉验证

- [~] 已有截图视觉模型分析脚本和模型列表脚本
- [~] Minecraft Mod MCP 已能提供 JPEG 截图
- [ ] 将截图获取与视觉分析接成自动验证流程
- [ ] 根据实际需要补充 OCR；当前视觉分析脚本不等同于完整 OCR 验证

## `modules/indexing/` / RAG

- [~] 已实现 RAG 索引构建代码
- [~] 已实现 RAG 查询和 `/api/query`，尚未完成查询质量与异常场景验证
- [~] 已提供 `python -m modules.indexing --rebuild` 入口，尚无自动化回归测试
- [x] 已存在近期重建的 ChromaDB 索引产物
- [ ] 增加流式输出
- [ ] 增加索引统计和健康检查

## `modules/maintenance/` / 维护工具

- [~] 已有去重、清理、质量审计、frontmatter 修复脚本，但部分脚本是导入即执行且缺少统一结果结构
- [~] 已提供 `python -m modules.maintenance` 入口，但入口调用的部分工具尚未实现 `run()`，当前不能完整使用
- [ ] 汇总各工具结果到 Dashboard

## `data/knowledge/` / 种子数据质量

- [x] 条目已使用 `source_type` 区分 manual、feature_article、wiki 等来源
- [x] frontmatter 已包含 `verified_in_game` 字段
- [ ] 实际完成游戏内验证的条目仍为 0，需要批量验证并标记
- [ ] 为条目增加“需要数据包验证 / 需要交互验证”等可调度字段
- [ ] 对人工条目和 AI 提取条目制定不同的审核规则

## `data/temp_datapacks/` / Beet 数据包验证

- [x] `pyproject.toml` 已加入 beet、bolt、mecha 依赖
- [x] `.opencode/skills/beet-datapack.md` 已记录 Beet 开发和 link 用法
- [~] 已记录 Windows 下只传 `--data-pack` 的 link 方式，但尚未接入并验证自动部署流程
- [x] 已有 `test_hello` 临时数据包样例
- [ ] 把 Beet 构建、部署、重载、结果检查和清理实现为验证器代码

## `projects/minecraft-mod-mcp/` / Minecraft Mod MCP

- [x] Mod bridge 已连接成功；2026-06-06 实测 `/api/status` 正常
- [x] 1.21.11 Fabric Mod 可构建、部署并在游戏内运行
- [x] MCP 控制模式下可释放鼠标并保持输入稳定
- [x] 支持键盘、鼠标、长按使用/攻击、右键使用物品
- [x] 支持聊天、暂停、关闭界面、枚举控件和按索引点击按钮
- [x] 支持 JPEG 原图截图和 PNG 网格预览
- [x] 命令响应保留游戏语言反馈，并为常见命令提供英文摘要
- [x] HTTP JSON 使用 UTF-8，服务端口绑定失败时会自动重试
- [x] 2026-06-06 实测 `/api/cmd` 可读取当前聊天界面控件
- [ ] 把这些能力封装为主项目 `modules/validator/` 可调用的交互验证后端
- [ ] 为关键 API 增加自动化回归测试

## `projects/mineflayer-bot/` / Mineflayer Bot

- [~] 已有独立 Node.js Bot、依赖和命令通信协议代码，但尚未完成当前环境下的实际命令验证
- [~] 已被 Python `MineflayerCommandExecutor` 调用
- [ ] 确认与当前 Minecraft 服务端版本和权限配置兼容
- [ ] 完成实际命令验证并保存报告

## `docs/` / 文档

- [~] 已有验证、Minecraft、提取策略和自动化系统设计文档
- [ ] 更新过时路径、命令和目录结构
- [ ] 区分“设计目标”“代码已实现”“已实际测试”，避免把设计文档当完成状态
