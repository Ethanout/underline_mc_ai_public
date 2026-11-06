# 毯毯 QQ 官方适配器

独立的麦麦 SDK 消息网关，不修改 NapCat 或麦麦主程序。配置、启停和连接状态统一放在毯毯资料服务首页。

在 underline_mc_ai 工作区运行 `.venv\Scripts\python.exe -m qqbot install-official`，然后重载麦麦插件。源码保存在本项目，部署副本位于 `MaiBot/plugins/underline_qq_official`，有独立 Git 仓库。

运行依赖使用麦麦现有的 `maibot_sdk`、`aiohttp`、Pillow。`config.toml` 仅保存本机管理服务地址、插件 token 文件路径和状态目录。官方 AppSecret 不写入插件配置，由已认证的本机服务提供。

支持：官方 WebSocket 接入、凭证刷新、断线 Resume、群聊/私聊、全量群消息开关、白名单、文本与小图片收发、引用发送、事件去重和回复序号持久化。GIF/WebP 发送时转为首帧 PNG，不发送动画。单张发送图片限制为 5 MiB，接收最多下载 8 MiB。

官方端平台名为 `qq_official`；群与用户标识使用 `official:<AppID>:<OpenID>`，与原有 `qq` 平台数据隔离。不会自动认领旧群、人物记忆或管理员权限。引用/合并聊天只读取官方事件实际提供的内容；文本 @ 目前仅作可读展示，不承诺触发客户端提及。

群精华枚举、群文件全量导出、长期历史补取与旧身份绑定尚未接入，继续使用 NapCat。官方群被动回复 5 分钟内最多 5 条，单聊 60 分钟内最多 4 条；主动发送需开启本机配置并获得官方权限。发送失败不自动切换到主动发送或无限重试。
# 昵称与头像

适配器保存官方事件实际提供的用户昵称、群名片、群名称和头像地址。
后续事件缺少这些字段时使用已保存的值；群名片按群隔离。
`adapter.profile.get` 返回已观察到的资料，`adapter.avatar.get` 接入麦麦头像缓存与 WebUI。
两者按 AppID 和端路由匹配。官方未提供的头像返回 `missing`，不把 OpenID 当 QQ 号拼头像链接。

