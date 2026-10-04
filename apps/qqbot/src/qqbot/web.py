"""Small, local-only WebUI backend for the QQ essence exporter."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import threading
import uuid
import time
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from . import essence_exporter as exporter
from .events import EventJournal
from .images import DEFAULT_IMAGE_DIR, ImageCache, image_segments
from .reply import ReplyContext, ReplyPolicy, addressed_text, deepseek_reply
from .store import Store
from .agent import Agent, make_post, prompt_messages
from .reply import probe_capabilities
from .tools import ToolRegistry
from .deepseek_files import DeepSeekImageFiles
from .admin_tools import install_admin_tools
from .collection import install_collection_tools, model_classifier
from .brain import Brain, BrainParameters, TurnCoordinator, model_judge, BASELINE_NAMES
from .runtime import RuntimeSettings

APP_ROOT = Path(__file__).resolve().parent
STATIC_INDEX = APP_ROOT / "static" / "index.html"
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="qqbot-export")
jobs: dict[str, dict[str, Any]] = {}
jobs_lock = threading.Lock()

@asynccontextmanager
async def lifespan(app):
    await run_in_threadpool(probe_models)
    stop = threading.Event()
    worker = threading.Thread(target=background_work, args=(stop,), daemon=True, name="qqbot-maintenance")
    worker.start()
    brain_worker = threading.Thread(target=brain_work, args=(stop,), daemon=True, name="qqbot-brain")
    brain_worker.start()
    recover_tasks()
    try:
        yield
    finally:
        stop.set()
        worker.join(timeout=2)
        brain_worker.join(timeout=2)


app = FastAPI(title="QQ Bot Exporter", version="0.1.0", lifespan=lifespan)
event_store = Store()
event_journal = EventJournal(Path(os.environ.get("QQBOT_EVENT_LOG", "runtime/private/qq_events.jsonl")), store=event_store)
# Own single worker: a slow image host must not hold up replies or export jobs.
image_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="qqbot-images")
memory_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="qqbot-memory")
image_cache = ImageCache(os.environ.get("QQBOT_IMAGE_DIR", DEFAULT_IMAGE_DIR))
reply_policy = ReplyPolicy(float(os.environ.get("QQBOT_REPLY_COOLDOWN", "1")))
reply_max_tokens = int(os.environ.get("QQBOT_REPLY_MAX_TOKENS", "220"))
reply_context_chars = int(os.environ.get("QQBOT_REPLY_CONTEXT_CHARS", "3000"))
reply_style_k = int(os.environ.get("QQBOT_STYLE_REPLY_K", "5"))

_style_memory_lock = threading.Lock()
_style_memory_instance = None
_capabilities = {}
_agent_lock = threading.Lock()
_brains = {}
_brains_lock = threading.Lock()
_inflight = set()


def get_brain(group_id):
    with _brains_lock:
        runtime = RuntimeSettings(event_store)
        baselines = {key: runtime.get("baseline_" + name) for key, name in BASELINE_NAMES.items()}
        params = BrainParameters(
            proactive_groups=tuple(g.strip() for g in os.environ.get("QQBOT_PROACTIVE_GROUPS", "").split(",") if g.strip()),
            proactive_min_gap=runtime.get("proactive_min_gap"),
            proactive_max_per_hour=int(runtime.get("proactive_max_per_hour")),
            active_min=runtime.get("active_min_seconds"), active_max=runtime.get("active_max_seconds"),
            profile_half_life=float(os.environ.get("QQBOT_PROFILE_HALF_LIFE", "2592000")),
            emotion_half_life=float(os.environ.get("QQBOT_EMOTION_HALF_LIFE", "1800")),
            mention_weight=float(os.environ.get("QQBOT_MENTION_WEIGHT", "3")),
            pickup_scale=float(os.environ.get("QQBOT_PICKUP_SCALE", ".01")))
        if group_id not in _brains:
            brain = Brain(event_store, group_id, baselines=baselines, parameters=params)
            if event_store.get_state("brain:" + group_id) is None:
                brain.rebuild_profile(event_store.messages(group_id))
            _brains[group_id] = brain
        brain = _brains[group_id]
        brain.baselines, brain.params = baselines, params
        return brain


def recover_tasks():
    for task in event_store.rows("SELECT * FROM tasks WHERE status IN ('queued','running','completed')"):
        row = event_store.message(task["group_id"], task["trigger_id"])
        if row:
            event = json.loads(row["raw"])
            executor.submit(reply_to_group, event, addressed_text(event) or "继续任务", task, task["id"].startswith("proactive:"))


def brain_work(stop):
    last_tick = 0
    while not stop.wait(1):
        now = time.time()
        with _brains_lock:
            brains = list(_brains.values())
        for brain in brains:
            if now - last_tick >= 20:
                brain.tick()
            if brain.clock() >= brain.active_until or not brain.judgment_due() or not brain.can_proactively_speak():
                continue
            with _brains_lock:
                if brain.group_id in _inflight: continue
            rows = [r for r in event_store.messages(brain.group_id) if not r["is_bot"]]
            if not rows: continue
            row = rows[-1]
            event = json.loads(row["raw"])
            task = event_store.create_task(brain.group_id, row["user_id"], f"proactive:{brain.version}", row["nickname"])
            if task["status"] in {"skipped", "failed", "sent"}:
                brain.pending = []
                brain.save()
                continue
            event_store.write("UPDATE tasks SET trigger_id=? WHERE id=?", (row["message_id"], task["id"]))
            task = event_store.task(task["id"])
            executor.submit(reply_to_group, event, "参与讨论", task, True)
        if now - last_tick >= 20: last_tick = now


def _onebot(action, params):
    return exporter.api_call(onebot_endpoint(), os.environ.get("ONEBOT_ACCESS_TOKEN"), action, params, False)


def _probe_upload(raw, ttl):
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as directory:
        path = Path(directory) / "probe.png"
        path.write_bytes(raw)
        return DeepSeekImageFiles(event_store, os.environ.get("DEEPSEEK_API_KEY", ""), ttl=ttl).upload(path)[0]


def probe_models():
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        _capabilities["error"] = "未配置 DeepSeek API key"
        return
    post = make_post(key)
    for model in dict.fromkeys((os.environ.get("QQBOT_MODEL", "deepseek-flash"), os.environ.get("QQBOT_JUDGE_MODEL", "deepseek-flash"))):
        value = probe_capabilities(post, _probe_upload, model)
        _capabilities[model] = value
        event_store.set_state("capabilities:" + model, value)


def ingest_style():
    from .style_memory import ingest_journal, read_journal
    memory = _get_style_memory()
    if memory is None:
        return {"text": 0, "images": 0}
    return ingest_journal(memory, read_journal(event_journal.path), image_cache)


def background_work(stop):
    interval = float(os.environ.get("QQBOT_MEMORY_INGEST_MINUTES", "30")) * 60
    if interval <= 0:
        return
    while not stop.wait(interval):
        try:
            ingest_style()
            sync_essence()
            from .memory_model import MemoryService
            for row in event_store.rows("SELECT DISTINCT group_id FROM memory_state"):
                MemoryService(event_store).sleep(row["group_id"])
        except Exception as exc:
            print(f"增量记忆入库失败：{type(exc).__name__}")


def sync_essence():
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        return
    registry = ToolRegistry(event_store, _onebot)
    tricks = install_collection_tools(registry, model_classifier(make_post(key)))
    groups = {row["group_id"] for row in event_store.rows("SELECT DISTINCT group_id FROM messages")}
    for group in sorted(groups):
        # Scheduled collection uses service provenance, never a forged group role.
        task = {"group_id": group}
        data = registry.read_essence(task, {})
        available = [row for row in data["messages"] if exporter.message_id(row) not in data["missing"]]
        tricks.sync(group, available)
    tricks.reindex()


def _get_style_memory():
    """Lazily build a StyleMemory, or return None if not configured."""
    global _style_memory_instance
    db_path = os.environ.get("QQBOT_STYLE_DB", "")
    if not db_path:
        return None
    with _style_memory_lock:
        if _style_memory_instance is None:
            from .embedding import build_embedder
            from .style_memory import StyleMemory
            _style_memory_instance = StyleMemory(db_path, build_embedder())
        return _style_memory_instance


DEFAULT_ONEBOT_ENDPOINT = "http://127.0.0.1:3000"
DEFAULT_WEB_PORT = 18787


def onebot_endpoint() -> str:
    """NapCat's HTTP API; filled from NapCat's config when ``NAPCAT_DIR`` is set."""
    return os.environ.get("ONEBOT_ENDPOINT", "").strip() or DEFAULT_ONEBOT_ENDPOINT


class JobRequest(BaseModel):
    endpoint: str = Field(default_factory=onebot_endpoint)
    group_id: str = Field(min_length=1, max_length=32)
    output: str = Field(default="runtime/private/qq_group_digest", min_length=1, max_length=500)
    action: str = Field(default="get_essence_msg_list", min_length=1, max_length=100)
    diagnose: bool = False
    refresh: bool = False


def validate_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(400, "endpoint 必须是 http(s) URL")
    return endpoint.rstrip("/")


def make_args(request: JobRequest) -> argparse.Namespace:
    return argparse.Namespace(
        endpoint=validate_endpoint(request.endpoint),
        token_env="ONEBOT_ACCESS_TOKEN",
        group_id=request.group_id,
        action=request.action,
        message_action="get_msg",
        root_envelope=False,
        output=request.output,
        page_size=100,
        max_pages=10000,
        max_messages=0,
        diagnose=request.diagnose,
        delay=0.3,
        refresh=request.refresh,
        overwrite=False,
    )


def run_job(job_id: str, request: JobRequest) -> None:
    with jobs_lock:
        jobs[job_id]["status"] = "running"
    try:
        args = make_args(request)
        if args.diagnose:
            value = exporter.api_call(
                args.endpoint,
                os.environ.get(args.token_env),
                args.action,
                {"group_id": args.group_id},
                False,
            )
            result = {"summary": exporter.response_summary(value)}
        else:
            # The CLI export function prints only counts and paths, never content.
            exit_code = exporter.export(args)
            if exit_code != 0:
                raise RuntimeError("导出器返回非零状态")
            manifest = Path(args.output).resolve() / "messages.json"
            result = {"output": str(manifest.parent), "messages": 0, "media": 0, "failures": 0}
            if manifest.exists():
                import json

                data = json.loads(manifest.read_text(encoding="utf-8"))
                result["messages"] = len(data.get("messages", []))
                for message in data.get("messages", []):
                    for media in message.get("media", []):
                        if media.get("file"):
                            result["media"] += 1
                        if media.get("error"):
                            result["failures"] += 1
        with jobs_lock:
            jobs[job_id].update(status="succeeded", result=result)
    except Exception as exc:
        with jobs_lock:
            jobs[job_id].update(status="failed", error=str(exc))


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    if not STATIC_INDEX.exists():
        return "<h1>QQ Bot WebUI</h1>"
    return STATIC_INDEX.read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "token_configured": str(bool(os.environ.get("ONEBOT_ACCESS_TOKEN"))).lower(),
        "onebot_endpoint": onebot_endpoint(),
        "observation_mode": "false",
        "model": os.environ.get("QQBOT_MODEL", "deepseek-flash"),
        "judge_model": os.environ.get("QQBOT_JUDGE_MODEL", "deepseek-flash"),
        "capabilities": _capabilities,
    }


def event_authorized(body: bytes, signature: str, authorization: str, expected: str) -> bool:
    """Check a pushed event against ``QQBOT_EVENT_TOKEN``.

    NapCat (and OneBot 11 HTTP POST in general) never sends the token itself:
    it signs the raw body, ``x-signature: sha1=<HMAC-SHA1(token, body)>``.  That
    is the path that matters.  A plain ``Authorization: Bearer`` is accepted
    too, for curl and for adapters that do send it.  No token configured means
    the endpoint is open, as before.
    """
    if not expected:
        return True
    if signature.startswith("sha1="):
        digest = hmac.new(expected.encode("utf-8"), body, hashlib.sha1).hexdigest()
        return hmac.compare_digest(signature[5:].strip().lower(), digest)
    supplied = authorization.removeprefix("Bearer ").strip()
    return bool(supplied) and hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8"))


@app.post("/api/onebot/event")
async def receive_onebot_event(request: Request) -> dict[str, Any]:
    """Receive a reverse HTTP event and journal it without an AI call."""
    # The signature covers the exact bytes sent, so read them before parsing.
    body = await request.body()
    if not event_authorized(
        body,
        request.headers.get("x-signature", ""),
        request.headers.get("authorization", ""),
        os.environ.get("QQBOT_EVENT_TOKEN", ""),
    ):
        raise HTTPException(401, "事件 token 无效")
    try:
        event = json.loads(body)
    except ValueError as exc:
        raise HTTPException(400, "事件不是 JSON") from exc
    if not isinstance(event, dict):
        raise HTTPException(400, "事件不是 JSON 对象")
    return await run_in_threadpool(handle_event, event)


def handle_event(event: dict[str, Any]) -> dict[str, Any]:
    accepted = event_journal.append(event)
    if accepted:
        from .memory_model import MemoryService
        memory_executor.submit(MemoryService(event_store).activate_candidates,
            str(event.get("group_id", "")), "".join(s.get("data", {}).get("text", "") for s in event.get("message", []) if isinstance(s, dict) and s.get("type") == "text"))
    if accepted and image_segments(event):
        # QQ image links expire within hours; copy them now, not at ingestion.
        image_executor.submit(cache_and_summarize, event)
    text = addressed_text(event)
    if accepted and str(event.get("user_id", "")) not in {"self", str(event.get("self_id", ""))}:
        brain = get_brain(str(event.get("group_id", "")))
        brain.event(mentioned=text is not None, question_count=1 if text is not None else 0,
                    timestamp=float(event.get("time") or time.time()))
    if accepted and text is not None:
        sender = event.get("sender") or {}
        task = event_store.create_task(str(event.get("group_id", "")), str(event.get("user_id", "")),
            str(event.get("message_id") or EventJournal.event_key(event)), sender.get("nickname", ""))
        executor.submit(reply_to_group, event, text, task)
    # NapCat reads this body as a "quick operation"; keep it free of keys such
    # as reply/ban/kick so nothing here is ever acted on.
    return {"ok": True, "accepted": accepted, "reply_queued": accepted and text is not None}


def cache_and_summarize(event):
    image_cache.fetch_event(event)
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    model = os.environ.get("QQBOT_MODEL", "deepseek-flash")
    if key and _capabilities.get(model, {}).get("images"):
        files = DeepSeekImageFiles(event_store, key)
        files.summarize(event, image_cache, make_post(key), model)


def reply_to_group(event: dict[str, Any], text: str, task=None, proactive=False) -> None:
    context = ReplyContext(str(event.get("group_id", "")), str(event.get("user_id", "")), text)
    if not proactive and (not task or task["status"] == "queued") and reply_policy.respond(context) is None:
        if task: event_store.update_task(task["id"], "skipped", "回复冷却")
        return
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        if task: event_store.update_task(task["id"], "failed", "未配置 DeepSeek API key")
        print("群回复跳过：未配置 DEEPSEEK_API_KEY")
        return
    with _brains_lock:
        if context.group_id in _inflight:
            # Mentioned requests remain queued and recoverable.
            return
        _inflight.add(context.group_id)
    try:
        sender = event.get("sender") if isinstance(event.get("sender"), dict) else {}
        sender_context = (
            f"群号：{event.get('group_id', '')}\n"
            f"发送者 QQ：{event.get('user_id', '')}\n"
            f"发送者昵称：{sender.get('nickname', '')}\n"
            f"群名片：{sender.get('card', '')}\n"
            f"群角色：{sender.get('role', 'member')}"
        )
        style_ctx = ""
        if reply_style_k > 0:
            try:
                sm = _get_style_memory()
                if sm is not None:
                    hits = sm.search(text, context.group_id, k=reply_style_k, kind="text")
                    if hits:
                        lines = [h["text"] for h in hits if h.get("text")]
                        style_ctx = "\n".join(lines)
            except Exception as exc:  # noqa: BLE001
                print(f"风格检索失败（不影响回复）：{exc}")
        trigger_id = str(event.get("message_id", EventJournal.event_key(event)))
        task = task or event_store.create_task(context.group_id, context.user_id, trigger_id,
            sender.get("nickname") or sender.get("card") or context.user_id)
        if task["status"] == "sent":
            return
        model = os.environ.get("QQBOT_MODEL", "deepseek-flash")
        post = make_post(api_key)
        files = DeepSeekImageFiles(event_store, api_key)
        def view_images(source):
            caps = _capabilities.get(model, event_store.get_state("capabilities:" + model, {}))
            if not caps.get("images"):
                raise RuntimeError("模型图片输入能力探测未通过")
            parts, missing = files.cached_parts(source, image_cache)
            return {"images": parts, "missing": missing}
        registry = ToolRegistry(event_store, _onebot, image_view=view_images)
        install_admin_tools(registry)
        install_collection_tools(registry, model_classifier(post))
        agent = Agent(event_store, registry, post, model=model,
            max_rounds=int(os.environ.get("QQBOT_TOOL_ROUNDS", "3")), max_tokens=int(RuntimeSettings(event_store).get("reply_max_tokens")),
            capabilities=_capabilities.get(model, event_store.get_state("capabilities:" + model, {})),
            use_langgraph=True)
        parts = []
        if image_segments(event):
            parts = view_images(event)["images"]
            files.summarize(event, image_cache, post, model)
        brain = get_brain(context.group_id)
        judge_model = os.environ.get("QQBOT_JUDGE_MODEL", "deepseek-flash")
        judge = model_judge(post, model=judge_model,
            capabilities=_capabilities.get(judge_model, event_store.get_state("capabilities:" + judge_model, {})),
            audit=lambda result: event_store.audit(task, "judge", {}, result))
        transcript = lambda: event_store.transcript(context.group_id, max_chars=reply_context_chars, trigger_id=trigger_id)
        def generate(current, regenerate):
            messages = prompt_messages(current,
                style_notes=event_store.get_state("style_notes:" + context.group_id, "TODO(人工调)：风格笔记"),
                emotions=brain.prompt_suffix(), now=time.strftime("%Y-%m-%d %H:%M:%S"),
                instruction=sender_context + "\n相似句语气参考：\n" + style_ctx, images=parts)
            return agent.regenerate(task, messages) if regenerate else agent.run(task, messages)
        def send(answer, reply_to):
            # A crash after sending has an unknown result; do not resend automatically.
            event_store.update_task(task["id"], "sending", answer)
            message = [{"type": "reply", "data": {"id": str(reply_to)}}, {"type": "text", "data": {"text": answer}}] if reply_to else answer
            result = _onebot("send_group_msg", {"group_id": context.group_id, "message": message})
            message_id = str(result.get("message_id")) if isinstance(result, dict) and result.get("message_id") else None
            event_journal.append_bot_message(context.group_id, answer, message_id, reply_to=trigger_id)
            event_store.update_task(task["id"], "sent", answer)
        result = TurnCoordinator(brain, judge).respond(transcript, generate, send, mentioned=not proactive)
        if not result["sent"]: event_store.update_task(task["id"], "skipped", result["why"])
    except Exception as exc:
        if task and event_store.task(task["id"])["status"] != "sending":
            event_store.update_task(task["id"], "failed", str(exc))
        print(f"群回复失败：{type(exc).__name__}")
    finally:
        with _brains_lock:
            _inflight.discard(context.group_id)
        queued = event_store.rows("SELECT * FROM tasks WHERE group_id=? AND status='queued' ORDER BY updated LIMIT 1", (context.group_id,))
        if queued:
            next_task = queued[0]
            row = event_store.message(next_task["group_id"], next_task["trigger_id"])
            if row:
                source = json.loads(row["raw"])
                executor.submit(reply_to_group, source, addressed_text(source) or "参与讨论", next_task,
                                ":proactive:" in next_task["id"])


@app.post("/api/jobs")
def create_job(request: JobRequest) -> dict[str, str]:
    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {"id": job_id, "status": "queued", "diagnose": request.diagnose}
    executor.submit(run_job, job_id, request)
    return {"id": job_id, "status": "queued"}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(404, "任务不存在")
        return dict(job)


@app.get("/api/tasks")
def tasks(limit: int = 50) -> dict[str, Any]:
    return {"tasks": event_store.rows("SELECT * FROM tasks ORDER BY updated DESC LIMIT ?", (max(1, min(limit, 200)),))}


@app.get("/api/audit")
def audit(limit: int = 100) -> dict[str, Any]:
    return {"audit": event_store.rows("SELECT * FROM audit ORDER BY ts DESC LIMIT ?", (max(1, min(limit, 500)),))}


@app.get("/api/memory/forgetting")
def forgetting() -> dict[str, Any]:
    return {"simulated": [event_store.get_state("memory_sleep:" + row["group_id"], {})
        for row in event_store.rows("SELECT DISTINCT group_id FROM memory_state")], "enabled": os.environ.get("QQBOT_MEMORY_FORGET_ENABLED", "0")}


@app.get("/api/recycle-bin")
def recycle_bin() -> dict[str, Any]:
    return {"items": event_store.rows("SELECT * FROM recycle_bin ORDER BY deleted DESC")}


def web_host() -> str:
    return os.environ.get("QQBOT_WEB_HOST", "").strip() or "127.0.0.1"


def web_port() -> int:
    # Not 8787: on Windows with Hyper-V/WSL that port often sits in an excluded
    # range and binding fails with WinError 10013.
    return int(os.environ.get("QQBOT_WEB_PORT", "").strip() or DEFAULT_WEB_PORT)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=web_host(), port=web_port())


if __name__ == "__main__":
    main()
