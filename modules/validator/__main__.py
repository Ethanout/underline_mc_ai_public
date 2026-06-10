"""CLI: python -m modules.validator [--technique ID]"""
import argparse
from .knowledge_validator import run

def main():
    parser = argparse.ArgumentParser(description="知识库自动验证")
    parser.add_argument("--technique", default=None, help="只验证单个技术 (如 t0001)")
    args = parser.parse_args()
    result = run(technique_id=args.technique)
    print(f"结果: {result}")

if __name__ == "__main__":
    main()
