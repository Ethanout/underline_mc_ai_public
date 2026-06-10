"""
爬取香草图书馆、datapack.wiki、Minecraft Wiki 等源头。
目标：识别「技巧片段」和「复合模式」而不只是基础机制。

使用说明：
    python -m modules.crawlers.scrape_sources --source vanilla_feature
    python -m modules.crawlers.scrape_sources --source datapack_wiki
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import time
from datetime import datetime
import argparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[错误] 需要 requests 和 beautifulsoup4 库")
    print("运行: pip install requests beautifulsoup4")
    sys.exit(1)

from ..config import SOURCES_DIR

SOURCES_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────
# 香草图书馆 Feature 月刊爬虫
# ─────────────────────────────────────────────────────────

def scrape_vanilla_feature():
    """爬取香草图书馆 Feature 月刊所有文章"""
    print("\n[香草图书馆 Feature 月刊]")
    print("爬取所有月刊文章...")
    
    base_url = "https://cr-019.github.io/datapack-index"
    articles = []
    
    try:
        # 获取月刊索引页
        r = requests.get(f"{base_url}/feature/_index.html", timeout=10)
        soup = BeautifulSoup(r.content, "html.parser")
        
        # 提取月刊列表（通常在左侧导航）
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if "/202" in href and "feature" in href and "index" in href:
                links.append({
                    "title": text,
                    "url": href if href.startswith("http") else f"{base_url}/{href}"
                })
        
        print(f"  找到 {len(links)} 个月刊")
        
        # 爬每一期月刊
        for link in links[:12]:  # 最近 12 期
            print(f"  -> {link['title']}")
            try:
                r = requests.get(link["url"], timeout=10)
                soup = BeautifulSoup(r.content, "html.parser")
                
                # 提取正文（通常在 main 或 article 标签）
                content = soup.find("main") or soup.find("article")
                if content:
                    text = content.get_text(separator="\n", strip=True)
                    articles.append({
                        "title": link["title"],
                        "url": link["url"],
                        "content": text[:3000],  # 截取前 3000 字
                        "scraped_at": datetime.now().isoformat()
                    })
                time.sleep(0.5)  # 礼貌延迟
            except Exception as e:
                print(f"     [警告] 爬取失败: {e}")
        
    except Exception as e:
        print(f"[错误] {e}")
        return []
    
    # 保存
    out_file = SOURCES_DIR / "vanilla_feature.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"  已保存 {len(articles)} 篇文章到 {out_file}")
    
    return articles


# ─────────────────────────────────────────────────────────
# Datapack.wiki 爬虫
# ─────────────────────────────────────────────────────────

def scrape_datapack_wiki():
    """爬取 datapack.wiki 所有页面"""
    print("\n[Datapack Wiki]")
    print("爬取所有页面...")
    
    base_url = "https://datapack.wiki"
    pages = []
    
    try:
        # datapack.wiki 的页面列表（假设有目录或 sitemap）
        # 这里我们先爬首页找链接
        r = requests.get(base_url, timeout=10)
        soup = BeautifulSoup(r.content, "html.parser")
        
        # 找所有内部链接（href 包含 datapack.wiki）
        links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if base_url in href or href.startswith("/"):
                full_url = href if href.startswith("http") else f"{base_url}{href}"
                if full_url not in links:
                    links.add(full_url)
        
        print(f"  找到 {len(links)} 个链接（首页）")
        
        # 爬前 20 个页面
        for link in list(links)[:20]:
            print(f"  -> {link}")
            try:
                r = requests.get(link, timeout=10)
                soup = BeautifulSoup(r.content, "html.parser")
                
                title = soup.find("h1")
                title_text = title.get_text(strip=True) if title else "Unknown"
                
                # 提取主要内容
                content = soup.find("main") or soup.find("article") or soup.body
                if content:
                    text = content.get_text(separator="\n", strip=True)
                    pages.append({
                        "title": title_text,
                        "url": link,
                        "content": text[:3000],
                        "scraped_at": datetime.now().isoformat()
                    })
                time.sleep(0.5)
            except Exception as e:
                print(f"     [警告] {e}")
        
    except Exception as e:
        print(f"[错误] {e}")
        return []
    
    # 保存
    out_file = SOURCES_DIR / "datapack_wiki.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
    print(f"  已保存 {len(pages)} 个页面到 {out_file}")
    
    return pages


# ─────────────────────────────────────────────────────────
# Minecraft Wiki Commands 爬虫
# ─────────────────────────────────────────────────────────

def scrape_minecraft_wiki_commands():
    """爬取中文 Minecraft Wiki 的命令相关页面"""
    print("\n[Minecraft Wiki Commands]")
    print("爬取命令相关页面...")
    
    base_url = "https://zh.minecraft.wiki"
    command_urls = [
        "/w/命令/execute",
        "/w/命令/scoreboard",
        "/w/命令/advancement",
        "/w/命令/data",
        "/w/命令/function",
        "/w/Data_component_format",
        "/w/标签",
    ]
    
    pages = []
    
    try:
        for path in command_urls:
            url = f"{base_url}{path}"
            print(f"  -> {path}")
            try:
                r = requests.get(url, timeout=10)
                soup = BeautifulSoup(r.content, "html.parser")
                
                title = soup.find("h1")
                title_text = title.get_text(strip=True) if title else path
                
                # 提取正文（wiki 通常在 mw-parser-output）
                content = soup.find("div", class_="mw-parser-output")
                if content:
                    text = content.get_text(separator="\n", strip=True)
                    pages.append({
                        "title": title_text,
                        "url": url,
                        "content": text[:4000],
                        "scraped_at": datetime.now().isoformat()
                    })
                time.sleep(0.3)
            except Exception as e:
                print(f"     [警告] {e}")
        
    except Exception as e:
        print(f"[错误] {e}")
        return []
    
    # 保存
    out_file = SOURCES_DIR / "minecraft_wiki_commands.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
    print(f"  已保存 {len(pages)} 个页面到 {out_file}")
    
    return pages


def main():
    parser = argparse.ArgumentParser(description="爬取数据包开发资源")
    parser.add_argument(
        "--source",
        choices=["all", "vanilla_feature", "datapack_wiki", "minecraft_wiki"],
        default="all",
        help="爬取源（默认全部）"
    )
    args = parser.parse_args()
    
    if args.source in ["all", "vanilla_feature"]:
        scrape_vanilla_feature()
    
    if args.source in ["all", "datapack_wiki"]:
        scrape_datapack_wiki()
    
    if args.source in ["all", "minecraft_wiki"]:
        scrape_minecraft_wiki_commands()
    
    print(f"\n已保存到: {SOURCES_DIR}")


if __name__ == "__main__":
    main()
