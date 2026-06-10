"""
crawl_and_extract.py
--------------------
两个阶段：
  Phase 1 (--phase crawl):  爬取所有源头，保存原始内容到 sources/raw/
  Phase 2 (--phase extract): 用 LLM 对每篇原始文章做逆向分析，提取 technique 条目

用法：
  python -m modules.crawlers.crawl_and_extract --phase crawl
  python -m modules.crawlers.crawl_and_extract --phase extract --model deepseek -j 20
  python -m modules.crawlers.crawl_and_extract --phase both   --model deepseek -j 20
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
import time
import threading
import argparse
import re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[错误] pip install requests beautifulsoup4")
    sys.exit(1)

from ..config import RAW_DIR, ENTRIES_DIR, API_DIR, build_index

TECH_DIR = ENTRIES_DIR
RAW_DIR.mkdir(parents=True, exist_ok=True)
TECH_DIR.mkdir(parents=True, exist_ok=True)

BASE = "https://cr-019.github.io/datapack-index"

# ── 所有已知月刊期号 ────────────────────────────────────────
FEATURE_ISSUES = [
    "202605","202604","202603","202602","202601",
    "202512","202511","202510","202509","202508",
    "202507","202506","202505","202504",
]

SESSION = requests.Session()
SESSION.headers["User-Agent"] = "Mozilla/5.0 (datapack-knowledge-crawler/1.0)"

# ══════════════════════════════════════════════════════════
# Phase 1: 爬取
# ══════════════════════════════════════════════════════════

def fetch_html(url: str, retries=3) -> str | None:
    for i in range(retries):
        try:
            r = SESSION.get(url, timeout=15)
            r.raise_for_status()
            return r.text
        except Exception as e:
            if i == retries - 1:
                print(f"  [FETCH ERR] {url}: {e}")
                return None
            time.sleep(1.5 ** i)


def extract_article_links_from_issue(issue: str) -> list[dict]:
    """从月刊目录页提取所有文章链接"""
    url = f"{BASE}/feature/index/{issue}.html"
    html = fetch_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        # 文章链接模式：../archive/YYYYMM/N/content  或绝对路径
        if f"archive/{issue}" in href and "content" in href:
            # 转成绝对 URL
            if href.startswith("../"):
                full = f"{BASE}/feature/{href[3:]}"
            elif href.startswith("/"):
                full = f"https://cr-019.github.io{href}"
            else:
                full = href

            # 找上级标题（通常在同一个 h3 或前一个 h3 下）
            title = a.get_text(strip=True) or href
            if full not in seen:
                seen.add(full)
                links.append({"issue": issue, "title": title, "url": full})

    return links


def extract_main_content(html: str) -> str:
    """从 VitePress 页面提取主体内容，去掉导航栏"""
    soup = BeautifulSoup(html, "html.parser")

    # VitePress 的正文在 .vp-doc 或 main 里
    content_div = (
        soup.find("div", class_="vp-doc")
        or soup.find("main")
        or soup.find("article")
    )
    if content_div:
        # 去掉 nav 侧栏
        for el in content_div.find_all(["nav", "aside", "footer"]):
            el.decompose()
        return content_div.get_text(separator="\n", strip=True)

    return soup.get_text(separator="\n", strip=True)


def crawl_feature_article(item: dict) -> dict | None:
    """爬取单篇 Feature 文章，返回原始数据"""
    html = fetch_html(item["url"])
    if not html:
        return None

    content = extract_main_content(html)

    # 提取代码块（保留 mcfunction / json 标记）
    soup = BeautifulSoup(html, "html.parser")
    code_blocks = []
    for pre in soup.find_all("pre"):
        lang_el = pre.find("code")
        lang = ""
        if lang_el and lang_el.get("class"):
            for cls in lang_el["class"]:
                if cls.startswith("language-"):
                    lang = cls.replace("language-", "")
        code_blocks.append({
            "lang": lang,
            "code": pre.get_text(strip=True)
        })

    return {
        "id": f"feature_{item['issue']}_{item['url'].split('/')[-2]}",
        "issue": item["issue"],
        "title": item["title"],
        "url": item["url"],
        "content": content,
        "code_blocks": code_blocks,
        "scraped_at": datetime.now().isoformat(),
        "source_type": "feature_article",
    }


def crawl_datapack_wiki() -> list[dict]:
    """爬取 datapack.wiki 关键页面"""
    print("\n[datapack.wiki]")

    # datapack.wiki 使用 VitePress，从根目录爬链接
    base = "https://datapack.wiki"
    html = fetch_html(base)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/") and not href.startswith("//"):
            links.add(f"{base}{href}")
        elif base in href:
            links.add(href)

    # 过滤掉锚点和非内容页
    links = [l for l in links if "#" not in l and l != base and l != f"{base}/"]
    print(f"  找到 {len(links)} 个内部链接")

    pages = []
    for url in sorted(links)[:60]:   # 最多 60 页
        html = fetch_html(url)
        if not html:
            continue
        content = extract_main_content(html)
        soup2 = BeautifulSoup(html, "html.parser")
        h1 = soup2.find("h1")
        title = h1.get_text(strip=True) if h1 else url

        code_blocks = []
        for pre in soup2.find_all("pre"):
            lang_el = pre.find("code")
            lang = ""
            if lang_el and lang_el.get("class"):
                for cls in lang_el["class"]:
                    if cls.startswith("language-"):
                        lang = cls.replace("language-", "")
            code_blocks.append({"lang": lang, "code": pre.get_text(strip=True)})

        pages.append({
            "id": f"dpwiki_{re.sub(r'[^a-z0-9]', '_', url.replace(base,'').lower()[:40])}",
            "title": title,
            "url": url,
            "content": content,
            "code_blocks": code_blocks,
            "scraped_at": datetime.now().isoformat(),
            "source_type": "datapack_wiki",
        })
        print(f"  OK  {title[:50]}")
        time.sleep(0.3)

    return pages


def phase_crawl(workers: int = 10):
    print("=" * 60)
    print("Phase 1: 爬取原始内容")
    print("=" * 60)

    all_articles: list[dict] = []

    # 1. Feature 月刊：先并发获取所有目录页的文章链接
    print(f"\n[Feature 月刊] 扫描 {len(FEATURE_ISSUES)} 期...")
    all_links: list[dict] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(extract_article_links_from_issue, iss): iss
                   for iss in FEATURE_ISSUES}
        for fut in as_completed(futures):
            links = fut.result()
            all_links.extend(links)
            print(f"  {futures[fut]}: {len(links)} 篇文章")

    print(f"  总计 {len(all_links)} 篇文章，开始并发爬取全文...")

    lock = threading.Lock()
    done = 0

    def crawl_worker(item):
        nonlocal done
        result = crawl_feature_article(item)
        with lock:
            done += 1
            status = "OK" if result else "FAIL"
            print(f"  [{done}/{len(all_links)}] {status} | {item['issue']} | {item['title'][:40]}")
        return result

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(crawl_worker, all_links))

    feature_articles = [r for r in results if r]
    all_articles.extend(feature_articles)

    # 保存 Feature 原始数据
    out = RAW_DIR / "feature_articles.json"
    out.write_text(json.dumps(feature_articles, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  Feature: {len(feature_articles)} 篇 -> {out}")

    # 2. datapack.wiki
    wiki_pages = crawl_datapack_wiki()
    all_articles.extend(wiki_pages)
    out2 = RAW_DIR / "datapack_wiki.json"
    out2.write_text(json.dumps(wiki_pages, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  datapack.wiki: {len(wiki_pages)} 页 -> {out2}")

    # 3. 合并索引
    index = [{"id": a["id"], "title": a["title"], "url": a["url"],
              "source_type": a["source_type"],
              "file": f"raw/{a['source_type']}.json"}
             for a in all_articles]
    (RAW_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n爬取完成：共 {len(all_articles)} 篇原始文章")
    return all_articles


# ══════════════════════════════════════════════════════════
# Phase 2: LLM 逆向分析 → technique 条目
# ══════════════════════════════════════════════════════════

EXTRACT_SYSTEM = """\
你是一名资深 Minecraft Java Edition 数据包开发者，也是知识提炼专家。

