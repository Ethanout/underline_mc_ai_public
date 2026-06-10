"""CLI: python -m modules.extractor [filename]"""
import argparse
from .pipeline import structure_inbox

def main():
    parser = argparse.ArgumentParser(description="Inbox 文件结构化")
    parser.add_argument("filename", help="inbox 文件名 (如 20240101_120000.md)")
    args = parser.parse_args()
    from ..config import INBOX_DIR
    f = INBOX_DIR / args.filename
    if not f.exists():
        print(f"文件不存在: {f}")
        return
    result = structure_inbox(f.read_text(encoding="utf-8"))
    print(f"结果: {result}")

if __name__ == "__main__":
    main()
