"""
同一 tid 保留最新修改的文件，其余移入 trash/techniques/
"""
import sys, json, re, shutil
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from collections import defaultdict

from ..config import ENTRIES_DIR, ARCHIVE_TECH_DIR

TECH_DIR = ENTRIES_DIR
ARCHIVE_DIR = ARCHIVE_TECH_DIR
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# 按 tid 分组
groups: dict[str, list[Path]] = defaultdict(list)
for f in TECH_DIR.glob("t*.md"):
    tid = f.stem.split("_")[0]
    groups[tid].append(f)

moved, kept = 0, 0
for tid, files in sorted(groups.items()):
    if len(files) == 1:
        kept += 1
        continue
    # 保留修改时间最新的
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    winner = files[0]
    for dup in files[1:]:
        dest = ARCHIVE_DIR / dup.name
        # 避免文件名冲突
        if dest.exists():
            dest = ARCHIVE_DIR / (dup.stem + "_dup.md")
        shutil.move(str(dup), str(dest))
        print(f"  移除重复: {dup.name}  →  archive/techniques/")
        moved += 1
    kept += 1

print(f"\n保留: {kept} 个 tid，移除重复: {moved} 个文件")
