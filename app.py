"""知识库管理 Web UI — FastAPI 后端（薄路由 + dispatcher 调度）"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from modules.config import (
    INBOX_DIR, ENTRIES_DIR, ARCHIVE_TECH_DIR, ARCHIVE_INBOX_DIR, STATIC_DIR,
    DEEPSEEK_KEY, SILICONFLOW_KEY, PROJECT_ROOT, RAG_DB_DIR, VALIDATION_DIR,
    TEMP_DATAPACKS_DIR, build_index,
)
from modules.dispatcher import start, start_async, cancel, status, list_tasks

TECH_DIR = ENTRIES_DIR

for d in (INBOX_DIR, ARCHIVE_TECH_DIR, ARCHIVE_INBOX_DIR, TEMP_DATAPACKS_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="MC知识库管理")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    return (ROOT / "static/index.html").read_text(encoding="utf-8")


# ═══ 工具函数 ══════════════════════════════════════════════

def load_index() -> dict:
    return build_index()

def next_id(index: dict) -> str:
    ids = [int(k[1:]) for k in index if re.match(r"t\d+$", k)]
    n = max(ids, default=-1) + 1
    return f"t{n:04d}"

def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}, text
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
                meta[key] = json.loads(val)
            except json.JSONDecodeError:
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
    return meta, text[m.end():].strip()

def safe_filename(s: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '', s.replace(' ', '_'))[:60]

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


# ═══ API: 任务管理 ══════════════════════════════════════════

@app.get("/api/tasks")
def api_list_tasks():
    return list_tasks()

@app.get("/api/tasks/{task_id}")
def api_task_status(task_id: str):
    s = status(task_id)
    if not s:
        raise HTTPException(404, "任务不存在")
    return s

@app.post("/api/tasks/{task_id}/cancel")
def api_cancel_task(task_id: str):
    if not cancel(task_id):
        raise HTTPException(404, "任务不存在")
    return {"ok": True, "task_id": task_id, "status": "cancelling"}


# ═══ API: Inbox ═════════════════════════════════════════════

class InboxItem(BaseModel):
    content: str
    hint: Optional[str] = ""

@app.post("/api/inbox")
def save_to_inbox(item: InboxItem):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = INBOX_DIR / f"{ts}.md"
    body = item.content
    if item.hint:
        body = f"<!-- hint: {item.hint} -->\n\n{body}"
    fname.write_text(body, encoding="utf-8")
    return {"ok": True, "file": fname.name}

@app.get("/api/inbox")
def list_inbox():
    files = sorted(INBOX_DIR.glob("*.md"), reverse=True)
    result = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        result.append({
            "file": f.name,
            "preview": text[:120].replace("\n", " "),
            "size": len(text),
            "mtime": f.stat().st_mtime,
        })
    return result

@app.get("/api/inbox/{filename}")
def get_inbox_file(filename: str):
    f = INBOX_DIR / filename
    if not f.exists():
        raise HTTPException(404)
    return {"content": f.read_text(encoding="utf-8")}

@app.put("/api/inbox/{filename}")
def update_inbox_file(filename: str, payload: dict):
    f = INBOX_DIR / filename
    if not f.exists():
        raise HTTPException(404)
    f.write_text(payload["content"], encoding="utf-8")
    return {"ok": True}

@app.delete("/api/inbox/{filename}")
def delete_inbox_file(filename: str):
    f = INBOX_DIR / filename
    if f.exists():
        dest = ARCHIVE_INBOX_DIR / filename
        if dest.exists():
            dest = ARCHIVE_INBOX_DIR / f"{f.stem}_{datetime.now().strftime('%H%M%S')}.md"
        f.rename(dest)
    return {"ok": True}


# ═══ API: LLM 结构化 ═══════════════════════════════════════

@app.post("/api/structure/{filename}")
def structure_inbox_file(filename: str):
    from modules.extractor.pipeline import structure_inbox
    f = INBOX_DIR / filename
    if not f.exists():
        raise HTTPException(404)
    result = structure_inbox(f.read_text(encoding="utf-8"))
    return result


# ═══ API: Techniques CRUD ══════════════════════════════════

class TechniquePayload(BaseModel):
    title_zh: str
    title_en: str
    layer: str = "technique"
    wiki_covers_this: bool = False
    confidence: str = "medium"
    tags: list[str] = []
    version_min: str = ""
    version_max: str = ""
    source_url: str = ""
    source_type: str = "manual"
    core_insight: str = ""
    code_example: str = ""
    file_structure: list[str] = []
    usage: str = ""
    use_cases: str = ""
    mechanism: str = ""
    notes: list[str] = []
    inbox_file: Optional[str] = None

@app.post("/api/techniques")
def create_technique(payload: TechniquePayload):
    index = load_index()
    tid = next_id(index)
    safe = safe_filename(payload.title_en or payload.title_zh)
    md_path = TECH_DIR / f"{tid}_{safe}.md"

    fm = {
        "id": tid,
        "title": payload.title_zh,
        "title_en": payload.title_en,
        "layer": payload.layer,
        "source_url": payload.source_url,
        "source_type": payload.source_type,
        "version_min": payload.version_min,
        "version_max": payload.version_max,
        "wiki_covers_this": payload.wiki_covers_this,
        "confidence": payload.confidence,
        "tags": payload.tags,
        "verified_in_game": False,
    }
    code_block = (f"## 代码示例\n\n```mcfunction\n{payload.code_example}\n```\n"
                  if payload.code_example else "## 代码示例\n\n（原文无完整代码示例）\n")
    notes_str = ("\n".join(f"- {n}" for n in payload.notes)
                 if payload.notes else "（暂无）")
    fs_str = ("\n".join(f"- {s}" for s in payload.file_structure)
              if payload.file_structure else "（待补充）")

    lines = [f"---", dict_to_yaml(fm), "---", ""]
    lines += [f"## 核心洞见\n\n{payload.core_insight}\n"]
    lines += [code_block]
    lines += [f"## 文件结构\n\n{fs_str}\n"]
    lines += [f"## 用法\n\n{payload.usage}\n"]
    lines += [f"## 使用场景\n\n{payload.use_cases}\n"]
    lines += [f"## 机制原理\n\n{payload.mechanism}\n"]
    lines += [f"## 注意事项\n\n{notes_str}\n"]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    if payload.inbox_file:
        inbox_f = INBOX_DIR / payload.inbox_file
        if inbox_f.exists():
            inbox_f.unlink()

    return {"ok": True, "id": tid, "file": md_path.name}

@app.get("/api/techniques")
def list_techniques(q: str = "", limit: int = 50, layer: str = ""):
    index = load_index()
    results = []
    for tid, meta in index.items():
        if q:
            haystack = (meta.get("title_zh","") + meta.get("title_en","") + ",".join(meta.get("tags",[]))).lower()
            if q.lower() not in haystack:
                continue
        confidence = "medium"
        entry_layer = "technique"
        quality = ""
        files = list(TECH_DIR.glob(f"{tid}_*.md"))
        if files:
            fm = parse_frontmatter(files[0].read_text(encoding="utf-8"))[0]
            confidence = fm.get("confidence", "medium")
            entry_layer = fm.get("layer", "technique")
            quality = fm.get("quality", "")
        if layer and entry_layer != layer:
            continue
        results.append({"id": tid, **meta, "confidence": confidence, "layer": entry_layer, "quality": quality})
    results.sort(key=lambda x: x["id"], reverse=True)
    return results[:limit]

@app.get("/api/techniques/{tid}")
def get_technique(tid: str):
    files = list(TECH_DIR.glob(f"{tid}_*.md"))
    if not files:
        raise HTTPException(404)
    return {"content": files[0].read_text(encoding="utf-8"), "file": files[0].name}

@app.put("/api/techniques/{tid}")
def update_technique(tid: str, payload: dict):
    files = list(TECH_DIR.glob(f"{tid}_*.md"))
    if not files:
        raise HTTPException(404)
    files[0].write_text(payload["content"], encoding="utf-8")
    return {"ok": True}

@app.post("/api/techniques/{tid}/quality")
def set_quality(tid: str, payload: dict):
    files = list(TECH_DIR.glob(f"{tid}_*.md"))
    if not files:
        raise HTTPException(404, "technique not found")
    quality = payload.get("quality", "")
    if quality not in ("core", "ok", "water", ""):
        raise HTTPException(400, "invalid quality value")
    text = files[0].read_text(encoding="utf-8")
    m = re.match(r"^(---\s*\n)(.*?)(\n---)", text, re.DOTALL)
    if not m:
        raise HTTPException(400, "no frontmatter")
    head, body, tail = m.group(1), m.group(2), m.group(3)
    lines = [l for l in body.split("\n") if not l.strip().startswith("quality:")]
    if quality:
        lines.append(f"quality: {quality}")
    new_fm = head + "\n".join(lines) + tail
    files[0].write_text(new_fm + text[m.end():], encoding="utf-8")
    return {"ok": True, "quality": quality}

@app.delete("/api/techniques/{tid}")
def delete_technique(tid: str):
    files = list(TECH_DIR.glob(f"{tid}_*.md"))
    if not files:
        raise HTTPException(404, "technique not found")
    f = files[0]
    index = load_index()
    index_entry = index.pop(tid, None)
    original_content = f.read_text(encoding="utf-8")
    trash_header = f"<!-- _trash_id: {tid} | _trash_original: {f.name} | _trash_index: {json.dumps(index_entry or {}, ensure_ascii=False)} -->\n"
    dest = ARCHIVE_TECH_DIR / f.name
    if dest.exists():
        dest = ARCHIVE_TECH_DIR / f"{f.stem}_{datetime.now().strftime('%H%M%S')}.md"
    dest.write_text(trash_header + original_content, encoding="utf-8")
    f.unlink()
    return {"ok": True}


# ═══ API: Trash ═════════════════════════════════════════════

def _parse_trash_header(text: str) -> dict:
    m = re.match(r"^<!-- _trash_id: (\S+) \| _trash_original: (\S+) \| _trash_index: (.+) -->", text)
    if m:
        return {"id": m.group(1), "original": m.group(2),
                "index_entry": json.loads(m.group(3)), "type": "technique"}
    return {"id": "", "original": "", "index_entry": {}, "type": "technique"}

@app.get("/api/trash")
def list_trash():
    items = []
    for f in sorted(ARCHIVE_TECH_DIR.glob("*.md"),
                    key=lambda x: x.stat().st_mtime, reverse=True):
        text = f.read_text(encoding="utf-8")
        m = _parse_trash_header(text)
        title = m["index_entry"].get("title_zh", "") if m["index_entry"] else ""
        preview = re.sub(r"^<!--.*?-->\n", "", text, flags=re.DOTALL)
        preview = re.sub(r"^---.*?---\s*", "", preview, flags=re.DOTALL).strip()[:100]
        items.append({"id": m["id"] or f.stem, "type": "technique",
                      "original": m["original"] or f.name,
                      "title_zh": title, "filename": f.name,
                      "content_preview": preview, "mtime": f.stat().st_mtime})
    for f in sorted(ARCHIVE_INBOX_DIR.glob("*.md"),
                    key=lambda x: x.stat().st_mtime, reverse=True):
        text = f.read_text(encoding="utf-8")
        items.append({"id": f.stem, "type": "inbox", "original": f.name,
                      "title_zh": "", "filename": f.name,
                      "content_preview": text[:100].replace("\n", " "),
                      "mtime": f.stat().st_mtime})
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items

@app.post("/api/trash/{filename}/restore")
def restore_trash(filename: str):
    f = ARCHIVE_TECH_DIR / filename
    if f.exists():
        text = f.read_text(encoding="utf-8")
        m = _parse_trash_header(text)
        content = re.sub(r"^<!--.*?-->\n", "", text, count=1)
        dest = TECH_DIR / (m["original"] or filename)
        dest.write_text(content, encoding="utf-8")
        f.unlink()
        return {"ok": True, "type": "technique", "id": m["id"]}
    f = ARCHIVE_INBOX_DIR / filename
    if f.exists():
        dest = INBOX_DIR / filename
        f.rename(dest)
        return {"ok": True, "type": "inbox", "id": filename}
    raise HTTPException(404, "not found in trash")

@app.delete("/api/trash/{filename}")
def permanent_delete(filename: str):
    for d in (ARCHIVE_TECH_DIR, ARCHIVE_INBOX_DIR):
        f = d / filename
        if f.exists():
            f.unlink()
            return {"ok": True}
    return {"ok": False, "msg": "not found"}

@app.delete("/api/trash")
def empty_trash():
    n = 0
    for d in (ARCHIVE_TECH_DIR, ARCHIVE_INBOX_DIR):
        for f in d.glob("*.md"):
            f.unlink()
            n += 1
    return {"ok": True, "deleted": n}


# ═══ API: 管道 & 验证 & RAG（异步，通过 dispatcher）═══════

@app.post("/api/pipeline/run")
def pipeline_run(phase: str = "both", model: str = "deepseek"):
    from modules.crawlers.crawl_and_extract import run as crawl_run
    task_id = start("pipeline", crawl_run, phase=phase, model=model)
    return {"ok": True, "task_id": task_id, "message": f"管道已启动 (phase={phase}, model={model})"}

@app.get("/api/pipeline/status")
def pipeline_status():
    tasks = list_tasks()
    pipeline_tasks = [t for t in tasks if t["name"] == "pipeline" and t["status"] == "running"]
    if pipeline_tasks:
        return {"running": True, **pipeline_tasks[0]}
    last = [t for t in tasks if t["name"] == "pipeline"]
    if last:
        return {"running": False, **last[0]}
    return {"running": False, "last_run": None, "error": None}

@app.post("/api/validate/run")
def validate_run(technique_id: Optional[str] = None):
    from modules.validator.knowledge_validator import run as validate_run_fn
    task_id = start("validate", validate_run_fn, technique_id=technique_id)
    return {"ok": True, "task_id": task_id, "message": "验证已启动"}

@app.get("/api/validate/report")
def validate_report():
    reports = sorted(VALIDATION_DIR.glob("validation_*.json"), reverse=True)
    if not reports:
        raise HTTPException(404, "暂无验证报告")
    return json.loads(reports[0].read_text(encoding="utf-8"))

@app.post("/api/rebuild-rag")
def rebuild_rag():
    from modules.indexing.build_rag_index import run as rebuild_fn
    task_id = start("rebuild-rag", rebuild_fn, rebuild=True)
    return {"ok": True, "task_id": task_id, "message": "RAG 重建已启动"}


# ═══ API: RAG 查询（同步，即时返回）════════════════════════

class QueryRequest(BaseModel):
    question: str
    n: int = 4

@app.post("/api/query")
def rag_query(req: QueryRequest):
    from modules.indexing.query import run as query_run
    result = query_run(question=req.question, n=req.n)
    return result


# ═══ API: 配置 ══════════════════════════════════════════════

@app.get("/api/config")
def list_config():
    return {
        "project_root": str(PROJECT_ROOT),
        "entries_dir": str(ENTRIES_DIR),
        "inbox_dir": str(INBOX_DIR),
        "temp_datapacks_dir": str(TEMP_DATAPACKS_DIR),
        "index_mode": "runtime_from_frontmatter",
        "siliconflow_key_exists": SILICONFLOW_KEY.exists() if hasattr(SILICONFLOW_KEY, 'exists') else False,
        "deepseek_key_exists": DEEPSEEK_KEY.exists(),
    }

@app.put("/api/config/{key}")
def update_config(key: str, value: str = ""):
    path = None
    if key == "deepseek_key":
        path = DEEPSEEK_KEY
    elif key == "siliconflow_key":
        path = SILICONFLOW_KEY
    else:
        raise HTTPException(400, detail=f"不支持的配置项: {key}")
    path.write_text(value.strip(), encoding="utf-8")
    return {"ok": True, "key": key, "path": str(path)}


# ═══ 启动 ═══════════════════════════════════════════════════

if __name__ == "__main__":
    import webbrowser, threading
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:8765")).start()
    uvicorn.run("app:app", host="127.0.0.1", port=8765, reload=True)
