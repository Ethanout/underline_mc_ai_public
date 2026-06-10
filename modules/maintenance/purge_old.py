"""将 to_delete.json 中的旧版条目移到回收站"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8")
from datetime import datetime

from ..config import ENTRIES_DIR, ARCHIVE_DIR, TO_DELETE_FILE, build_index

TECH_DIR = ENTRIES_DIR
ARCHIVE_DIR.mkdir(exist_ok=True)

to_delete = json.loads(TO_DELETE_FILE.read_text(encoding="utf-8"))
index = build_index()

moved, missing = 0, 0
for tid in to_delete:
    files = list(TECH_DIR.glob(f"{tid}_*.md"))
    if not files:
        missing += 1
        # 也从 index 删掉
        index.pop(tid, None)
        continue
    f = files[0]
    meta = {
        "type": "technique",
        "id": tid,
        "original": f.name,
        "source": "techniques",
        "content": f.read_text(encoding="utf-8"),
        "index_entry": index.pop(tid, None),
        "purge_reason": "duplicate_replaced_by_newer_extraction",
        "purged_at": datetime.now().isoformat(),
    }
    dest = ARCHIVE_DIR / f.name
    # 如果回收站里已有同名文件，加时间戳
    if dest.exists():
        dest = ARCHIVE_DIR / f"{f.stem}_{datetime.now().strftime('%H%M%S')}.md"
    f.rename(dest)
    (ARCHIVE_DIR / (dest.name + ".meta")).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    moved += 1

print(f"已移到回收站: {moved}")
print(f"文件不存在(仅从frontmatter丢失): {missing}")
print(f"现有条目数: {len(build_index())}")
