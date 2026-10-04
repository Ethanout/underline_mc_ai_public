# 已归档：毯毯的拟人部分

2026-10-05 起，群聊回复交给 MaiBot（麦麦）：人设、插话时机、表达学习、长期记忆、表情和看图都由它负责。我们这边只做工具调用和群知识库，见 `apps/maibot_plugin/`。

这里的代码不再被导入，也不在测试路径里。留着是因为有几样 MaiBot 没有，以后想移植成插件时可以参考：

| 文件 | 做什么 | MaiBot 里对应的 |
|---|---|---|
| `brain.py` | 168 格活跃画像、6 维情绪向量、判断模型（说完没有、要不要说） | 只有 `emotion_trait` 一个枚举；插话时机由 maisaka 的 turn trigger 负责 |
| `style_memory.py`、`embedding.py` | 每群 ChromaDB，文字和图片同一个向量空间的相似句检索 | 表达学习是「当X时可以Y」规则对，不检索原句，也不收图 |
| `style_notes.py` | 定期让模型写风格笔记，代码检查不抄原句、不点名 | 表达自省、行为学习 |
| `memory_model.py`、`runtime.py` | 幂律遗忘、睡眠整理、只模拟不删；白名单可调参数 | A_memorix：指数半衰期、冻结/复活/回收站 |
| `persona_prompts.py` | 毯毯人设全文 | 填进 MaiBot 的 `[personality]` |

`runtime/private/qq_style/`（ChromaDB）和 `qqbot.db` 里的 `memory_state`、`brain:*` 状态都原样留在磁盘上，没有删。

代码和测试里的导入还是 `qqbot.xxx`，想恢复就 `git mv` 回 `src/qqbot/` 和 `tests/`。归档时的最后一个可运行版本是提交 7c9cdeb。
