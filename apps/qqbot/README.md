# QQ Bot：群精华采集

当前子项目只负责通过 OneBot/NapCat/Lagrange 兼容 HTTP API 抓取群精华消息和媒体，并把结果保存为知识库的外部来源快照。

## 配置

复制根目录的 `.env.example` 成 `.env` 填好就够了，不用每次开 shell 设 `$env:`。`qqbot` 包在导入时会自动读它：从当前目录往上找最近的一处，也可以用 `QQBOT_ENV_FILE` 指定别的路径。进程里已经有的真环境变量优先，所以 `$env:QQBOT_EMBED_MODEL=... python -m qqbot.web` 这种临时覆盖照样管用。

密钥不必搬进 `.env`。`<NAME>_FILE` 指向一个文件，`<NAME>` 就会取那个文件的内容：

```bash
# .env 里这样写，key 留在原来那个文件里
QQBOT_EMBED_API_KEY_FILE=D:\重要的资料\身份认证和各种key\silicon.txt
```

填完检查一下读到了什么（只报长度，不打印密钥，带 key 的话还会真发一次请求验证）：

```bash
python -m qqbot
```

## WebUI 后端

设置 `ONEBOT_ACCESS_TOKEN` 后，在本目录运行 `python -m qqbot.web`，然后打开 `http://127.0.0.1:8787`。也可以在 editable 安装后运行 `qqbot-web`。WebUI 只接受 endpoint、已授权群号和输出目录；不会接收或展示 Token。任务状态通过 `/api/jobs/{id}` 查询，`/api/health` 只返回服务状态和是否配置 Token。

## 运行

```powershell
python .\src\qqbot\essence_exporter.py `
  --endpoint http://127.0.0.1:3000 `
  --group-id <your-authorized-group-id> `
  --output <private-output-directory>
```

实际使用时请通过环境变量提供 token，例如 `$env:ONEBOT_ACCESS_TOKEN = "..."`，不要把 token 写进仓库、命令历史或参数。`run-export.ps1` 是便捷包装；`config/config.example.json` 只包含非敏感默认值。本工具仅应访问自己管理或已明确获授权的群。

## 数据流

```text
OneBot HTTP API -> essence_exporter.py -> messages.json + media/
                                      -> qqbot.organize
                                      -> 私有原文与分类索引
                                      -> 后续接入 ../underline_wiki/（尚未实现）
```

导出器按 `message_id` 增量合并，保留服务返回的原始元数据与 `content`，并下载 `image`、`file`、`video`、`record` 段。精华列表已含 `content` 时不会调用 `get_msg`。`--diagnose` 仅显示接口结构/数量且不写入文件；正常导出结束会显示消息、媒体、失败数量和输出目录。不同适配器的精华列表 action 可用 `--action` 覆盖。

## 自动回复预留

`src/qqbot/reply.py` 仅提供策略边界，默认不回复。未来接入事件消费时，必须先实现群白名单、发送者权限、冷却/速率限制、敏感内容过滤和可审计日志，再接入知识库检索。

`src/qqbot/prompts.py` 保存 Underline Agent 的系统提示词。它叠加在 DeepSeek Harness 的简明表达规则之上；Harness 的内置提示词不在本仓库中修改。

## 风格记忆（第一步）

模型的权重不会因为你聊天而改变，能变的是每次喂进去的上下文。所以要让它越来越像毯毯说话，只有一个办法：把群里说过的真实句子存下来，在合适的时机检索出最相近的几条放进提示词。

`src/qqbot/style_memory.py` 做的是这条链路的存储和检索部分。

```text
runtime/private/qq_events.jsonl
  -> collect_utterances()   只留文字，认出发言人，认出毯毯自己的话，还原引用的原文
  -> Embedder.encode()      默认本机 CPU 跑 bge-m3；也可切到 API
  -> ChromaDB               每个群一个 collection，按 event_key 去重，重复跑不会写重
```

运行（在仓库根目录下）：

```bash
PYTHONPATH=apps/qqbot/src python -m qqbot.style_memory
```

默认读 `runtime/private/qq_events.jsonl`，写 `runtime/private/qq_style/`，结束后打印每个群存了多少条。这两个路径是相对**当前工作目录**解析的，不是相对这个文件，所以在 `apps/qqbot/` 里跑会读到不存在的位置、安静地写入 0 条。要么在根目录跑，要么显式给 `--journal`。

`python -m qqbot.style_memory` 需要 `src/` 在导入路径上。装过 `pip install -e apps/qqbot` 的话直接跑就行，也可以用安装出的命令 `qqbot-style-memory`。

**收哪些数据**

- `--since 2026-10-04` — 只收这个时间之后的记录。
- `--bot-since 2026-10-04` — 只对毯毯自己的话生效。修好引用记录之前的旧回复没有 `reply` 段，看不出在回什么，混进去会教坏检索。想先只用干净的语料，就给这个参数一个修复之后的时间。
- `--stats` 只看条数，不动数据。`--group` 指定群号（库里有多个群时必须给），`--k` 是检索条数，`--bot-only` / `--human-only` 分别在毯毯自己的话和群友的话里检索。

检索看看效果（这一步才是你判断 embedding 好不好的依据）：

```bash
python -m qqbot.style_memory --query "这段 execute 是干嘛的" --bot-only
```

后端靠环境变量切换，见 `.env.example`：

- `QQBOT_EMBED_BACKEND=local` — 本机 `bge-m3`，走 CPU，**不占显存**，把显卡留给别的活。
- `QQBOT_EMBED_BACKEND=api` — OpenAI 兼容的 `/embeddings` 接口，配 `QQBOT_EMBED_BASE_URL`、`QQBOT_EMBED_API_KEY`、`QQBOT_EMBED_MODEL`。

两种后端产出的向量不在同一个空间里。换后端之后要清掉 `runtime/private/qq_style/` 重建，否则新旧向量混在一起，距离全是错的。

注意这里存的是**说过什么**，不是**应该怎么说**。固定的人设范例和不许出现的写法留在提示词里，不放进这个库。库里目前也没有任何"这句回得好"的判断，检索结果就是原样的事实，先看数字，再自己看几条，别直接当成训练数据接进自动流程。

## 整理已有导出

整理不会删除或改写原始 `messages.json` 和 `media/`。运行 `python -m qqbot.organize --source <原始导出>/messages.json`，结果会写入私有的 `runtime/private/qq_essence_organized/`，包含分类索引、独立 Markdown 文档和媒体副本。重复内容只在 `index.json` 中标记，进入正式知识库前仍需人工核验。

## 不迁移的草稿内容

`probe/`、`probe2/`、`diagnose/`、`auto-probe/` 是一次性接口探测和重复导出，不属于运行代码；完整历史导出属于私有资料，不进入 Git。
