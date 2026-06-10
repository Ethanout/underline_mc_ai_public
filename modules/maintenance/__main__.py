"""CLI: python -m modules.maintenance [--fix] [--dedup] [--purge]"""
import argparse

def main():
    parser = argparse.ArgumentParser(description="知识库维护工具")
    parser.add_argument("--fix", action="store_true", help="修复 frontmatter")
    parser.add_argument("--dedup", action="store_true", help="去重")
    parser.add_argument("--purge", action="store_true", help="清理过期条目")
    args = parser.parse_args()
    if args.fix:
        from .fix_frontmatter import run; result = run()
    elif args.dedup:
        from .dedup_entries import run; result = run()
    elif args.purge:
        from .purge_old import run; result = run()
    else:
        parser.print_help()
        return
    print(f"结果: {result}")

if __name__ == "__main__":
    main()
