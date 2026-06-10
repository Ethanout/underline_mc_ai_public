"""CLI: python -m modules.indexing [--rebuild]"""
import argparse
from .build_rag_index import run

def main():
    parser = argparse.ArgumentParser(description="RAG 索引构建")
    parser.add_argument("--rebuild", action="store_true", help="重建索引（清空旧数据）")
    args = parser.parse_args()
    result = run(rebuild=args.rebuild)
    print(f"结果: {result}")

if __name__ == "__main__":
    main()
