# Underline Tricks Collector 工作区

当前保留 QQ 精华采集器，作为 Collector 的开发起点。旧 Python RAG、知识控制台、爬取管线和验证器已归档。知识资料迁往相邻目录 `../underline_wiki/`，后续检索以该 wiki 为来源。新的 wiki 接入尚未实现。

## 快速开始

```powershell
python -m pip install -e "apps/qqbot[style]"
copy .env.example .env   # 填 NAPCAT_DIR 和 key 文件路径，只填这一次
.\start_ui.bat           # 同步 NapCat 配置 -> 起 web -> 起 NapCat
# http://127.0.0.1:18787
```

详见 `apps/qqbot/README.md` 的「一键启动」。

## 当前目录

| 目录 | 职责 |
|---|---|
| `apps/qqbot/` | 经授权的 OneBot/NapCat 群精华采集；导出资料默认保持私有并先经人工审阅 |
| `../underline_wiki/` | 独立的知识资产目录，由提取任务整理 |
| `runtime/private/` | 私有 QQ 消息与整理结果，不进入 Git |
| `config/api/` | 旧本地密钥，保留且不进入 Git |
| `tests/` | 当前 QQ 采集与整理测试 |
| `tools/` | 归档操作工具 |
| `.archive/` | 待删除的临时历史资料，不参与运行或版本管理 |

旧知识和旧实现已退出活动代码。`.archive/` 是待删除的临时目录；删除它不影响当前 QQ 模块。提取到 `../underline_wiki/` 的资料保留原位，目前也没有接入运行代码。

## 常用命令

```powershell
python -m unittest discover -s tests -v
python -m qqbot.essence_exporter --help
```

当前状态见 `docs/WORKSPACE_STATUS.md`，待办见 `TODO.md`。QQ 工具用法见 `apps/qqbot/README.md`。
