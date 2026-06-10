"""
Minecraft Wiki 爬虫 —— 灵活底层 + CLI 特化上层

底层 WikiCrawler 接受 wiki/lang/output_dir 等参数，不写死任何路径。
上层 main() 给 CLI 使用，提供默认值和参数解析。
modules.crawlers.wiki_crawler 可被其它模块导入做程序化调用。
"""
import sys
import json
import re
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import OrderedDict

from ..config import RAW_DIR, PROJECT_ROOT

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[错误] pip install requests beautifulsoup4")

# ═══ 数据（中文 / 英文 Wiki 配置） ═══

DP_KEYWORDS = [
    "命令", "数据包", "进度", "谓词", "战利品", "函数", "标签",
    "配方", "维度", "世界生成", "物品修饰", "存储", "NBT",
    "execute", "scoreboard", "advancement", "predicate", "loot",
    "mcfunction", "datapack", "tag", "recipe", "dimension",
]

SEED_PAGES_ZH = [
    "命令/execute", "命令/scoreboard", "命令/advancement", "命令/data",
    "命令/function", "命令/forceload", "命令/loot", "命令/item",
    "命令/return", "命令/schedule", "命令/tag", "命令/team",
    "数据包", "进度", "谓词", "战利品表", "标签", "配方",
    "物品修饰器", "自定义世界生成", "函数", "结构",
    "命令上下文", "存储", "NBT", "JSON格式",
    "命令/summon", "命令/give", "命令/setblock", "命令/fill",
    "命令/clone", "命令/tp", "命令/teleport",
]

SEED_PAGES_EN = [
    "Commands/execute", "Commands/scoreboard", "Commands/advancement", "Commands/data",
    "Commands/function", "Commands/loot", "Commands/item",
    "Commands/return", "Commands/schedule",
    "Data pack", "Advancement", "Predicate", "Loot table", "Tag",
    "Recipe", "Item modifier", "Custom world generation", "Function (Java Edition)",
    "Storage", "NBT", "Commands/summon", "Commands/give",
]

WIKI_CONFIGS = {
    "zh": {
        "name": "中文 Minecraft Wiki",
        "api_url": "https://zh.minecraft.wiki/api.php",
        "base_url": "https://zh.minecraft.wiki",
        "seed_pages": SEED_PAGES_ZH,
        "search_terms": [
            "execute 命令", "scoreboard", "数据包开发",
            "advancement", "predicate", "loot_table",
            "mcfunction", "storage", "NBT",
        ],
    },
    "en": {
        "name": "English Minecraft Wiki",
        "api_url": "https://minecraft.wiki/w/api.php",
        "base_url": "https://minecraft.wiki",
        "seed_pages": SEED_PAGES_EN,
        "search_terms": [
            "execute command", "scoreboard", "datapack development",
            "advancement", "predicate", "loot_table",
            "mcfunction", "storage", "NBT path",
        ],
    },
}

VERSION_PATTERN = re.compile(
    r'^(Java版|基岩版|原主机版)\d|^1\.\d|^\d{2}w\d{2}|^Java版$', re.IGNORECASE
)


def _is_high_priority(title: str) -> bool:
    t = title.lower()
    return any(kw.lower() in t for kw in DP_KEYWORDS)


# ═══ 底层：灵活的 WikiCrawler ═══

