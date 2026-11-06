# underline_tools：给麦麦用的毯毯工具插件

麦麦（MaiBot 1.3.x）负责群聊。这个插件做两件事：

- 给麦麦查询工具：`underline_search_knowledge`（群技巧库 + Underline 教学和文档 + mcfunction 笔记 + 聊天记录）、`underline_search_chat`（聊天记录）、`underline_read_essence`（群精华）。
  - 知识库来源：群里积累的技巧库（AI 整理，未实测），Underline 平行线教程，命令和性能文档，存档的中文 Wiki 页面，mcfunction 工程笔记，群聊天记录。
- 研究工具：`underline_web_search` 搜索网页，`underline_web_read` 读取并保存来源，`underline_save_research` 整理带来源的知识，`underline_recall_work` 回忆本群实际工具记录。
- 拦下以 `/毯` 开头的消息，麦麦不接这句。这条消息由毯毯的 web 服务从 NapCat 推送里接手，按发送者真实 QQ 号定权限后回复。

插件不保存任何权限。工具以无权限的 `maibot` 身份调用本机的毯毯服务，服务端再检查工具名、群号白名单（`QQBOT_GROUPS`）和插件 token。

研究工具可追加未验证资料，不能调用任意文件、终端或 SQL。日期工作区、技术标签和 Wiki 导出说明见 [agent-research.md](../../../docs/agent-research.md)。

## 安装

用目录联接装进麦麦的 `plugins/`，这样插件始终是仓库里的最新版本，token 文件路径也能自动找到。在 PowerShell 里：

```powershell
cmd /c mklink /J "D:\projects\MaiBot\plugins\underline_tools" "D:\重要的资料\项目\__mc\underline_mc_ai\apps\maibot_plugin\underline_tools"
```

然后在麦麦里启用 `Underline 工具` 插件。麦麦会在插件目录生成 `config.toml`（已被本仓库忽略）：

```toml
[plugin]
enabled = true

[service]
service_url = "http://127.0.0.1:18787"   # 和 .env 的 QQBOT_WEB_PORT 一致
token_file = ""                           # 留空：用仓库的 config/api/qqbot_plugin.txt
timeout_seconds = 20.0
```

如果不用目录联接而是复制过去，`token_file` 要填 token 文件的完整路径。token 文件在 `.env` 设了 `MAIBOT_DIR` 后，第一次启动毯毯时自动生成。

## 检查

跨群工具 `underline_list_groups` 同时列出本地已知的 `qq` 和 `qq_official` 会话。
官方端使用完整的 `official:AppID:OpenID` 作为 `target_group`，也能通过端管理中显式绑定的旧群号定位。
同名或多个目标无法唯一确定时，工具要求选择完整ID。绑定服务不可用时，完整官方ID仍可用。
`underline_chat_in_group` 成功只表示目标群已接收发言任务，不表示实际消息已发送；机器人不能把排队说成已发出。

- 毯毯的 web 在跑，`/api/health` 里 `plugin_token_configured` 是 `true`。
- 群里问麦麦一句和技巧库相关的问题，`/api/audit` 里能看到 `maibot` 的调用。
- 群里发 `/毯 查一下 execute`：麦麦不接话，毯毯回复那条消息。

## 测试

`tests/test_maibot_plugin.py` 用一个假的 `maibot_sdk` 跑，不需要装麦麦，也不联网。
