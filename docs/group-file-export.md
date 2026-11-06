# QQ 群文件导出

NapCat 提供 `get_group_root_files`、`get_group_files_by_folder` 和 `get_file`。毯毯用这些接口查询并下载选定文件。默认使用 QQ 原生下载，不需要 PacketBackend。`QQBOT_GROUP_FILE_TRANSPORT=url` 可切换到 `get_group_file_url`，但当前安装的 QQ 版本与 PacketBackend 不兼容，该模式会报错。

## 群内使用

麦麦可以用 `underline_list_group_files` 查询当前群文件。可以直接说“查一下群文件里的教程”，由模型决定是否查询。

管理员可发送 `/毯 把群文件中的某某文件导出到 underline_wiki，保留来源`。管理员 QQ 号由 `QQBOT_ADMIN_IDS` 配置。服务从实际消息确定身份，插件无法取得导出权限。

先使用 `list_group_files` 取得真实 `file_id`。文件夹中的文件同时需要列表里的 `folder_id`。列表按当前文件夹返回，文件夹排在前面。可用 `keyword` 筛选名称，用 `offset` 和 `next_offset` 分页。不会递归导出全部群文件。

当前 NapCat 每次列出同一个文件时，会创建新 `file_id`。服务将真实查询结果按群保存在 SQLite，导出时用原文件名、上传者和上传时间重新定位并取得当前 ID。有多个同来源候选时会报错。来源缓存每群最多保留 20000 个 ID，旧 ID 失效后需重新查询。

## 本机接口

- `GET /api/group-files?group_id=100000001`：查根目录。
- `GET /api/group-files?group_id=100000001&folder_id=...&keyword=...&offset=0`：查文件夹。
- `POST /api/group-files/export`：导出一个文件，请求体如下。

```json
{"group_id":"100000001","file_id":"列表返回的 ID","folder_id":""}
```

这些接口遵循现有本机管理服务的权限边界：只接受本机连接和已配置的群。不要将管理端口转发到公网。本机导出记录任务和工具审计。

## 输出与限制

输出位置由 `UNDERLINE_WIKI_ROOT` 设置。文件保存到 `qq_group_files/群号/来源哈希/内容SHA256/安全文件名`，来源 JSON 保存在来源目录。JSON 包含原文件名、群号、文件夹 ID、上传者、接口返回的时间、文件大小、SHA256 和导出时间。接口中的未知字段仍为未知，时间 0 不作已知时间。

返回 `exported` 或 `already_exported` 表示有实际文件和来源清单。同一来源的相同元数据会检查本地校验值并复用文件，不重复下载。元数据变化后重新下载，旧版本保留。人工修改的文件不会被覆盖。

这是原文件收集接口。压缩包、PDF、代码等原样保存，不执行、不解压、不自动视为已验证知识。下载地址不写入来源清单或工具结果。

默认单文件上限为 64 MiB。`QQBOT_GROUP_FILE_MAX_BYTES` 可调低，最高仍为 64 MiB。原生模式先检查列表中的大小，再检查 NapCat 下载结果及导出大小。QQ 下载时间由 NapCat 控制。URL 模式的网络超时为 20 秒，读取总时限为 60 秒。下载失败不会产生成功回执。文件名和目录检查阻止写出 Wiki 根目录。

代码更新后，重启资料服务与 MaiBot，工具才会加载。