任务：阅读社区技术文章，提取「技术发现条目」(technique)。

━━━ 什么是 technique ━━━
technique = 非直觉的、Wiki 没有完整描述的、需要被发现的技术现象或设计模式。例如：
- 巧妙的机制组合（利用整数除法特性做状态机）
- 反直觉行为（execute store success 遇到 return 的特殊行为）
- 工程架构决策（UUID 二进制位作 tag 实现 O(log n) 实体查找）

━━━ confidence 判断规则 ━━━
- "medium"：文章包含完整的步骤说明或可运行代码，读者按照文章可以实现这个技术
- "low"：文章是原理分析、心得分享、经验总结，没有完整实现，或只有片段代码

━━━ 各字段要求 ━━━

code（代码示例）：
- confidence=medium：必须包含原文中的完整可运行代码，不能截断，不能只写注释
- confidence=low：有则引用，无则留空字符串
- 保留原始代码中的注释，不要改写
- 若原文有多段代码，全部包含，用注释标明各段用途

file_structure（数据包文件结构）：
- 列出实现此技术需要创建的所有文件及其路径（相对于数据包根目录）
- 原文有明确文件路径 → 照搬，不要省略
- 原文没有明确路径但有代码 → 根据 function 引用、advancement 引用等推断文件路径
- 每条格式：`data/<namespace>/functions/xxx.mcfunction`（仅路径，不加说明）
- 涉及多个 namespace 或资源包文件也一并列出

