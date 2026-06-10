"""清理 frontmatter 缺失 id 的孤立 technique 文件"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from datetime import datetime

from ..config import ENTRIES_DIR, ARCHIVE_DIR, build_index

TECH_DIR = ENTRIES_DIR
ARCHIVE_DIR.mkdir(exist_ok=True)

index = build_index()
indexed_ids = set(index.keys())

moved = 0
for f in sorted(TECH_DIR.glob("t*.md")):
    tid = f.stem.split("_")[0]
    if tid not in indexed_ids:
        meta = {
            "type": "technique",
            "id": tid,
            "original": f.name,
            "source": "techniques",
            "content": f.read_text(encoding="utf-8"),
            "index_entry": None,
            "purge_reason": "orphan_not_in_index",
            "purged_at": datetime.now().isoformat(),
        }
        dest = ARCHIVE_DIR / f.name
        if dest.exists():
            dest = ARCHIVE_DIR / f"{f.stem}_{datetime.now().strftime('%H%M%S%f')}.md"
        f.rename(dest)
        (ARCHIVE_DIR / (dest.name + ".meta")).write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        moved += 1

remaining = len(list(TECH_DIR.glob("t*.md")))
print(f"孤立文件移到回收站: {moved}")
print(f"techniques/ 剩余: {remaining} 个文件")
print(f"index 条目: {len(index)}")
