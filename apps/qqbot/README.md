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

## 一键启动

`.env` 里设好 `NAPCAT_DIR`（NapCat.Shell 的目录）后，双击仓库根目录的 `start_ui.bat`，或者运行：

```bash
python -m qqbot start
```

它会依次：

1. 从 NapCat 的 `config/onebot11_<QQ号>.json` 读 OneBot 地址和 token。不用再抄进 `.env`。
2. 事件 token 不存在就生成一个。
3. 把 web 的推送地址和事件 token 写进 NapCat 的 `httpClients`，旧文件先备份成 `.bak`，没变化就不动。
4. 先起 web。
5. 等 web 起来了，再在新窗口起 NapCat。它直接找 `QQ.exe`，不走 NapCat 自带的 `.bat`。那个脚本只查注册表，有些 QQNT 安装没写注册表，就会报 provided QQ path is invalid。实在找不到就在 `.env` 里设 `NAPCAT_QQ_PATH`。设了 `NAPCAT_UIN` 会快速登录：这个号在本机扫码登录过一次以后就不用再扫。

如果 NapCat 已经在跑，就不会再起一个。这时要是配置刚改过，它会提示你重开 NapCat，但不会替你杀进程，因为 NapCat 和桌面 QQ 共用同一份安装。改端口只改 `.env` 的 `QQBOT_WEB_PORT`，再启动一次就行。只想起 web 就加 `--no-napcat`。

## WebUI 后端

单独起 web：在本目录运行 `python -m qqbot.web`，然后打开 `http://127.0.0.1:18787`。也可以在 editable 安装后运行 `qqbot-web`。WebUI 只接受 endpoint、已授权群号和输出目录；不会接收或展示 Token。任务状态通过 `/api/jobs/{id}` 查询，`/api/health` 只返回服务状态和是否配置 Token。

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
  -> collect_utterances()   文字：认出发言人，认出毯毯自己的话，还原引用的原文
  -> collect_images()       图片：每张一条，同一条消息里的文字当说明
  -> Embedder.encode()      默认走硅基流动的 Qwen3-VL-Embedding-8B；也可切到本机 bge-m3
  -> ChromaDB               每个群一个 collection，按 event_key 去重，重复跑不会写重
```

**图片**

图片和文字进同一个库、同一个向量空间，所以拿一句话能检索出图片，反过来也行。每张图单独一条（id 是 `<event_key>#img<n>`），只用图片本身算向量；把文字和图片合成一个输入试过，出来的向量几乎全是文字（和纯文字相似度 0.89，和图片只有 0.41），等于丢了图片。

QQ 图片链接几个小时就过期，所以下载发生在 **web 收到消息的时候**：`python -m qqbot.web` 开着，群里每来一张图就在后台存进 `QQBOT_IMAGE_DIR`（默认 `runtime/private/qq_images/`，按内容去重，同一个表情包只存一份）。入库时读这份缓存；缓存里没有的会再试着下载一次，多半已经过期，跑完会报有几张拿不到。web 没开的那段时间里的图就是补不回来了。

只有 api 后端的 VL 模型能收图片。`local` 后端的 `bge-m3` 只认文字，入库时会说明跳过了几张图。`--no-images` 可以这次只收文字。

