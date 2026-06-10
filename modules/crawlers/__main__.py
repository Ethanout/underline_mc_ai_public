"""CLI: python -m modules.crawlers [--phase PHASE] [--model MODEL]"""
import argparse
from .crawl_and_extract import run

def main():
    parser = argparse.ArgumentParser(description="爬取 + 提取管道")
    parser.add_argument("--phase", default="both", choices=["crawl", "extract", "both"])
    parser.add_argument("--model", default="deepseek", choices=["deepseek", "siliconflow"])
    args = parser.parse_args()
    result = run(phase=args.phase, model=args.model)
    print(f"结果: {result}")

if __name__ == "__main__":
    main()
