"""
Pipeline 配置中心
===============
所有路径通过 PROJECT_ROOT 计算，消除固定目录层级硬编码。
PROJECT_ROOT 通过查找根目录标记文件（pyproject.toml / .gitignore / app.py）自动定位。
"""
from pathlib import Path


def _find_project_root() -> Path:
    """从当前文件向上查找项目根目录标记，确保路径正确且不受文件移动影响。"""
    current = Path(__file__).resolve().parent
    candidates = [current] + list(current.parents)
    for parent in candidates:
        if (parent / ".gitignore").exists() and (parent / "app.py").exists():
            return parent
    # 兜底
    raise RuntimeError("Unable to locate project root from modules/config.py")


PROJECT_ROOT = _find_project_root()

# ═══ 数据目录 ═══
DATA_DIR        = PROJECT_ROOT / "data"
INBOX_DIR       = DATA_DIR / "inbox"
SOURCES_DIR     = DATA_DIR / "sources"
RAW_DIR         = SOURCES_DIR / "raw"          # 爬虫原始输出
KNOWLEDGE_DIR   = DATA_DIR / "knowledge"
ENTRIES_DIR     = KNOWLEDGE_DIR / "entries"
REFERENCE_DIR   = KNOWLEDGE_DIR / "reference"
BEST_PRACTICES_DIR = KNOWLEDGE_DIR / "best_practices"
def build_index() -> dict:
    """运行时从 .md frontmatter 构建索引，替代静态 _index.json"""
    import re
    index = {}
    for f in ENTRIES_DIR.glob("t*.md"):
        text = f.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if not m:
            continue
        meta = {}
        for line in m.group(1).split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            if val in ("true", "false"):
                meta[key] = val == "true"
            elif val.startswith("[") and val.endswith("]"):
                try:
                    import json
                    meta[key] = json.loads(val)
                except Exception:
                    meta[key] = val
            elif val.startswith('"') and val.endswith('"'):
                meta[key] = val[1:-1]
            else:
                try:
                    meta[key] = int(val)
                except ValueError:
                    try:
                        meta[key] = float(val)
                    except ValueError:
                        meta[key] = val
        tid = meta.get("id", "")
        if tid:
            entry = {}
            for k in ("title_zh", "title", "title_en", "source_type", "source_url",
                       "wiki_covers_this", "confidence", "tags", "version_min",
                       "version_max", "layer", "verified_in_game"):
                if k in meta:
                    entry[k] = meta[k]
            if "title" in entry and "title_zh" not in entry:
                entry["title_zh"] = entry.pop("title")
            index[tid] = entry
    return index
RAG_DB_DIR      = KNOWLEDGE_DIR / "rag_chroma_db"
VALIDATION_DIR  = PROJECT_ROOT / "validation_results"
TO_DELETE_FILE  = Path(__file__).parent / "maintenance" / "to_delete.json"

# ═══ API 密钥 ═══
API_DIR             = PROJECT_ROOT / "config" / "api"
SILICONFLOW_KEY     = API_DIR / "siliconflow.txt"
DEEPSEEK_KEY        = API_DIR / "deepseek.txt"
REDDIT_MCC_CONFIG   = PROJECT_ROOT / "config" / "crawlers" / "reddit_minecraftcommands.json"

# ═══ 归档 ═══
ARCHIVE_DIR         = DATA_DIR / "archive"
ARCHIVE_TECH_DIR    = ARCHIVE_DIR / "techniques"
ARCHIVE_INBOX_DIR   = ARCHIVE_DIR / "inbox"

# ═══ 静态资源 ═══
STATIC_DIR = PROJECT_ROOT / "static"

# ═══ 数据包测试 ═══
TEMP_DATAPACKS_DIR  = DATA_DIR / "temp_datapacks"      # beet 生成的临时测试数据包

# ═══ MCP ═══
MCP_DIR         = PROJECT_ROOT / "projects" / "minecraft-mod-mcp"
MINEFLAYER_DIR  = PROJECT_ROOT / "projects" / "mineflayer-bot"