usage（用法）：
- 说明"写完这套文件后，怎么让它运行起来"
- 如果是需要显式调用的函数（有输入参数、返回值、需要 function 命令调用）→ 说明调用方式、参数、返回值
- 如果是事件驱动/自动触发型（右键检测、物品栏监听、tick 自动运行等）→ 写"构建完数据包即可在游戏内测试效果"或简述触发条件
- 如果原文有说明，原文照搬；没有则根据代码推断属于哪种类型再描述

use_cases（使用场景）：
- 什么情况下应该用这个技术（列举 1-3 个具体场景）
- 如果原文明确提到，照搬；否则根据机制原理合理推断
- 可选：什么情况下不适合使用

mechanism（机制原理）：
- 为什么这个技术能工作——底层机制是什么
- 关键的推导过程或数学原理（如有），不能省略
- 和直觉/朴素实现相比，这个技术的特殊之处
- 若原文对某个机制的表述含糊、有歧义、或你无法确定其确切含义，不要强行断言。如实转述原文，并在该处用「（原文表述需核实）」标注

notes（注意事项）：
- 原文明确提到的注意事项、限制、版本依赖、已知坑 → 全部列出
- 不要编造原文没有的内容
- 若某条注意事项依赖于你不确定的机制理解（如版本行为、是否被废弃等），在该条末尾加「（原文表述需核实）」，提醒人工核对

━━━ 提取规则 ━━━
1. 一篇文章 0-3 个 technique
2. 作品展示、快讯、地图介绍 → 输出 []
3. 每个 technique 必须能独立成立

━━━ layer 判断规则 ━━━
- "technique"：具体可实现的技术点/解法（有代码、有步骤），如射线检测、F键检测
- "concept"：基础概念/背景知识，解释"X是什么/为什么"，如 fake player、command context、storage 是什么
- "pattern"：跨技术的设计模式/架构思路，如 scoreboard ID 系统、状态机设计
判断依据：
- 文章标题或主体是"X是什么/解释一个概念"（如 "What is..."）→ concept，即使文中含示例代码也是 concept（代码只是辅助说明概念，不是要你照抄实现）
- 文章是"教你做一件事/解决一个问题"（如 "How do I..."）→ technique
- 一种通用设计思路/架构 → pattern

━━━ 输出格式（直接输出 JSON 数组，不加代码块）━━━
[
  {
    "title": "snake_case_english_title",
    "title_zh": "中文标题（8字以内）",
    "layer": "technique",
    "insight": "一句话：这个条目揭示了什么非直觉的事实",
    "code": "完整可运行代码（confidence=medium时必须完整）",
    "file_structure": ["data/<namespace>/functions/xxx.mcfunction", "..."],
    "usage": "写完代码后怎么调用/触发/接入数据包",
    "use_cases": "适用场景，1-3条，可含不适用场景",
    "mechanism": "完整的机制原理，包含推导过程，不少于100字",
    "notes": ["注意事项1", "注意事项2"],
    "version_min": "1.xx",
    "version_max": "（留空=至今有效；若已被破坏性更新废弃则填末个有效版本，如1.20.4）",
    "wiki_covers_this": false,
    "confidence": "medium",
    "tags": ["tag1", "tag2"]
  }
]

