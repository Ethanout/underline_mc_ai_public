"""mcf-skill SKILL.md → 直接复制到 0_语法参考/ 作为参考文档，无 LLM 调用。
mcf-skill 是命令语法手册（execute/data/scoreboard 语法），不含非直觉技术，
不适合提取 technique；直接作为 RAG 参考层使用即可。
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import shutil

from ..config import SOURCES_DIR, REFERENCE_DIR

MCF_DIR = SOURCES_DIR / "mcf-skill"
REF_DIR = REFERENCE_DIR

def main():
    REF_DIR.mkdir(parents=True, exist_ok=True)
    skill_files = sorted(MCF_DIR.rglob("SKILL.md"))
    copied = 0
    for sf in skill_files:
        skill_name = sf.parent.name
        dest = REF_DIR / f"mcf-skill_{skill_name}.md"
        if dest.exists():
            print(f"  skip (already exists): {dest.name}")
        else:
            shutil.copy2(sf, dest)
            size = dest.stat().st_size
            print(f"  copied: {dest.name}  ({size:,} bytes)")
            copied += 1
    print(f"\n完成！共复制 {copied} 个参考文档到 {REF_DIR}")

if __name__ == "__main__":
    main()