```bash
python -m qqbot.style_memory --query "笑死" --kind image        # 用一句话找图
python -m qqbot.style_memory --query-image some.png --kind text  # 用一张图找话
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
- `--stats` 只看条数，不动数据。`--group` 指定群号（库里有多个群时必须给），`--k` 是检索条数，`--bot-only` / `--human-only` 分别在毯毯自己的话和群友的话里检索，`--kind text` / `--kind image` 只检索文字或只检索图片。

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

---

## Agent 与权限

毯毯使用 LangGraph 管理工具循环，任务状态持久化到 SQLite，重启后可恢复，同一 `run_id` 的工具调用不重复执行。每次回复都是一个独立任务，绑定发起人的权限，直到任务结束。

**管理员判断**只认 `.env` 的 `QQBOT_ADMIN_IDS`（逗号分隔的 QQ 号），与 OneBot 事件里的 `user_id` 比对。群主身份、群管理员角色、消息里自称管理员，一律不算。工具层在注册和执行两处都检查权限，审计写到 SQLite 的 `audit` 表。

工具分两档：

- **普通成员**：`search_chat`、`read_chat_around`、`read_history`、`read_quoted`、`read_forward`、`read_essence`（只读，当前群）；`search_memory`（只读，相关库和本群聊天）；`view_image`；`adjust_runtime`（白名单参数，有冷却）。
- **管理员专属**：`remember`（写无关库，内容模糊化成软偏好）、`forget`（进回收站，只删约定不删聊天原文）、`reset_runtime`；技巧收录相关的 `web_search`、`web_read`、`read_file`、`write_file`、`run_command`。

跨群读取、普通成员调写入工具，都会被拒并写审计。

`QQBOT_TOOL_ROUNDS`（默认 3）限制单次任务的工具循环轮数，`QQBOT_TOOL_MAX_ITEMS` / `QQBOT_TOOL_MAX_CHARS` 限制每次工具返回的条数和字数。

## 记忆与约定

**记忆分库**：每群有一个相关库（MC 原版创作、数据包、编程方向的内容，长期保存）和一个无关库（暂时分不清的内容先放这里）。两库都用 ChromaDB 存向量，和风格记忆的库分开。

**约定的读写路径**：
- 管理员通过 `remember` 写入无关库时，内容会被模糊化成软偏好，例如「伊桑说他说摸摸的时候想看到 ww，看心情接」，不保留完整原文。
- 约定不作为 `search_memory` 的检索结果——普通成员触发的任务里查不到无关库。
- 但每次生成回复前，`MemoryService.preference_hints()` 会把激活度高的软偏好注入 prompt 末尾，毯毯照样能看心情遵守。
- 只有当前 `QQBOT_ADMIN_IDS` 名单里的人写的才算约定，群友说「以后你要……」只是聊天内容。

**遗忘模拟**：`QQBOT_MEMORY_FORGET_ENABLED=0` 时只模拟，结果在 `/api/memory/forgetting` 可见，不删数据。设为 1 后实际遗忘的内容先进 `/api/recycle-bin`。

## 技巧收录

收录入口有两个：一是精华同步（每 `QQBOT_ESSENCE_SYNC_MINUTES` 分钟自动跑，也可以 @ 毯毯手动触发）；二是管理员指定历史范围或合并转发直接收录。收录前模型先判断内容是否是数据包技术资料（技巧、教程、工具链接、失败经验等），普通聊天不收。

条目写成 Markdown，存在 `QQBOT_TRICKS_DIR`（默认 `runtime/private/qq_tricks/<群号>/`）。每条包含：标题、用途、适用版本、代码、限制、作者、原消息来源。不知道的字段写「未知」，并注明「AI 整理、未验证」。文件改动后自动重建索引。

重复收录时合并来源，结论矛盾时两边都保留，不强行裁判。群库与外部知识库分开。

压缩包内容有路径穿越检查和大小限制；视频只保存来源链接，不尝试解析正文。

## 仿生记忆参数

这是一套可解释的工程近似，不是测量人类记忆的实验结果。

遗忘公式：`R(t) = (1 + t/S)^(-d)`，`S` 是强度（秒），`d` 是衰减指数，`t` 是距上次实际使用的时长。`R` 只是模型内部的保留分数，门槛和各参数都可以按群调。

以下参数可在 `.env` 里调整：

| 变量 | 默认值 | 含义 |
|---|---|---|
| `QQBOT_MEMORY_INITIAL_STRENGTH` | 86400 | 新记忆的初始强度（秒） |
| `QQBOT_MEMORY_DECAY` | 0.5 | 遗忘衰减指数 |
| `QQBOT_MEMORY_RETRIEVAL_THRESHOLD` | 0.1 | 低于此 R 值视为可遗忘 |
| `QQBOT_MEMORY_ACTIVATION_HALF_LIFE` | 3600 | 短期激活度的半衰期（秒） |
| `QQBOT_MEMORY_HIT_GAIN` | 0.15 | 检索命中对激活度的提升 |
| `QQBOT_MEMORY_REINFORCEMENT_GAIN` | 3600 | 实际使用一次的强化量（秒） |
| `QQBOT_MEMORY_SPACING_SCALE` | 86400 | 间隔效应参考时长：使用间隔越接近此值，强化效果越好 |
| `QQBOT_MEMORY_REPEAT_WINDOW` | 600 | 短窗口内重复命中不额外强化的时间范围（秒） |
| `QQBOT_MEMORY_REPEAT_PENALTY` | 0.5 | 短窗口内重复命中的强化折扣 |

检索命中只提高短期激活度；只有被毯毯实际引用使用才强化长期强度 `S`。刷屏刷不出永久记忆。

睡眠整理（每 `QQBOT_MEMORY_SLEEP_MINUTES` 分钟后台跑一次）：先压缩低激活记忆，再合并语义相近的短记忆（保留各自来源，剩余遗忘时间取平均），最后标记可以实际遗忘的内容。

## 主动发言与情绪

**主动发言**默认关闭。在 `.env` 里填 `QQBOT_PROACTIVE_GROUPS=100000001`（你的群号）才启用。每次主动发言至少间隔 `QQBOT_PROACTIVE_MIN_GAP` 秒（默认 120），受情绪影响在 0.5–2 倍之间缩放；每小时不超过 `QQBOT_PROACTIVE_MAX_PER_HOUR` 次（默认 6）。@ 回复沿用原有冷却，不受此限制。

**活跃节律**：后台按「周几 × 小时」168 格统计群消息量，带指数时间衰减，@ 毯毯的消息额外加权。每 20 秒 tick 一次，当前格活跃度越高、最近消息越密、精力越足，这次 tick「拿起手机」的概率越大。拿起后随机活跃 5–20 分钟。状态持久化到 SQLite，重启后自动恢复。

**情绪向量**（6 维，各有基线，随时间回归基线，初始值均为 0.5）：

- 兴奋、心情、兴趣、精力、烦躁、亲近
- 被 @ 时兴趣上升；被连续提问时烦躁上升、精力下降；判断模型每次给出 `emotion_delta`，裁剪后叠加。
- 数值直接写进 prompt 末尾，毯毯知道自己现在的状态。

**判断模型**（`QQBOT_JUDGE_MODEL`，默认 `deepseek-flash`，思考深度 `QQBOT_JUDGE_REASONING_EFFORT`，默认 `medium`）：
- 去抖：约 8 秒没有新消息，或者 8 秒内攒满 5 条，触发一次判断。
- 输出 JSON：`{speak, finished, wait_seconds, why, reply_to?, emotion_delta, stay}`。`finished=false` 就等 `wait_seconds` 秒再看一次，总等待上限 20 秒。
- 发送前如果又来了新消息：@ 回复用新转录稿重新生成（最多一次）；主动插话直接放弃。
- 返回坏 JSON 时按「不说」处理，不报错、不重试。

基线和其他 brain 参数（`QQBOT_BASELINE_*`、`QQBOT_JUDGE_THRESHOLD`、`QQBOT_ACTIVE_MIN/MAX_SECONDS` 等）见 `.env.example` 注释。管理界面 `/api/brain` 可以看当前情绪数值和活跃画像，`adjust_runtime` 可以在白名单范围内微调。