class WikiCrawler:
    """Minecraft Wiki 爬虫 — 所有参数可配置，不写死路径"""

    def __init__(self, wiki: str = "zh", output_dir: Path = None):
        cfg = WIKI_CONFIGS.get(wiki, WIKI_CONFIGS["zh"])
        self.name = cfg["name"]
        self.api_url = cfg["api_url"]
        self.base_url = cfg["base_url"]
        self.default_search_terms = cfg["search_terms"]
        self.seed_pages = cfg.get("seed_pages", [])
        self.output_dir = output_dir or RAW_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MinecraftDatapackKB/1.0 (knowledge base crawler; respectful crawling)"
        })

    # ── API 基础 ──

    def _api_get(self, params: dict) -> Optional[dict]:
        params["format"] = "json"
        try:
            resp = self.session.get(self.api_url, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"  API 错误: {e}")
            return None

    def get_page_wikitext(self, title: str) -> Optional[str]:
        data = self._api_get({
            "action": "query", "titles": title,
            "prop": "revisions", "rvprop": "content", "rvlimit": "1",
        })
        if not data:
            return None
        for page_info in data.get("query", {}).get("pages", {}).values():
            if page_info.get("pageid", -1) < 0:
                return None
            revs = page_info.get("revisions", [])
            if revs:
                return revs[0].get("*", "")
        return None

    def get_page_html(self, title: str) -> Optional[str]:
        data = self._api_get({
            "action": "parse", "page": title, "prop": "text", "formatversion": "2",
        })
        if data and "parse" in data:
            return data["parse"].get("text")
        return None

    # ── HTML 解析 ──

    def _extract_from_html(self, html: str) -> Dict[str, Any]:
        from urllib.parse import unquote
        soup = BeautifulSoup(html, "html.parser")

        # 蓝链
        internal_links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.startswith("/w/"):
                continue
            raw = unquote(href[3:]).split("#")[0].split("?")[0]
            if not raw or len(raw) > 60:
                continue
            link_title = raw.replace("_", " ")
            if VERSION_PATTERN.match(link_title):
                continue
            if ":" in link_title:
                ns = link_title.split(":")[0]
                if ns not in ("命令", "Commands"):
                    continue
            internal_links.add(link_title)

        for el in soup.find_all(["nav", "aside", "footer", "script", "style", "table-of-contents"]):
            el.decompose()

        code_blocks = []
        for pre in soup.find_all("pre"):
            lang = ""
            code_el = pre.find("code")
            if code_el and code_el.get("class"):
                for cls in code_el["class"]:
                    if cls.startswith("language-") or cls.startswith("mw-"):
                        lang = cls.replace("language-", "").replace("mw-", "")
            code_text = pre.get_text(strip=True)
            if code_text and len(code_text) > 10:
                code_blocks.append({"language": lang, "code": code_text})

        text = soup.get_text(separator="\n", strip=True)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return {"text": text, "code_blocks": code_blocks, "internal_links": internal_links}

    # ── 灵活底层：页面爬取 ──

    def list_category_members(self, category: str) -> List[str]:
        pages = []
        cmcontinue = None
        while True:
            params = {
                "action": "query", "list": "categorymembers",
                "cmtitle": f"Category:{category}", "cmlimit": "50", "cmtype": "page",
            }
            if cmcontinue:
                params["cmcontinue"] = cmcontinue
            data = self._api_get(params)
            if not data:
                break
            for member in data.get("query", {}).get("categorymembers", []):
                if member.get("ns", 0) == 0:
                    pages.append(member["title"])
            cmcontinue = data.get("continue", {}).get("cmcontinue")
            if not cmcontinue:
                break
            time.sleep(0.3)
        return pages

    def search_pages(self, query: str, limit: int = 20) -> List[str]:
        data = self._api_get({
            "action": "query", "list": "search",
            "srsearch": query, "srlimit": str(limit),
        })
        if not data:
            return []
        pages = []
        for result in data.get("query", {}).get("search", []):
            title = result.get("title", "")
            if ":" not in title or title.split(":")[0] in ("Minecraft Wiki", "模块"):
                pages.append(title)
        return pages

    def crawl_page(self, title: str) -> Optional[Dict[str, Any]]:
        html = self.get_page_html(title)
        if not html:
            return None
        extracted = self._extract_from_html(html)
        safe_title = title.replace(" ", "_")
        return {
            "id": f"wiki_{re.sub(r'[^a-z0-9]', '_', title.lower())[:60]}",
            "title": title,
            "url": f"{self.base_url}/w/{safe_title}",
            "content": extracted["text"][:15000],
            "code_blocks": extracted["code_blocks"],
            "internal_links": list(extracted["internal_links"]),
            "scraped_at": datetime.now().isoformat(),
            "source_type": "mcc_wiki",
        }

    # ── 高级爬取模式 ──

    def crawl_deep(self, seed_pages: List[str] = None,
                   max_depth: int = 1, max_pages: int = 200) -> List[Dict[str, Any]]:
        """深度爬取：从种子页面出发，沿蓝链扩展"""
        if seed_pages is None:
            seed_pages = self.seed_pages

        visited = set()
        articles = []
        priority_queue = list(seed_pages)
        normal_queue = []

        while (priority_queue or normal_queue) and len(articles) < max_pages:
            title = priority_queue.pop(0) if priority_queue else normal_queue.pop(0)
            if title in visited or VERSION_PATTERN.match(title):
                continue
            visited.add(title)

            print(f"  [{len(articles) + 1}/{max_pages}] {title}")
            article = self.crawl_page(title)

            if article and len(article["content"]) > 100:
                articles.append(article)
                if max_depth > 0 and article.get("internal_links"):
                    for link in article["internal_links"]:
                        if link not in visited and not VERSION_PATTERN.match(link):
                            (priority_queue if _is_high_priority(link) else normal_queue).append(link)
            time.sleep(0.3)

        return articles

    def crawl_search(self, terms: List[str] = None) -> List[Dict[str, Any]]:
        """搜索式爬取"""
        if terms is None:
            terms = self.default_search_terms

        all_pages = OrderedDict()
        for term in terms:
            print(f"\n🔍 搜索: {term}")
            pages = self.search_pages(term)
            print(f"   找到 {len(pages)} 个结果")
            for page in pages:
                all_pages[page] = True

        print(f"\n共 {len(all_pages)} 个不重复页面")
        articles = []
        for i, title in enumerate(all_pages, 1):
            print(f"  [{i}/{len(all_pages)}] {title}")
            article = self.crawl_page(title)
            if article and len(article["content"]) > 100:
                articles.append(article)
            time.sleep(0.3)
        return articles

    # ── 特化接口：便捷方法 ──

    def crawl_all(self, categories: List[str] = None):
        """便捷：爬取分类下所有页面（用于其它模块快速调用）"""
        if categories is None:
            categories = [
                "Advancements", "Commands", "Data_packs",
                "Loot_tables", "Predicates",
            ]
        for cat in categories:
            print(f"\n📂 分类: {cat}")
            pages = self.list_category_members(cat)
            print(f"   找到 {len(pages)} 个页面")
            for i, page in enumerate(pages, 1):
                print(f"  [{i}/{len(pages)}] {page}")
                article = self.crawl_page(page)
                if article:
                    self._save_article(article)
                time.sleep(0.3)

    def crawl_related_pages(self, keywords: List[str]):
        """便捷：搜索关键词并爬取（兼容模块化调用）"""
        articles = self.crawl_search(keywords)
        for article in articles:
            self._save_article(article)

    def _save_article(self, article: Dict[str, Any]):
        """保存单篇文章到 output_dir"""
        existing = []
        out_file = self.output_dir / f"minecraft_wiki_{self.name.split()[0].lower()}.json"
        if out_file.exists():
            try:
                existing = json.loads(out_file.read_text(encoding="utf-8"))
                if not isinstance(existing, list):
                    existing = []
            except Exception:
                existing = []
        existing_ids = {a.get("id") for a in existing}
        if article["id"] not in existing_ids:
            existing.append(article)
            out_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_results(self, articles: List[Dict[str, Any]], out_name: str = None):
        """保存爬取结果（去重合并）"""
        out_name = out_name or f"minecraft_wiki_{self.name.split()[0].lower()}.json"
        out_file = self.output_dir / out_name

        existing = []
        if out_file.exists():
            try:
                existing = json.loads(out_file.read_text(encoding="utf-8"))
                if not isinstance(existing, list):
                    existing = []
            except Exception:
                existing = []

        existing_ids = {a.get("id") for a in existing}
        new_articles = [a for a in articles if a["id"] not in existing_ids]
        all_data = existing + new_articles

        out_file.write_text(json.dumps(all_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n共 {len(all_data)} 篇（新增 {len(new_articles)} 篇）-> {out_file}")


# ═══ 上层：CLI 特化 ═══

def main():
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Minecraft Wiki 爬虫")
    parser.add_argument("--wiki", choices=["zh", "en"], default="zh")
    parser.add_argument("--mode", choices=["search", "deep", "both"], default="deep")
    parser.add_argument("--search", nargs="*", help="搜索关键词")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 60)
    print(f"Wiki 爬虫 - {WIKI_CONFIGS[args.wiki]['name']}")
    print("=" * 60)

    crawler = WikiCrawler(wiki=args.wiki)
    all_articles = []

    if args.mode in ("search", "both"):
        terms = args.search or WIKI_CONFIGS[args.wiki]["search_terms"]
        all_articles.extend(crawler.crawl_search(terms))

    if args.mode in ("deep", "both"):
        all_articles.extend(crawler.crawl_deep(
            max_depth=args.depth, max_pages=args.max_pages,
        ))

    # 去重
    seen = set()
    unique = [a for a in all_articles if not (a["id"] in seen or seen.add(a["id"]))]

    if not unique:
        print("\n没有爬取到内容")
        return

    crawler.save_results(unique, args.output)
    print(f"\n下一步: python -m modules.crawlers.crawl_and_extract --phase extract")


if __name__ == "__main__":
    main()
