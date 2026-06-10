"""Archive r/MinecraftCommands posts and reconstruct their comment trees."""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

from ..config import RAW_DIR, REDDIT_MCC_CONFIG


DEFAULT_API = "https://arctic-shift.photon-reddit.com/api"
REMOVED_TEXT = {"", "[deleted]", "[removed]"}


def load_config(path: Path = REDDIT_MCC_CONFIG) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    data.setdefault("api_base", DEFAULT_API)
    data.setdefault("subreddit", "MinecraftCommands")
    data.setdefault("proxy", "")
    data.setdefault("request_delay_seconds", 0.25)
    data.setdefault("max_scan_posts", 1000)
    data.setdefault("java_only", True)
    data.setdefault("help_only", True)
    data.setdefault("min_comments", 1)
    data.setdefault("min_comment_score", 1)
    return data


def _clean_text(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text in REMOVED_TEXT else text


def _full_name(prefix: str, value: Any) -> str:
    text = str(value or "")
    return text if text.startswith(prefix) else f"{prefix}{text}"


def build_comment_tree(comments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a nested tree while preserving orphaned comments as roots."""
    nodes: dict[str, dict[str, Any]] = {}
    for comment in comments:
        comment_id = _full_name("t1_", comment.get("id"))
        nodes[comment_id] = {
            "id": comment_id,
            "parent_id": comment.get("parent_id", ""),
            "author": comment.get("author", ""),
            "author_flair": comment.get("author_flair_text", ""),
            "body": _clean_text(comment.get("body")),
            "score": comment.get("score", 0),
            "created_utc": comment.get("created_utc"),
            "permalink": comment.get("permalink", ""),
            "is_submitter": bool(comment.get("is_submitter")),
            "distinguished": comment.get("distinguished"),
            "replies": [],
        }

    roots: list[dict[str, Any]] = []
    for node in nodes.values():
        parent = nodes.get(node["parent_id"])
        if parent is None:
            roots.append(node)
        else:
            parent["replies"].append(node)

    def sort_tree(items: list[dict[str, Any]]):
        items.sort(key=lambda item: (-int(item.get("score") or 0), item.get("created_utc") or 0))
        for item in items:
            sort_tree(item["replies"])

    sort_tree(roots)
    return roots


def flatten_comment_tree(tree: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []

    def visit(items: list[dict[str, Any]], depth: int):
        for item in items:
            copy = {key: value for key, value in item.items() if key != "replies"}
            copy["depth"] = depth
            flattened.append(copy)
            visit(item["replies"], depth + 1)

    visit(tree, 0)
    return flattened


def post_matches(post: dict[str, Any], config: dict[str, Any]) -> bool:
    flair = str(post.get("link_flair_text") or "").lower()
    if config["java_only"] and "java" not in flair:
        return False
    if config["help_only"] and "help" not in flair:
        return False
    if int(post.get("num_comments") or 0) < int(config["min_comments"]):
        return False
    if _clean_text(post.get("selftext")) == "" and not post.get("url"):
        return False
    return True


def build_article(
    post: dict[str, Any], comments: list[dict[str, Any]], min_comment_score: int = 1
) -> dict[str, Any]:
    tree = build_comment_tree(comments)
    flat = flatten_comment_tree(tree)
    useful = [
        comment
        for comment in flat
        if comment["body"]
        and (
            int(comment.get("score") or 0) >= min_comment_score
            or comment.get("distinguished")
            or comment.get("is_submitter")
        )
    ]

    content_parts = [
        f"# {post.get('title', '')}",
        f"Flair: {post.get('link_flair_text', '')}",
        f"Post score: {post.get('score', 0)}",
        "",
        _clean_text(post.get("selftext")) or f"External link: {post.get('url', '')}",
    ]
    if useful:
        content_parts.extend(["", "## Comments"])
        for comment in useful:
            indent = "  " * min(int(comment["depth"]), 4)
            content_parts.append(
                f"{indent}- **{comment['author']}** (score {comment['score']}): "
                f"{comment['body']}"
            )

    content = "\n".join(content_parts)
    permalink = post.get("permalink", "")
    source_url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else post.get("url", "")
    digest = hashlib.sha256(
        (
            str(post.get("id"))
            + _clean_text(post.get("selftext"))
            + "".join(comment["id"] + comment["body"] for comment in flat)
        ).encode("utf-8")
    ).hexdigest()[:16]

    return {
        "id": f"reddit_mcc_{post['id']}",
        "title": post.get("title", ""),
        "url": source_url,
        "content": content,
        "source_type": "mcc_reddit",
        "source_issue": post["id"],
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "content_hash": digest,
        "post": {
            "id": _full_name("t3_", post["id"]),
            "author": post.get("author", ""),
            "title": post.get("title", ""),
            "selftext": _clean_text(post.get("selftext")),
            "score": post.get("score", 0),
            "upvote_ratio": post.get("upvote_ratio"),
            "num_comments": post.get("num_comments", 0),
            "created_utc": post.get("created_utc"),
            "flair": post.get("link_flair_text", ""),
            "permalink": permalink,
        },
        "comment_tree": tree,
        "comments": flat,
        "useful_comment_count": len(useful),
    }


class MinecraftCommandsRedditCrawler:
    def __init__(self, config: Optional[dict[str, Any]] = None, output_dir: Optional[Path] = None):
        self.config = config or load_config()
        self.output_dir = output_dir or RAW_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "underline-mc-ai/0.1 public archive importer"
        proxy = self.config.get("proxy")
        if proxy:
            self.session.proxies.update({"http": proxy, "https": proxy})

    def _get(self, endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        url = f"{self.config['api_base'].rstrip('/')}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise RuntimeError(str(payload["error"]))
        return payload.get("data", [])

    def fetch_posts(
        self, max_posts: int, before: Optional[int] = None, after: Optional[int] = None
    ) -> list[dict[str, Any]]:
        posts: list[dict[str, Any]] = []
        cursor = before
        while len(posts) < max_posts:
            batch_limit = min(100, max_posts - len(posts))
            params: dict[str, Any] = {
                "subreddit": self.config["subreddit"],
                "limit": batch_limit,
                "sort": "desc",
            }
            if cursor:
                params["before"] = cursor
            if after:
                params["after"] = after
            batch = self._get("posts/search", params)
            if not batch:
                break
            posts.extend(batch)
            oldest = min(int(post.get("created_utc") or 0) for post in batch)
            if not oldest or oldest == cursor:
                break
            cursor = oldest - 1
            time.sleep(float(self.config["request_delay_seconds"]))
        return posts[:max_posts]

    def fetch_matching_posts(
        self, max_posts: int, before: Optional[int] = None, after: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """Fetch until max_posts matching threads are found or the scan limit is reached."""
        selected: list[dict[str, Any]] = []
        cursor = before
        scanned = 0
        max_scan_posts = max(max_posts, int(self.config["max_scan_posts"]))

        while len(selected) < max_posts and scanned < max_scan_posts:
            batch_size = min(100, max_scan_posts - scanned)
            batch = self.fetch_posts(max_posts=batch_size, before=cursor, after=after)
            if not batch:
                break
            scanned += len(batch)
            selected.extend(post for post in batch if post_matches(post, self.config))
            oldest = min(int(post.get("created_utc") or 0) for post in batch)
            if not oldest or oldest == cursor:
                break
            cursor = oldest - 1

        print(f"Scanned {scanned} posts; selected {min(len(selected), max_posts)} matching threads")
        return selected[:max_posts]

    def fetch_comments(self, post_id: str) -> list[dict[str, Any]]:
        comments: list[dict[str, Any]] = []
        cursor: Optional[int] = None
        seen_ids: set[str] = set()
        while True:
            params: dict[str, Any] = {"link_id": post_id, "limit": 100, "sort": "asc"}
            if cursor is not None:
                params["after"] = cursor
            batch = self._get("comments/search", params)
            fresh = [comment for comment in batch if str(comment.get("id")) not in seen_ids]
            comments.extend(fresh)
            seen_ids.update(str(comment.get("id")) for comment in fresh)
            if len(batch) < 100:
                break
            newest = max(int(comment.get("created_utc") or 0) for comment in batch)
            if not newest or newest == cursor:
                break
            cursor = newest
            time.sleep(float(self.config["request_delay_seconds"]))
        return comments

    def crawl(
        self, max_posts: int = 20, before: Optional[int] = None, after: Optional[int] = None
    ) -> list[dict[str, Any]]:
        selected = self.fetch_matching_posts(max_posts=max_posts, before=before, after=after)
        articles: list[dict[str, Any]] = []
        for index, post in enumerate(selected, 1):
            comments = self.fetch_comments(post["id"])
            articles.append(
                build_article(
                    post,
                    comments,
                    min_comment_score=int(self.config["min_comment_score"]),
                )
            )
            print(
                f"[{index}/{len(selected)}] {post.get('link_flair_text', '')} | "
                f"{post.get('title', '')[:70]} | comments={len(comments)}"
            )
            time.sleep(float(self.config["request_delay_seconds"]))
        return articles

    def save_articles(self, articles: list[dict[str, Any]], dry_run: bool = False) -> dict[str, Any]:
        output = self.output_dir / "reddit_minecraftcommands.json"
        existing: list[dict[str, Any]] = []
        if output.exists():
            loaded = json.loads(output.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                existing = loaded
        by_id = {article["id"]: article for article in existing}
        added = updated = 0
        for article in articles:
            previous = by_id.get(article["id"])
            if previous is None:
                added += 1
            elif previous.get("content_hash") != article["content_hash"]:
                updated += 1
            by_id[article["id"]] = article
        merged = sorted(
            by_id.values(), key=lambda article: article.get("post", {}).get("created_utc") or 0
        )
        if not dry_run and (added or updated or not output.exists()):
            output.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        comments = [comment for article in articles for comment in article["comments"]]
        return {
            "ok": True,
            "fetched": len(articles),
            "fetched_comments": len(comments),
            "nested_threads": sum(
                any(comment["depth"] > 0 for comment in article["comments"]) for article in articles
            ),
            "max_comment_depth": max((comment["depth"] for comment in comments), default=0),
            "added": added,
            "updated": updated,
            "total": len(merged),
            "output": str(output),
            "dry_run": dry_run,
        }


def run(
    max_posts: int = 20,
    before: Optional[int] = None,
    after: Optional[int] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    crawler = MinecraftCommandsRedditCrawler()
    articles = crawler.crawl(max_posts=max_posts, before=before, after=after)
    return crawler.save_articles(articles, dry_run=dry_run)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Archive r/MinecraftCommands Java help threads")
    parser.add_argument("--max-posts", type=int, default=20)
    parser.add_argument("--before", type=int, help="Unix timestamp")
    parser.add_argument("--after", type=int, help="Unix timestamp")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = run(args.max_posts, args.before, args.after, args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
