"""Crawl the primary curated sources and import manual unstructured notes."""

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

from ..config import ARCHIVE_INBOX_DIR, INBOX_DIR, RAW_DIR


DATAPACK_WIKI_BASE = "https://datapack.wiki"
MCC_QUESTIONS_URL = "https://minecraftcommands.github.io/wiki/questions"
REMOVED_ELEMENTS = ["nav", "aside", "footer", "script", "style"]


class KnowledgeSourceCrawler:
    def __init__(self, delay_seconds: float = 0.2):
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "underline-mc-ai/0.1 curated-source-crawler"
        RAW_DIR.mkdir(parents=True, exist_ok=True)

    def _get(self, url: str) -> requests.Response:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response

    @staticmethod
    def _extract_page(url: str, html: str, source_type: str, article_id: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        root = (
            soup.select_one(".vp-doc")
            or soup.select_one(".markdown-body")
            or soup.find("main")
            or soup.find("article")
            or soup.body
        )
        if root is None:
            root = soup
        for element in root.select(",".join(REMOVED_ELEMENTS)):
            element.decompose()

        headings = [
            heading.get_text(" ", strip=True)
            for heading in root.find_all("h1")
            if heading.get_text(" ", strip=True).lower() != "wiki"
        ]
        if headings:
            title = headings[0]
        elif soup.title:
            title = soup.title.get_text(" ", strip=True).split("|", 1)[0].strip()
        else:
            title = url
        for heading in root.find_all("h1"):
            if heading.get_text(" ", strip=True).lower() == "wiki":
                heading.decompose()
        code_blocks = []
        for pre in root.find_all("pre"):
            code = pre.find("code")
            language = ""
            if code:
                for class_name in code.get("class", []):
                    if class_name.startswith("language-"):
                        language = class_name.removeprefix("language-")
            code_blocks.append({"lang": language, "code": pre.get_text("\n", strip=True)})

        return {
            "id": article_id,
            "title": title,
            "url": url,
            "content": root.get_text("\n", strip=True),
            "code_blocks": code_blocks,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "source_type": source_type,
        }

    @staticmethod
    def _save(filename: str, articles: list[dict[str, Any]]) -> Path:
        output = RAW_DIR / filename
        output.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
        return output

    def crawl_datapack_wiki(self) -> list[dict[str, Any]]:
        sitemap = self._get(f"{DATAPACK_WIKI_BASE}/sitemap.xml").text
        root = ElementTree.fromstring(sitemap)
        urls = sorted(
            {
                (element.text or "").strip()
                for element in root.findall(".//{*}loc")
                if (element.text or "").strip().startswith(DATAPACK_WIKI_BASE)
            }
        )
        articles = []
        for index, url in enumerate(urls, 1):
            path = urlparse(url).path.strip("/") or "index"
            article_id = "dpwiki_" + re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_")
            article = self._extract_page(url, self._get(url).text, "datapack_wiki", article_id)
            if len(article["content"]) >= 100:
                articles.append(article)
            print(f"[datapack.wiki {index}/{len(urls)}] {article['title'][:70]}")
            time.sleep(self.delay_seconds)
        self._save("datapack_wiki.json", articles)
        return articles

    def crawl_mcc_questions(self) -> list[dict[str, Any]]:
        index_html = self._get(MCC_QUESTIONS_URL).text
        soup = BeautifulSoup(index_html, "html.parser")
        links = set()
        for anchor in soup.find_all("a", href=True):
            url = urldefrag(urljoin(MCC_QUESTIONS_URL + "/", anchor["href"]))[0].rstrip("/")
            if url.startswith(MCC_QUESTIONS_URL + "/"):
                links.add(url)

        articles = []
        for index, url in enumerate(sorted(links), 1):
            slug = url.rsplit("/", 1)[-1]
            article = self._extract_page(url, self._get(url).text, "mcc_wiki", f"mcc_{slug}")
            if len(article["content"]) >= 100:
                articles.append(article)
            print(f"[MCC Questions {index}/{len(links)}] {article['title'][:70]}")
            time.sleep(self.delay_seconds)
        self._save("mcc_questions.json", articles)
        return articles

    @staticmethod
    def _manual_article(path: Path, source_file: str, external: bool = False) -> dict[str, Any] | None:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return None
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = path.stem if external else (title_match.group(1).strip() if title_match else path.stem)
        hint_match = re.search(r"<!--\s*hint:\s*(.*?)\s*-->", content, re.DOTALL)
        source_url = hint_match.group(1).strip() if hint_match else ""
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        code_blocks = [
            {"lang": match.group(1).strip(), "code": match.group(2).strip()}
            for match in re.finditer(r"```([^\n`]*)\n(.*?)```", content, re.DOTALL)
        ]
        suffix = f"_{digest[:8]}" if external else ""
        return {
            "id": f"manual_{path.stem}{suffix}",
            "title": title,
            "url": source_url,
            "content": content,
            "code_blocks": code_blocks,
            "source_file": source_file,
            "content_hash": digest,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "source_type": "manual",
        }

    def import_manual_notes(self, extra_files: list[Path] | None = None) -> list[dict[str, Any]]:
        output = RAW_DIR / "manual_notes.json"
        existing = json.loads(output.read_text(encoding="utf-8")) if output.exists() else []
        by_id = {article["id"]: article for article in existing if isinstance(article, dict)}

        articles = []
        locations = [
            (INBOX_DIR, "inbox"),
            (ARCHIVE_INBOX_DIR, "archive/inbox"),
        ]
        for directory, label in locations:
            for path in sorted(directory.glob("*.md")):
                article = self._manual_article(path, f"{label}/{path.name}")
                if article:
                    articles.append(article)
                    print(f"[manual {label}] {path.name} | {article['title'][:70]}")
        for article in articles:
            by_id[article["id"]] = article
        for path in extra_files or []:
            article = self._manual_article(path, str(path), external=True)
            if article:
                by_id[article["id"]] = article
                print(f"[manual external] {path.name} | {article['title'][:70]}")
        merged = sorted(by_id.values(), key=lambda article: article["id"])
        self._save("manual_notes.json", merged)
        return merged


def run(
    source: str = "all",
    delay_seconds: float = 0.2,
    manual_files: list[Path] | None = None,
) -> dict[str, Any]:
    crawler = KnowledgeSourceCrawler(delay_seconds=delay_seconds)
    results: dict[str, Any] = {"ok": True, "sources": {}}
    if source in ("all", "datapack_wiki"):
        results["sources"]["datapack_wiki"] = len(crawler.crawl_datapack_wiki())
    if source in ("all", "mcc_questions"):
        results["sources"]["mcc_questions"] = len(crawler.crawl_mcc_questions())
    if source in ("all", "manual"):
        results["sources"]["manual"] = len(crawler.import_manual_notes(manual_files))
    results["total"] = sum(results["sources"].values())
    return results


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Crawl curated knowledge sources")
    parser.add_argument(
        "--source",
        choices=["all", "datapack_wiki", "mcc_questions", "manual"],
        default="all",
    )
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between requests in seconds")
    parser.add_argument(
        "--manual-file",
        type=Path,
        action="append",
        default=[],
        help="Additional UTF-8 .txt or .md file to preserve as a manual source",
    )
    args = parser.parse_args()
    missing = [str(path) for path in args.manual_file if not path.is_file()]
    if missing:
        parser.error(f"manual files not found: {', '.join(missing)}")
    print(json.dumps(run(args.source, args.delay, args.manual_file), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