没有可提取的 technique 时输出：[]
"""

def call_llm_extract(content: str, model_name: str, api_key: str) -> str:
    from openai import OpenAI

    cfg = {
        "deepseek": {"base_url": "https://api.deepseek.com", "model": "deepseek-chat"},
        "openai":   {"base_url": None, "model": "gpt-4o"},
    }[model_name]

    kwargs = {"api_key": api_key}
    if cfg["base_url"]:
        kwargs["base_url"] = cfg["base_url"]

    client = OpenAI(**kwargs)
    # 不再粗暴截断到 6000：DeepSeek 上下文 64K，整篇文章可放下。
    # 仅设一个防极端的安全上限，超长文章才截断。
    MAX_CHARS = 40000
    article = content if len(content) <= MAX_CHARS else content[:MAX_CHARS]
    resp = client.chat.completions.create(
        model=cfg["model"],
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user",   "content": f"请分析以下文章，提取 technique 条目：\n\n{article}"},
        ],
        temperature=0.1,
        max_tokens=8000,
    )
    return resp.choices[0].message.content


def save_technique(tech: dict, source_id: str, source_url: str,
                   source_type: str, issue: str, counter: list):
    """将单个 technique 写为 md 文件"""
    with threading.Lock():
        idx = counter[0]
        counter[0] += 1

    tid = f"t{idx:04d}"
    slug = re.sub(r"[^a-z0-9_]", "", tech.get("title", "unknown").lower())[:40]
    filename = f"{tid}_{slug}.md"

    code = tech.get("code", tech.get("code_snippet", "")).strip()
    code_block = f"\n```mcfunction\n{code}\n```\n" if code else "\n（原文无完整代码示例）\n"

    notes = tech.get("notes", [])
    notes_str = "\n".join(f"- {n}" for n in notes) if notes else "（暂无）"

    file_structure = tech.get("file_structure", [])
    fs_str = "\n".join(f"- {s}" for s in file_structure) if file_structure else "（待补充）"

    tags_str = ", ".join(f'"{t}"' for t in tech.get("tags", []))
    confidence  = tech.get("confidence", "medium")
    version_min = tech.get("version_min", "1.13")
    version_max = tech.get("version_max", "")

    content = f"""\
---
id: {tid}
title: "{tech.get('title_zh', tech.get('title', ''))}"
title_en: "{tech.get('title', '')}"
layer: {tech.get('layer', 'technique')}
source_url: "{source_url}"
source_type: "{source_type}"
source_issue: "{issue}"
version_min: "{version_min}"
version_max: "{version_max}"
wiki_covers_this: {str(tech.get('wiki_covers_this', False)).lower()}
confidence: {confidence}
tags: [{tags_str}]
verified_in_game: false
---

## 核心洞见

{tech.get('insight', '')}

## 代码示例
{code_block}
## 文件结构

{fs_str}

## 用法

{tech.get('usage', '')}

## 使用场景

{tech.get('use_cases', '')}

## 机制原理

{tech.get('mechanism', '')}

## 注意事项

