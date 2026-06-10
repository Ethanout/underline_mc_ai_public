# r/MinecraftCommands 归档

抓取器使用 Arctic Shift 的公开历史接口获取：

- `r/MinecraftCommands` 帖子
- Arctic Shift 归档中可获取的评论
- 根据 `parent_id` 重建的回复树
- 分数、标签、作者、时间和原链接

默认仅保留带 `Help | Java ...` 标签且至少有一条评论的帖子。`--max-posts`
表示最终保留的匹配帖子数；爬虫最多扫描配置项 `max_scan_posts` 指定的候选帖子。
单个帖子的评论会自动分页，并根据 `parent_id` 重建回复树。

注意：公开归档不保证包含 Reddit 上曾经存在的每条评论；已删除、未及时收录或
归档服务缺失的评论可能无法获取。

## 小批量检查

```powershell
python -m modules.crawlers.reddit_minecraftcommands --max-posts 20 --dry-run
```

## 正式抓取

```powershell
python -m modules.crawlers.reddit_minecraftcommands --max-posts 100
```

结果保存到：

```text
data/sources/raw/reddit_minecraftcommands.json
```

配置位于：

```text
config/crawlers/reddit_minecraftcommands.json
```

`before` 和 `after` 参数接受 Unix 时间戳，可用于按时间范围抓取。
