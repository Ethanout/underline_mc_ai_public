# 🧬 数据包知识自动化系统架构

一个自动爬取、提取、验证、迭代的 Minecraft 数据包知识引擎。

## 🎯 核心理念

**自动爬取 → AI 提取 → 游戏内验证 → 自动入库 → 持续迭代**

```
                   ┌─────────────────────────┐
                   │   知识库 (已验证条目)     │
                   └──────────┬──────────────┘
                              │
    ┌─────────────┐    ┌──────▼──────┐    ┌─────────────┐
    │  数据来源    │───▶│  验证引擎   │◀───│  爬虫系统   │
    │ Reddit      │    │  Mineflayer │    │  Wiki       │
    │ Wiki        │    │  MCP Mod    │    │  GitHub     │
    │ YouTube     │    │  数据包构建 │    │  Reddit     │
    │ GitHub      │    │  截图 OCR   │    │  Reddit     │
    └─────────────┘    └──────┬──────┘    └─────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  AI 提取流水线    │
                    │  LLM + 规则       │
                    │  命令提取         │
                    │  数据包解析       │
                    └───────────────────┘
```

## 📂 项目结构

```
underline_mc_ai/
├── crawlers/                    # 爬虫系统
│   ├── reddit_minecraftcommands.py # r/MinecraftCommands 问答爬虫
│   ├── wiki_crawler.py          # Minecraft Wiki 爬虫
│   ├── github_crawler.py        # GitHub 数据包仓库
│   └── youtube_crawler.py       # YouTube 字幕
│
├── extractor/                   # AI 提取流水线
│   ├── pipeline.py              # 主流水线
│   ├── llm_extractor.py         # LLM 提取
│   └── rule_extractor.py        # 规则提取
│
├── validator/                   # 验证引擎（已有）
│   ├── mineflayer/              # Mineflayer 命令验证
│   ├── mcp/                     # Mod MCP 交互验证
│   └── datapack/                # 数据包构建验证
│
├── database/                    # 知识数据库
│   ├── models.py                # 数据模型
│   ├── entry_manager.py         # 条目管理
│   └── migration.py             # 版本迁移
│
├── orchestrator/                # 编排系统
│   ├── scheduler.py             # 定时任务
│   └── pipeline_manager.py      # 流水线管理
│
├── knowledge/                   # 现有知识库（Markdown）
│   └── entries/                 # 已验证的条目
│
├── inbox/                       # 待处理原始数据
│
├── scripts/                     # 辅助脚本
│
└── docs/                        # 文档
```

## 🔄 工作流程

### 流水线 1：爬取 → 提取 → 验证 → 入库

```
1. 爬虫系统
   │
   ├── Reddit:  抓取帖子和评论回复树
   ├── Wiki:    定期扫描更新
   ├── GitHub:  监控新仓库/Star
   └── 手动:    inbox/ 目录投放
   │
   ▼
2. 原始数据缓存 (inbox/)
   │
   ▼
3. AI 提取流水线
   │
   ├── LLM 分析: "这是一个什么数据包技巧？"
   ├── 命令提取: 从代码块提取命令
   ├── 数据包识别: 它是 advancement/loot_table/predicate?
   └── 结构化: 生成标准条目格式
   │
   ▼
4. 验证引擎
   │
   ├── 是否需要数据包？ → 构建临时数据包 → 部署 → 测试
   ├── 只需要命令？     → Mineflayer 执行 → 检查输出
   ├── 需要交互？       → MCP 模拟按键 → 截图验证
   └── 需要玩家？       → 标记为"需人工确认"
   │
   ▼
5. 结果处理
   │
   ├── ✅ 验证通过 → 入库 (knowledge/entries/)
   │                 - 更新时间戳
   │                 - 记录验证来源
   │                 - 附加验证证据（截图）
   │
   ├── ❌ 验证失败 → 修复尝试
   │                 - 自动修复命令语法
   │                 - 重新测试
   │                 - 3次失败后标记待审
   │
   └── ⚠️ 需要人工 → inbox/needs_review/
```

### 流水线 2：定期重新验证

```
定时任务 (每天/每周)
   │
   ├── 扫描所有已入库条目
   ├── 重新执行验证
   ├── 更新验证状态
   └── 标记"不再有效"的条目
```

### 流水线 3：知识库质量提升

```
AI 分析整个知识库
   │
   ├── 发现知识缺口（某版本特性缺失）
   ├── 对比多个来源一致性
   ├── 生成综合条目
   └── 去重和合并
```

## 🧠 AI 提取流水线设计

### LLM 提示词设计