{notes_str}
"""

    out = TECH_DIR / filename
    out.write_text(content, encoding="utf-8")
    return tid, filename


def process_article_for_techniques(article: dict, model_name: str,
                                   api_key: str, counter: list,
                                   index: dict, lock: threading.Lock) -> int:
    """处理单篇文章，提取并保存所有 technique"""
    # 跳过非技术性内容（快讯、封二等）
    title = article.get("title", "")
    skip_keywords = ["快讯", "封二", "Spotlight", "ifc", "tva", "奖", "地图", "作品"]
    if any(kw in title for kw in skip_keywords):
        return 0

    content_text = article.get("content", "")
    if len(content_text) < 200:
        return 0

    try:
        raw = call_llm_extract(content_text, model_name, api_key)
    except Exception as e:
        print(f"  [LLM ERR] {article['id']}: {e}")
        return 0

    # 解析 JSON
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    try:
        techniques = json.loads(raw)
    except json.JSONDecodeError:
        # 尝试提取第一个 [ ... ] 块
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if m:
            try:
                techniques = json.loads(m.group())
            except Exception:
                techniques = []
        else:
            techniques = []

    if not isinstance(techniques, list):
        techniques = []

    count = 0
    for tech in techniques:
        if not isinstance(tech, dict):
            continue
        if not tech.get("title") and not tech.get("title_zh"):
            continue

        # 兜底：标题以 "What is" 开头的文章一律是 concept（AI 易被代码示例误导成 technique）
        art_title = article.get("title", "").strip().lower()
        if art_title.startswith("what is") or art_title.startswith("what's"):
            tech["layer"] = "concept"

        tid, fname = save_technique(
            tech,
            source_id=article.get("id", article.get("url", "unknown")),
            source_url=article.get("url", ""),
            source_type=article.get("source_type", "unknown"),
            issue=article.get("issue", article.get("source_issue", "")),
            counter=counter,
        )

        with lock:
            index[tid] = {
                "file": f"entries/{fname}",
                "title_zh": tech.get("title_zh", ""),
                "title_en": tech.get("title", ""),
                "layer": tech.get("layer", "technique"),
                "source_url": article["url"],
                "source_type": article.get("source_type", "unknown"),
                "wiki_covers_this": tech.get("wiki_covers_this", False),
                "version_min": tech.get("version_min", "1.13"),
                "tags": tech.get("tags", []),
                "verified_in_game": False,
            }
        count += 1

    return count


def phase_extract(model_name: str, workers: int):
    print("=" * 60)
    print("Phase 2: LLM 逆向分析 → technique 条目")
    print("=" * 60)

    # 读 API key
    key_file = API_DIR / f"{model_name}.txt"
    if not key_file.exists():
        print(f"[错误] API key 文件不存在: {key_file}")
        sys.exit(1)
    api_key = key_file.read_text(encoding="utf-8").strip()
    print(f"API key 读取成功（{model_name}）")

    # 加载所有原始文章
    articles: list[dict] = []
    for f in RAW_DIR.glob("*.json"):
        if f.name == "index.json":
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(data, list):
            articles.extend(data)
    print(f"加载 {len(articles)} 篇原始文章")

    # 加载现有索引，过滤已处理（除非 --force）
    existing_index = {}
    if not force:
        existing_index = build_index()

    force = getattr(phase_extract, "_force", False)
    if force:
        # 强制重提取：只保留非 feature_article 的条目（mcf_skill / manual 等）
        kept = {k: v for k, v in existing_index.items()
                if v.get("source_type") not in ("feature_article", "unknown", None)}
        print(f"--force 模式：保留 {len(kept)} 个非 feature 条目，重新提取其余")
        to_process = articles
        index = dict(kept)
        counter = [max((int(k[1:]) for k in index), default=-1) + 1]
    else:
        existing_urls = {v.get("source_url") for v in existing_index.values()}
        to_process = [a for a in articles if a.get("url") not in existing_urls]
        print(f"待处理（未提取过）: {len(to_process)} 篇")
        if not to_process:
            print("全部已处理。用 --force 强制重新提取。")
            return
        index = dict(existing_index)
        counter = [max((int(k[1:]) for k in index), default=-1) + 1]
    lock = threading.Lock()
    total_techniques = 0
    processed = 0
    stats_lock = threading.Lock()

    def worker(article):
        nonlocal total_techniques, processed
        n = process_article_for_techniques(article, model_name, api_key, counter, index, lock)
        with stats_lock:
            total_techniques += n
            processed += 1
            if processed % 5 == 0:
                print(f"  [进度] {processed}/{len(to_process)} 篇处理完 | "
                      f"累计提取 {total_techniques} 个 technique")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(worker, to_process))

    wiki_false = sum(1 for v in index.values() if not v.get("wiki_covers_this", True))
    print(f"\n提取完成：")
    print(f"  总 technique 条目: {len(index)}")
    print(f"  wiki_covers_this=false（最有价值）: {wiki_false}")


# ══════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════

def crawl_wiki(wiki_lang: str = "zh"):
    """爬取 Minecraft Wiki"""
    print(f"\n[Minecraft Wiki ({wiki_lang})]")

    wiki_raw = RAW_DIR / f"minecraft_wiki_{wiki_lang}.json"
    if wiki_raw.exists():
        existing = json.loads(wiki_raw.read_text(encoding="utf-8"))
        print(f"  已有 {len(existing)} 条 Wiki 数据，跳过")
        return existing

    print("  无 Wiki 数据，开始爬取...")
    from .wiki_crawler import WikiCrawler

    crawler = WikiCrawler(wiki=wiki_lang)
    articles = crawler.crawl_categories()
    articles.extend(crawler.crawl_search())

    # 去重
    seen = set()
    unique = []
    for a in articles:
        if a["id"] not in seen:
            seen.add(a["id"])
            unique.append(a)

    wiki_raw.write_text(
        json.dumps(unique, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Minecraft Wiki: {len(unique)} 页 -> {wiki_raw}")
    return unique


def run(phase="both", model="deepseek", cancel_event=None):
    files_processed = 0

    if phase in ("crawl", "both"):
        articles = phase_crawl(workers=10)
        files_processed += len(articles)

        if cancel_event and cancel_event.is_set():
            return {"ok": False, "cancelled": True, "files_processed": files_processed}

    if phase in ("extract", "both"):
        if cancel_event and cancel_event.is_set():
            return {"ok": False, "cancelled": True, "files_processed": files_processed}

        from ..config import API_DIR
        key_file = API_DIR / f"{model}.txt"
        if not key_file.exists():
            return {"ok": False, "cancelled": False, "files_processed": files_processed,
                    "error": f"API key not found: {key_file}"}

        api_key = key_file.read_text(encoding="utf-8").strip()

        articles = []
        for f in RAW_DIR.glob("*.json"):
            if f.name == "index.json":
                continue
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, list):
                articles.extend(data)

        existing_index = build_index()
        existing_urls = {v.get("source_url") for v in existing_index.values()}
        to_process = [a for a in articles if a.get("url") not in existing_urls]

        index = dict(existing_index)
        counter = [max((int(k[1:]) for k in index if k.startswith("t")), default=-1) + 1]
        lock = threading.Lock()
        total_techniques = 0
        processed = 0
        stats_lock = threading.Lock()

        def worker(article):
            nonlocal total_techniques, processed
            n = process_article_for_techniques(article, model, api_key, counter, index, lock)
            with stats_lock:
                total_techniques += n
                processed += 1

        BATCH_SIZE = 20
        for i in range(0, len(to_process), BATCH_SIZE):
            if cancel_event and cancel_event.is_set():
                return {"ok": False, "cancelled": True, "files_processed": files_processed + processed}
            batch = to_process[i:i + BATCH_SIZE]
            with ThreadPoolExecutor(max_workers=20) as pool:
                list(pool.map(worker, batch))

        files_processed += processed

    return {"ok": True, "cancelled": False, "files_processed": files_processed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["crawl", "extract", "both"], default="both")
    parser.add_argument("--model", default="deepseek", choices=["deepseek", "openai"])
    parser.add_argument("-j", "--workers", type=int, default=20)
    parser.add_argument("--force", action="store_true", help="强制重新提取所有文章，覆盖旧条目")
    parser.add_argument("--wiki", choices=["zh", "en", "none"], default="none",
                       help="是否爬取 Minecraft Wiki（默认跳过）")
    args = parser.parse_args()

    if args.phase in ("crawl", "both"):
        phase_crawl(workers=args.workers)

        if args.wiki != "none":
            wiki_articles = crawl_wiki(wiki_lang=args.wiki)
            index_file = RAW_DIR / "index.json"
            if index_file.exists():
                index = json.loads(index_file.read_text(encoding="utf-8"))
            else:
                index = []
            for a in wiki_articles:
                index.append({"id": a["id"], "title": a["title"], "url": a["url"],
                             "source_type": a["source_type"],
                             "file": f"raw/minecraft_wiki_{args.wiki}.json"})
            index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.phase in ("extract", "both"):
        phase_extract._force = args.force
        phase_extract(model_name=args.model, workers=args.workers)


if __name__ == "__main__":
    main()
