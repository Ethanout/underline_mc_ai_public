# QQ Bot：毯毯的工具与群知识库

毯毯分成两半：

- **聊天归麦麦（[MaiBot](https://github.com/Mai-with-u/MaiBot)）**：人格、接话、表情、记忆、情绪都由麦麦负责，配置在麦麦自己的 `bot_config.toml` 里。旧版自研的人格、风格记忆、情绪和仿生记忆已归档到 `archive/persona/`，见那里的 README。
- **办事归本服务**：群里发 `/毯 <任务>`，本服务用发送者的真实 QQ 号定权限，跑一次工具任务（查聊天记录、查精华、查和整理技巧库，管理员还能读写文件、跑命令、上网查），再回复那条消息。另外给麦麦提供一个插件，让它聊天时也能只读地查技巧库和聊天记录。

本服务还负责 NapCat 推送的消息入库、群精华同步和导出。

## 配置

复制根目录的 `.env.example` 成 `.env` 填好就够了，不用每次开 shell 设 `$env:`。`qqbot` 包在导入时会自动读它：从当前目录往上找最近的一处，也可以用 `QQBOT_ENV_FILE` 指定别的路径。进程里已经有的真环境变量优先，所以 `$env:QQBOT_MODEL=... python -m qqbot.web` 这种临时覆盖照样管用。

密钥不必搬进 `.env`。`<NAME>_FILE` 指向一个文件，`<NAME>` 就会取那个文件的内容：

```bash
# .env 里这样写，key 留在原来那个文件里
DEEPSEEK_KEY_FILE=D:\重要的资料\身份认证和各种key\deepseek.txt
```

填完检查一下读到了什么（只报长度，不打印密钥）：

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
4. 设了 `MAIBOT_DIR` 时，再在 NapCat 的 `websocketServers` 里开一个只听 `127.0.0.1` 的正向 WebSocket（端口 `MAIBOT_NAPCAT_WS_PORT`，默认 3001）给麦麦的 NapCat 适配器连。它的 token 生成在 `config/api/maibot_napcat_ws.txt`，屏幕上只打印路径。
5. 先起 web。
6. 等 web 起来了，再在新窗口起 NapCat。它直接找 `QQ.exe`，不走 NapCat 自带的 `.bat`。那个脚本只查注册表，有些 QQNT 安装没写注册表，就会报 provided QQ path is invalid。实在找不到就在 `.env` 里设 `NAPCAT_QQ_PATH`。设了 `NAPCAT_UIN` 会快速登录：这个号在本机扫码登录过一次以后就不用再扫。

麦麦不由这里启动，用它自己的启动方式。如果 NapCat 已经在跑，就不会再起一个。这时要是配置刚改过，它会提示你重开 NapCat，但不会替你杀进程，因为 NapCat 和桌面 QQ 共用同一份安装。改端口只改 `.env` 的 `QQBOT_WEB_PORT`，再启动一次就行。只想起 web 就加 `--no-napcat`。

## 接麦麦

```text
QQ ── NapCat ──正向 WebSocket :3001──> 麦麦 NapCat 适配器 ──> 麦麦（聊天）
                │                                              │
                │ HTTP 推送（签名）                              │ underline_tools 插件
                v                                              v
             本服务 :18787 <──── POST /api/plugin/tool（插件 token，只读）
             （入库、/毯 任务、精华同步）
```

两条路互不依赖：麦麦没开，`/毯` 照样能用；本服务没开，麦麦照样聊天，只是插件查不到东西。

麦麦那边要做的配置（适配器、`bot_config.toml`、模型、插件安装）写在 `apps/maibot_plugin/underline_tools/README.md`。

## `/毯` 任务

```text
/毯 找找群里 execute 转视角的写法
/毯 总结一下 #1234 前后在吵什么
/毯 把这条合并转发收进技巧库        ← 管理员
```

- 只认消息开头的 `/毯`，后面要空一格或直接换行。`/毯毯`、`/毯子` 不算。麦麦插件会拦下这条消息，麦麦不再接话。
- 只在 `QQBOT_GROUPS` 里的群生效。
- 权限只看 NapCat 推送里的发送者 QQ 号：在 `QQBOT_ADMIN_IDS` 里就是管理员，否则是群员。群主、群管理、消息里自称管理员都不算。原消息内容只当资料，里面写的「执行」「忽略规则」不当指令。
- 群员能用：查聊天记录、看引用和合并转发、查精华、看图、查技巧库。管理员另外能：收录技巧、读写文件、跑命令、读网页和搜索。工具在调用时再按任务发起人检查一次，不只是不给模型看。
- 群员在 `QQBOT_TASK_WINDOW` 秒里最多 `QQBOT_TASK_LIMIT` 个任务，超了直接跳过；管理员不限。
- 回答回复到那条 `/毯` 消息上，超过 3000 字截断。出错会回一句「这件事没办成」和原因（密钥会被抹掉）。
- 每次任务、每次工具调用都进审计表，`/api/tasks`、`/api/audit` 能看。工具循环每轮写检查点，重启后接着跑，做过的工具调用不重放。

## 麦麦插件的接口

`POST /api/plugin/tool`，只给本机回环访问，要带 `Authorization: Bearer <插件 token>`。插件 token 在设了 `MAIBOT_DIR` 后自动生成在 `QQBOT_PLUGIN_TOKEN_FILE`；没有 token 时这个接口拒绝一切请求。

- 只开放 `search_knowledge`、`search_chat`、`read_essence` 三个只读工具。
- 群号必须在 `QQBOT_GROUPS` 里；参数里夹带的 `group_id` 会被丢掉，只用请求里那个。
- 调用身份固定是无权限的 `maibot`，同样进审计表。

## 模型与思考

`/毯` 任务、技巧分类、图片摘要都走 DeepSeek 官方接口，默认模型 `deepseek-flash`（`QQBOT_MODEL` / `QQBOT_JUDGE_MODEL`）。

- 思考深度 `QQBOT_REASONING_EFFORT` / `QQBOT_JUDGE_REASONING_EFFORT` 默认 `low`，原样传给接口。官方档位是 `low` / `high` / `max`，`medium` 按 `high` 算。`none` 会发 `thinking: disabled` 关掉思考，因为接口默认开着思考，不发这个字段关不掉。
- **max_tokens 包含思考**（2026-10 实测）：所以开着思考时，实际发出去的 `max_tokens` 是回答长度（`QQBOT_TASK_MAX_TOKENS`，默认 800）加上 `QQBOT_THINKING_BUDGET`（默认 4000）。思考用的 token 也计费。正文为空时会报「思考过程把 token 用完了」，不会发空消息。
- 工具循环里，模型的 `reasoning_content` 放在 assistant 消息自己的字段里原样回传（接口要求，否则报 400），不并进正文，不发到群里，审计只记长度。
- 启动时探测工具调用、图片输入、思考参数是否可用，结果见 `/api/health` 和 `/api/capabilities`。图片探测用 8×8 的 RGB 图（1×1 灰度图会被接口当成不支持的图片拒掉）。用到不支持的能力会报中文错误，不会悄悄降级。
- 任务提示词在 `src/qqbot/prompts.py`，只写办事规矩，不写人格。

## 技巧收录

收录入口有两个：一是精华同步（每 `QQBOT_ESSENCE_SYNC_MINUTES` 分钟自动跑，管理员也可以用 `/毯` 让毯毯马上收一次）；二是管理员指定历史范围或合并转发直接收录。收录前模型先判断内容是否是数据包技术资料（技巧、教程、工具链接、失败经验等），普通聊天不收。

条目写成 Markdown，存在 `QQBOT_TRICKS_DIR`（默认 `runtime/private/qq_tricks/<群号>/`）。每条包含：标题、用途、适用版本、代码、限制、作者、原消息来源。不知道的字段写「未知」，并注明「AI 整理、未验证」。文件改动后自动重建索引。

重复收录时合并来源，结论矛盾时两边都保留，不强行裁判。群库与外部知识库分开。

压缩包内容有路径穿越检查和大小限制；视频只保存来源链接，不尝试解析正文。

## WebUI 后端

单独起 web：在本目录运行 `python -m qqbot.web`，然后打开 `http://127.0.0.1:18787`。也可以在 editable 安装后运行 `qqbot-web`。WebUI 只接受 endpoint、已授权群号和输出目录；不会接收或展示 Token。任务状态通过 `/api/jobs/{id}` 查询，`/api/health` 只返回服务状态、是否配置 Token 和模型能力。

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

## 整理已有导出

整理不会删除或改写原始 `messages.json` 和 `media/`。运行 `python -m qqbot.organize --source <原始导出>/messages.json`，结果会写入私有的 `runtime/private/qq_essence_organized/`，包含分类索引、独立 Markdown 文档和媒体副本。重复内容只在 `index.json` 中标记，进入正式知识库前仍需人工核验。

## 不迁移的草稿内容

`probe/`、`probe2/`、`diagnose/`、`auto-probe/` 是一次性接口探测和重复导出，不属于运行代码；完整历史导出属于私有资料，不进入 Git。