```python
EXTRACTION_PROMPT = """你是一个 Minecraft 数据包专家。分析以下内容，提取数据包技巧：

{raw_content}

请输出 JSON 格式：
{
  "title": "技巧标题",
  "summary": "一句话摘要（中文）",
  "category": "advancement|predicate|loot_table|function|command|other",
  "minecraft_version": "1.21",
  "requires_datapack": true/false,
  "datapack_files": [
    {
      "type": "advancement",
      "path": "data/namespace/advancement/example.json",
      "content": {提取的JSON}
    }
  ],
  "commands": ["命令1", "命令2"],
  "keywords": ["标签1", "标签2"],
  "difficulty": "beginner|intermediate|advanced",
  "source": {
    "type": "reddit|wiki|github|manual",
    "url": "来源链接",
    "author": "作者"
  },
  "verification": {
    "method": "command|datapack|interactive",
    "steps": ["验证步骤1", "验证步骤2"],
    "expected_result": "预期输出或现象"
  }
}"""
```

### 模型选择

| 阶段 | 推荐模型 | 成本 | 速度 |
|------|----------|------|------|
| 提取 | DeepSeek / Qwen2.5-32B | 低 | 快 |
| 验证决策 | 本地 Ollama + Qwen2.5 | 免费 | 中 |
| 复杂推理 | Claude Code（手动辅助） | 高 | 慢但准确 |

## 🔌 爬虫系统设计

### Reddit 爬虫

抓取 `r/MinecraftCommands` 的 Java Help 帖子及公开归档中可获取的评论，
根据 `parent_id` 重建回复树，并增量保存原始问答数据。

### Wiki 爬虫

```python
class WikiCrawler:
    """
    爬取 Minecraft Wiki
    
    来源：
    - https://minecraft.wiki/w/Advancement
    - https://minecraft.wiki/w/Predicate
    - https://minecraft.wiki/w/Loot_table
    
    使用 mediawiki API
    """
    
    def crawl_category(self, category: str):
        # 爬取某个分类下的所有页面
        pages = wiki_api.get_category_members(category)
        for page in pages:
            content = wiki_api.get_page_content(page)
            # 提取代码示例
            examples = self.extract_code_examples(content)
            self.save_to_inbox(examples)
```

### GitHub 爬虫

```python
class GithubCrawler:
    """
    爬取 GitHub 上的数据包仓库
    
    搜索关键词：
    - "datapack" topic
    - "minecraft datapack"
    - "advancement" "predicate"
    
    监控 Star 增长快的仓库
    """
    
    def search_repositories(self):
        repos = github_api.search_repositories(
            query="topic:datapack",
            sort="stars",
            limit=50
        )
        
        for repo in repos:
            # 下载 README 和示例文件
            files = self.get_datapack_files(repo)
            self.analyze_and_extract(files)
```

## ✅ 验证引擎增强

### 智能验证调度

```python
class ValidationScheduler:
    """智能选择验证方法"""
    
    def schedule(self, entry: Dict) -> ValidationPlan:
        plan = ValidationPlan()
        
        if entry.get("requires_datapack"):
            # 需要构建数据包
            plan.add_step("build_datapack", entry["datapack_files"])
            plan.add_step("deploy_to_game")
            plan.add_step("reload")
            
            # 根据类型选择验证方法
            for file in entry["datapack_files"]:
                if file["type"] == "advancement":
                    plan.add_step("grant_and_check")
                elif file["type"] == "predicate":
                    plan.add_step("setup_and_test")
                elif file["type"] == "loot_table":
                    plan.add_step("run_loot_command")
        
        if entry.get("commands"):
            plan.add_step("mineflayer_execute", entry["commands"])
        
        if entry.get("interactive"):
            plan.add_step("mcp_press_key", entry["interactive"]["keys"])
            plan.add_step("screenshot")
        
        return plan
```

### 自适应验证

```python
class AdaptiveValidator:
    """根据验证结果自动调整"""
    
    async def validate_with_retry(self, entry: Dict, max_retries: int = 3):
        for attempt in range(max_retries):
            result = await self.validate(entry)
            
            if result["success"]:
                return result
            
            # 分析失败原因
            error = result["error"]
            
            if "Unknown command" in error:
                # 可能是语法问题，尝试修复
                entry = self.fix_syntax(entry, error)
            
            elif "No permission" in error:
                # 需要 OP
                self.send_chat(f"/op {self.bot_name}")
            
            elif "timeout" in error:
                # 服务器负载高，等一下重试
                await asyncio.sleep(10)
            
            # 记录失败次数
            self.log_failure(entry, attempt, error)
        
        # 标记需要人工审核
        entry["status"] = "needs_review"
        return entry
```

## 🗄️ 数据库设计

### SQLite Schema

