"""审计知识库内容质量"""
import sys, re, json
sys.stdout.reconfigure(encoding="utf-8")

from ..config import ENTRIES_DIR, build_index

TECH_DIR = ENTRIES_DIR
INDEX = build_index()

strip_fm = lambda c: re.sub(r"^---.*?---\s*", "", c, flags=re.DOTALL)

lengths, no_code, short, feature, mcf_skill, manual = [], [], [], [], [], []

for f in sorted(TECH_DIR.glob("t*.md")):
    c = f.read_text(encoding="utf-8")
    body = strip_fm(c)
    n = len(body)
    lengths.append((n, f.name))

    tid = f.stem.split("_")[0]
    src = INDEX.get(tid, {}).get("source_type", "unknown")
    if src == "feature_article": feature.append(f.name)
    elif src == "mcf_skill": mcf_skill.append(f.name)
    elif src == "manual": manual.append(f.name)

    if "mcfunction" not in c and "```" not in c:
        no_code.append(f.name)
    if n < 200:
        short.append((n, f.name))

lengths.sort()
vals = [l for l, _ in lengths]
n = len(vals)

print(f"总条目: {n}")
print(f"来源分布: feature_article={len(feature)}, mcf_skill={len(mcf_skill)}, manual={len(manual)}")
print()
print(f"内容长度:")
print(f"  最短: {vals[0]}")
print(f"  p25:  {vals[n//4]}")
print(f"  中位: {vals[n//2]}")
print(f"  p75:  {vals[3*n//4]}")
print(f"  最长: {vals[-1]}")
print()
print(f"无代码示例: {len(no_code)} 条 ({len(no_code)*100//n}%)")
print()
print(f"内容极短 (<200字符) 的条目 ({len(short)} 条):")
for l, name in short[:20]:
    print(f"  {l:4d}  {name}")
