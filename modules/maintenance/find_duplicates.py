"""找出新旧版本重复的 technique 条目（按 source_url 去重）"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8")
from collections import defaultdict

from ..config import ENTRIES_DIR, TO_DELETE_FILE, build_index

TECH_DIR = ENTRIES_DIR
INDEX = build_index()

# 按 source_url 分组
by_url = defaultdict(list)
no_url = []
for tid, meta in INDEX.items():
    url = meta.get("source_url", "").strip()
    if url:
        by_url[url].append(tid)
    else:
        no_url.append(tid)

# 找重复
duplicates = {url: tids for url, tids in by_url.items() if len(tids) > 1}

print(f"总条目: {len(INDEX)}")
print(f"有重复 source_url 的组: {len(duplicates)}")
print(f"涉及重复条目总数: {sum(len(v) for v in duplicates.values())}")
print()

old_ids = []  # 要删的旧 ID（编号小的）
keep_ids = []

for url, tids in duplicates.items():
    tids_sorted = sorted(tids, key=lambda x: int(x[1:]))
    keep = tids_sorted[-1]   # 保留编号最大的（新版）
    old = tids_sorted[:-1]   # 删除编号小的（旧版）
    old_ids.extend(old)
    keep_ids.append(keep)
    print(f"  删: {old}  保留: {keep}  {INDEX[keep].get('title_zh','')[:20]}")

print(f"\n待删除旧条目: {len(old_ids)}")
print(f"保留新条目:   {len(keep_ids)}")

# 写出待删列表供下一步使用
out = TO_DELETE_FILE
out.write_text(json.dumps(old_ids, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n待删列表已写入: {out}")