```sql
CREATE TABLE entries (
    id TEXT PRIMARY KEY,           -- t0001, t0002...
    title TEXT NOT NULL,
    summary TEXT,
    category TEXT,                 -- advancement, predicate, command
    minecraft_version TEXT,
    difficulty TEXT,               -- beginner, intermediate, advanced
    requires_datapack BOOLEAN,
    status TEXT DEFAULT 'unverified',  -- unverified, verified, failed, deprecated
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    verified_at TIMESTAMP,
    verification_method TEXT,      -- mineflayer, mcp, datapack, manual
    verification_confidence REAL   -- 0.0 ~ 1.0
);

CREATE TABLE entry_contents (
    entry_id TEXT REFERENCES entries(id),
    language TEXT DEFAULT 'zh',    -- zh, en, ja...
    content_md TEXT,              -- Markdown 内容
    raw_source TEXT               -- 原始来源
);

CREATE TABLE datapack_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT REFERENCES entries(id),
    file_type TEXT,               -- advancement, predicate, loot_table...
    namespace TEXT,
    path TEXT,                    -- data/namespace/type/name.json
    content_json TEXT             -- JSON 内容
);

CREATE TABLE commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT REFERENCES entries(id),
    command TEXT,
    language TEXT DEFAULT 'mcfunction'
);

CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT REFERENCES entries(id),
    source_type TEXT,             -- reddit, wiki, github, manual
    url TEXT,
    author TEXT,
    fetched_at TIMESTAMP
);

CREATE TABLE verification_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT REFERENCES entries(id),
    verified_at TIMESTAMP,
    success BOOLEAN,
    method TEXT,
    details TEXT,                 -- JSON with output, screenshots, logs
    confidence REAL
);

CREATE TABLE crawl_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT,
    source_url TEXT,
    raw_content TEXT,
    status TEXT DEFAULT 'pending', -- pending, processing, done, failed
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    processed_at TIMESTAMP
);

-- 索引
CREATE INDEX idx_entries_status ON entries(status);
CREATE INDEX idx_entries_category ON entries(category);
CREATE INDEX idx_entries_version ON entries(minecraft_version);
CREATE INDEX idx_crawl_status ON crawl_queue(status);
```

## 🤖 编排系统

### 主循环

```python
class Orchestrator:
    """系统编排器"""
    
    def __init__(self):
        self.crawlers = [RedditCrawler(), WikiCrawler(), GithubCrawler()]
        self.extractor = AIExtractor(model="deepseek")
        self.validator = AdaptiveValidator()
        self.db = Database()
        self.scheduler = Scheduler()
    
    async def run(self):
        """主循环"""
        while True:
            await self.crawl_phase()
            await self.extract_phase()
            await self.validate_phase()
            await self.curate_phase()
            await asyncio.sleep(3600)  # 每小时循环一次
    
    async def crawl_phase(self):
        """爬取阶段"""
        for crawler in self.crawlers:
            results = await crawler.crawl()
            for result in results:
                self.db.add_to_queue(result)
    
    async def extract_phase(self):
        """提取阶段"""
        pending = self.db.get_pending_items(limit=10)
        for item in pending:
            entry = await self.extractor.extract(item.raw_content)
            self.db.save_entry(entry)
            item.status = "processed"
            self.db.update(item)
    
    async def validate_phase(self):
        """验证阶段"""
        unverified = self.db.get_unverified_entries(limit=5)
        for entry in unverified:
            result = await self.validator.validate_with_retry(entry)
            self.db.save_verification(entry.id, result)
            
            if result["success"]:
                entry.status = "verified"
                entry.verified_at = datetime.now()
                self.db.update(entry)
                self.export_to_markdown(entry)  # → knowledge/entries/
    
    async def curate_phase(self):
        """策展阶段"""
        # 重新验证旧条目
        old = self.db.get_entries_older_than(days=7)
        for entry in old:
            await self.revalidate(entry)
        
        # 合并重复条目
        duplicates = self.db.find_duplicates()
        for group in duplicates:
            self.merge_entries(group)
        
        # 清理失败条目
        failed = self.db.get_failed_entries(max_retries=3)
        for entry in failed:
            entry.status = "needs_review"
            self.export_to_inbox(entry)
```

## 🚀 立即开始

### 第一步：安装依赖

```bash
# 爬虫
pip install wikipedia-api beautifulsoup4 requests
pip install git+https://github.com/PyGithub/PyGithub.git

# AI 提取
pip install openai  # 兼容 DeepSeek/OpenAI/Qwen

# 数据库
pip install sqlitedict aiosqlite
```

### 第二步：运行

```bash
# 启动完整流水线
python orchestrator/start.py

# 或单独组件
python crawlers/wiki_crawler.py  # 只爬取 Wiki
python extractor/pipeline.py     # 只处理 inbox/
python validator/run.py           # 只验证现有条目
```

### 最终目标

```
输入: Reddit 问答 / Wiki 页面 / GitHub 仓库 / ...

处理流程:
  Crawl → Extract → Build Datapack → Deploy → Test → Verify → Store

输出: /knowledge/entries/t0001_...md  (已验证的条目)

质量保证:
  - 每个条目都在真实游戏中测试过
  - 失败的条目自动修复或标记待审
  - 定期重新验证防止版本过时
  - 截图保留作为证据
```

---

这是一个完整的**自动化知识引擎**。你希望先实现哪部分？
- 🔴 爬虫系统？（Reddit / Wiki）
- 🟡 AI 提取流水线？（LLM 提取）
- 🟢 验证引擎增强？（已有，需要扩展）
- 🔵 数据库集成？
- 🟣 编排系统？
