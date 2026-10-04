# underline_tools：给麦麦用的毯毯工具插件

麦麦（MaiBot 1.3.x）负责群聊。这个插件做两件事：

- 给麦麦三个只读工具：`underline_search_knowledge`（群技巧库 + 聊天记录）、`underline_search_chat`（聊天记录）、`underline_read_essence`（群精华）。麦麦聊天时觉得要查就会调。
- 拦下以 `/毯` 开头的消息，麦麦不接这句。这条消息由毯毯的 web 服务从 NapCat 推送里接手，按发送者真实 QQ 号定权限后回复。

插件不保存任何权限。工具以无权限的 `maibot` 身份调用本机的毯毯服务，服务端再检查工具名、群号白名单（`QQBOT_GROUPS`）和插件 token。

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

- 毯毯的 web 在跑，`/api/health` 里 `plugin_token_configured` 是 `true`。
- 群里问麦麦一句和技巧库相关的问题，`/api/audit` 里能看到 `maibot` 的调用。
- 群里发 `/毯 查一下 execute`：麦麦不接话，毯毯回复那条消息。

## 测试

`tests/test_maibot_plugin.py` 用一个假的 `maibot_sdk` 跑，不需要装麦麦，也不联网。
