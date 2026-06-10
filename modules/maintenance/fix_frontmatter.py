"""批量将 JSON frontmatter 转为 YAML"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8")

from ..config import ENTRIES_DIR

TECH_DIR = ENTRIES_DIR

def dict_to_yaml(d: dict) -> str:
    lines = []
    for k, v in d.items():
        if isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, list):
            items = ", ".join(json.dumps(x, ensure_ascii=False) for x in v)
            lines.append(f"{k}: [{items}]")
        elif isinstance(v, (int, float)):
            lines.append(f"{k}: {v}")
        elif v is None or v == "":
            lines.append(f'{k}: ""')
        else:
            s = str(v)
            needs_quote = ('"' in s or '\\' in s or ':' in s or '#' in s or
                          s.startswith("{") or s.startswith("[") or
                          s.strip() == "" or s.startswith(" ") or s.endswith(" "))
            if needs_quote:
                escaped = s.replace('\\', '\\\\').replace('"', '\\"')
                lines.append(f'{k}: "{escaped}"')
            else:
                lines.append(f"{k}: {s}")
    return "\n".join(lines)

fixed, skipped = 0, 0
for f in sorted(TECH_DIR.glob("t*.md")):
    content = f.read_text(encoding="utf-8")
    # Check if second line (between --- and ---) is JSON
    m = re.match(r"^---\s*\n(\{.*?\})\s*\n---", content, re.DOTALL)
    if m:
        try:
            fm = json.loads(m.group(1))
            yaml_fm = dict_to_yaml(fm)
            new_content = content.replace(m.group(1), yaml_fm)
            f.write_text(new_content, encoding="utf-8")
            print(f"  fixed: {f.name}")
            fixed += 1
        except Exception as e:
            print(f"  skip: {f.name} ({e})")
            skipped += 1

print(f"\nDone: {fixed} fixed, {skipped} skipped")
