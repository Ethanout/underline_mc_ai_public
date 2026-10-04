"""Local-only service: journal NapCat events, run ``/毯`` tool tasks, serve the plugin.

Chat replies belong to MaiBot.  This service keeps the parts MaiBot has no
equivalent for: a signed record of every group message, tasks bound to the
sender's own permissions (admin only by ``QQBOT_ADMIN_IDS``), the trick library
and essence export.  Identity always comes from the NapCat event that carried
the ``/毯`` message, never from MaiBot or the plugin.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import ipaddress
import json
import os
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from . import essence_exporter as exporter
from .admin_tools import install_admin_tools, redact
from .agent import Agent, make_post, prompt_messages
from .collection import install_collection_tools, model_classifier
from .deepseek import probe_capabilities
from .deepseek_files import DeepSeekImageFiles
from .events import EventJournal
from .images import DEFAULT_IMAGE_DIR, ImageCache, image_segments
from .store import Store
from .tools import ToolRegistry, admin_ids

APP_ROOT = Path(__file__).resolve().parent
STATIC_INDEX = APP_ROOT / "static" / "index.html"
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="qqbot-export")
task_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="qqbot-task")
jobs: dict[str, dict[str, Any]] = {}
jobs_lock = threading.Lock()

# ``/毯 <要做的事>``.  ``/毯毯`` and ``/毯子`` are ordinary chat, not the command.
TASK_COMMAND = re.compile(r"^\s*/毯(?![\w毯])\s*(?P<request>[\s\S]*)$")
# Read-only tools MaiBot's planner may call through the plugin.
PLUGIN_TOOLS = ("search_knowledge", "search_chat", "read_essence")
MAX_ANSWER_CHARS = 3000



@asynccontextmanager
async def lifespan(app):
    await run_in_threadpool(probe_models)
    stop = threading.Event()
    worker = threading.Thread(
        target=background_work, args=(stop,), daemon=True, name="qqbot-maintenance"
    )
    worker.start()
    recover_tasks()
    try:
        yield
    finally:
        stop.set()
        worker.join(timeout=2)


app = FastAPI(title="QQ Bot", version="0.2.0", lifespan=lifespan)


@app.middleware("http")
async def local_only(request, call_next):
    try:
        local = request.client is not None and ipaddress.ip_address(request.client.host).is_loopback
    except ValueError:
        local = False
    if not local:
        return JSONResponse({"detail": "管理服务只接受本机连接"}, status_code=403)
    return await call_next(request)


event_store = Store()
event_journal = EventJournal(
    Path(os.environ.get("QQBOT_EVENT_LOG", "runtime/private/qq_events.jsonl")), store=event_store
)
# Own single worker: a slow image host must not hold up tasks or export jobs.
image_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="qqbot-images")
image_cache = ImageCache(os.environ.get("QQBOT_IMAGE_DIR", DEFAULT_IMAGE_DIR))
reply_context_chars = int(os.environ.get("QQBOT_REPLY_CONTEXT_CHARS", "3000"))

_capabilities: dict[str, Any] = {}
_submitted: set[str] = set()
_submitted_lock = threading.Lock()


def task_model() -> str:
    return os.environ.get("QQBOT_MODEL", "deepseek-flash")


def model_capabilities() -> dict[str, Any]:
    model = task_model()
    return _capabilities.get(model) or event_store.get_state("capabilities:" + model, {})


def _onebot(action, params):
    return exporter.api_call(
        onebot_endpoint(), os.environ.get("ONEBOT_ACCESS_TOKEN"), action, params, False
    )


def _probe_upload(raw, ttl):
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        path = Path(directory) / "probe.png"
        path.write_bytes(raw)
        return DeepSeekImageFiles(
            event_store, os.environ.get("DEEPSEEK_API_KEY", ""), ttl=ttl
        ).upload(path)[0]


def probe_models():
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        _capabilities["error"] = "未配置 DeepSeek API key"
        return
    model = task_model()
    value = probe_capabilities(make_post(key), _probe_upload, model)
    _capabilities[model] = value
    event_store.set_state("capabilities:" + model, value)


def background_work(stop):
    interval_minutes = float(os.environ.get("QQBOT_ESSENCE_SYNC_MINUTES", "60"))
    due = time.time() + interval_minutes * 60
    while not stop.wait(20):
        if interval_minutes <= 0 or time.time() < due:
            continue
        try:
            sync_essence()
        except Exception as exc:
            event_store.set_state(
                "maintenance:essence_sync", {"at": time.time(), "error": type(exc).__name__}
            )
        due = time.time() + interval_minutes * 60


def sync_essence():
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        return
    registry = ToolRegistry(event_store, _onebot)
    tricks = install_collection_tools(registry, model_classifier(make_post(key)))
    for group in sorted(known_groups()):
        # Scheduled collection uses service provenance, never a forged group role.
        task = {"group_id": group}
        data = registry.read_essence(task, {})
        available = [
            row for row in data["messages"] if exporter.message_id(row) not in data["missing"]
        ]
        tricks.sync(group, available)
    tricks.reindex()


def configured_groups() -> set[str]:
    return {g.strip() for g in os.environ.get("QQBOT_GROUPS", "").split(",") if g.strip()}


def known_groups() -> set[str]:
    """Groups the service works for: ``QQBOT_GROUPS``, else every group seen."""
    groups = configured_groups()
    if groups:
        return groups
    return {row["group_id"] for row in event_store.rows("SELECT DISTINCT group_id FROM messages")}


def group_allowed(group_id: str) -> bool:
    groups = configured_groups()
    if groups:
        return str(group_id) in groups
    return bool(event_store.rows("SELECT 1 FROM messages WHERE group_id=? LIMIT 1", (str(group_id),)))


def message_text(event: dict[str, Any]) -> str:
    segments = event.get("message", [])
    if isinstance(segments, str):
        return segments
    return "".join(
        str(segment.get("data", {}).get("text", ""))
        for segment in segments
        if isinstance(segment, dict) and segment.get("type") == "text"
    )


def task_request(event: dict[str, Any]) -> str | None:
    """The request after ``/毯``, or None when this message is not the command."""
    if event.get("post_type") != "message" or event.get("message_type") != "group":
        return None
    if str(event.get("user_id", "")) in {"self", str(event.get("self_id", ""))}:
        return None
    match = TASK_COMMAND.match(message_text(event))
    return match.group("request").strip() if match else None


def rate_limited(group_id: str, user_id: str) -> bool:
    """Members get a few tasks per window; each one costs model tokens."""
    if user_id in admin_ids():
        return False
    window = float(os.environ.get("QQBOT_TASK_WINDOW", "600"))
    limit = int(os.environ.get("QQBOT_TASK_LIMIT", "5"))
    recent = event_store.rows(
        "SELECT COUNT(*) AS n FROM tasks WHERE group_id=? AND user_id=? AND updated>=?",
        (group_id, user_id, event_store.clock() - window),
    )
    return recent[0]["n"] > limit


def submit_task(task: dict[str, Any]) -> bool:
    with _submitted_lock:
        if task["id"] in _submitted:
            return False
        _submitted.add(task["id"])
    task_executor.submit(run_task, task)
    return True


def recover_tasks():
    """Resume ``/毯`` tasks a restart interrupted.  Anything else is left alone.

    A task whose answer may already have gone out (``sending``) is not resent.
    """
    for task in event_store.rows("SELECT * FROM tasks WHERE status IN ('queued','running','completed')"):
        row = event_store.message(task["group_id"], task["trigger_id"])
        if row and task_request(json.loads(row["raw"])) is not None:
            submit_task(task)


def build_registry(api_key: str, post) -> ToolRegistry:
    files = DeepSeekImageFiles(event_store, api_key)

    def view_images(source):
        if not model_capabilities().get("images"):
            raise RuntimeError("模型图片输入能力探测未通过")
        parts, missing = files.cached_parts(source, image_cache)
        return {"images": parts, "missing": missing}

    registry = ToolRegistry(event_store, _onebot, image_view=view_images)
    install_admin_tools(registry)
    install_collection_tools(registry, model_classifier(post))
    return registry


def task_images(api_key: str, row: dict[str, Any]) -> list[dict[str, Any]]:
    """Images in the command message and in the message it quotes, if the model can see."""
    if not model_capabilities().get("images"):
        return []
    files = DeepSeekImageFiles(event_store, api_key)
    sources = [json.loads(row["raw"])]
    if row["quote_id"]:
        quoted = event_store.message(row["group_id"], row["quote_id"])
        if quoted:
            sources.append(json.loads(quoted["raw"]))
    parts: list[dict[str, Any]] = []
    for source in sources:
        if not image_segments(source):
            continue
        try:
            image_cache.fetch_event(source)
            parts.extend(files.cached_parts(source, image_cache)[0])
        except Exception as exc:  # noqa: BLE001 - an unreadable image must not sink the task
            print(f"任务图片读取失败（不影响任务）：{type(exc).__name__}")
    return parts[:4]


def run_task(task: dict[str, Any]) -> None:
    try:
        current = event_store.task(task["id"])
        if current is None or current["status"] in {"sending", "sent", "failed", "skipped"}:
            return
        row = event_store.message(task["group_id"], task["trigger_id"])
        if row is None:
            event_store.update_task(task["id"], "failed", "找不到发起任务的消息")
            return
        event = json.loads(row["raw"])
        request = task_request(event) or ""
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            event_store.update_task(task["id"], "failed", "未配置 DeepSeek API key")
            send(task, "没配 DeepSeek key，这件事办不了。")
            return
        if not request:
            event_store.update_task(task["id"], "skipped", "空任务")
            send(task, "要我做什么？在 /毯 后面写上，比如：/毯 找找 execute 转视角的技巧")
            return
        post = make_post(api_key)
        registry = build_registry(api_key, post)
        agent = Agent(
            event_store,
            registry,
            post,
            model=task_model(),
            max_rounds=int(os.environ.get("QQBOT_TOOL_ROUNDS", "4")),
            max_tokens=int(os.environ.get("QQBOT_TASK_MAX_TOKENS", "800")),
            capabilities=model_capabilities(),
            use_langgraph=True,
        )
        sender = event.get("sender") if isinstance(event.get("sender"), dict) else {}
        name = sender.get("card") or sender.get("nickname") or task["user_id"]
        role = "管理员" if registry.is_admin(task) else "群成员"
        messages = prompt_messages(
            event_store.transcript(
                task["group_id"], max_chars=reply_context_chars, trigger_id=task["trigger_id"]
            ),
            request=request,
            sender=f"{name}（QQ {task['user_id']}，{role}）",
            now=time.strftime("%Y-%m-%d %H:%M:%S"),
            images=task_images(api_key, row),
        )
        answer = agent.run(task, messages)
        send(task, answer)
    except Exception as exc:  # noqa: BLE001 - report every failure to the requester
        latest = event_store.task(task["id"])
        if latest and latest["status"] not in {"sending", "sent"}:
            event_store.update_task(task["id"], "failed", redact(str(exc)))
            try:
                send(task, "这件事没办成：" + redact(str(exc))[:200])
            except Exception:  # noqa: BLE001 - NapCat unreachable; the task row keeps the reason
                pass
        print(f"任务失败：{type(exc).__name__}")


def send(task: dict[str, Any], answer: str) -> None:
    """Reply to the command message.  A crash mid-send is not retried: it may have gone out."""
    answer = answer.strip()
    if len(answer) > MAX_ANSWER_CHARS:
        answer = answer[:MAX_ANSWER_CHARS] + f"\n（太长了，后面没发。完整结果见管理页任务 {task['id']}）"
    final = event_store.task(task["id"])["status"] not in {"failed", "skipped"}
    if final:
        event_store.update_task(task["id"], "sending", answer)
    message = [
        {"type": "reply", "data": {"id": str(task["trigger_id"])}},
        {"type": "text", "data": {"text": answer}},
    ]
    result = _onebot("send_group_msg", {"group_id": task["group_id"], "message": message})
    message_id = (
        str(result.get("message_id"))
        if isinstance(result, dict) and result.get("message_id")
        else None
    )
    event_journal.append_bot_message(
        task["group_id"], answer, message_id, reply_to=task["trigger_id"]
    )
    if final:
        event_store.update_task(task["id"], "sent", answer)


def plugin_authorized(authorization: str) -> bool:
    """The MaiBot plugin's bearer token.  No token configured means closed, not open."""
    expected = os.environ.get("QQBOT_PLUGIN_TOKEN", "").strip()
    supplied = authorization.removeprefix("Bearer ").strip()
    return bool(expected) and bool(supplied) and hmac.compare_digest(
        supplied.encode("utf-8"), expected.encode("utf-8")
    )


class PluginToolRequest(BaseModel):
    tool: str = Field(min_length=1, max_length=64)
    group_id: str = Field(min_length=1, max_length=32)
    args: dict[str, Any] = Field(default_factory=dict)


@app.post("/api/plugin/tool")
def plugin_tool(body: PluginToolRequest, request: Request) -> dict[str, Any]:
    """Read-only lookups for MaiBot's planner.

    MaiBot does not tell a plugin tool who in a group triggered it, so these
    calls run as an unprivileged ``maibot`` caller: member tools only, scoped
    to one group the service works for.  Anything needing a person's rights
    goes through ``/毯``.
    """
    if not plugin_authorized(request.headers.get("authorization", "")):
        raise HTTPException(401, "插件 token 无效")
    if body.tool not in PLUGIN_TOOLS:
        raise HTTPException(403, "这个工具不对插件开放")
    if not re.fullmatch(r"\d+", body.group_id) or not group_allowed(body.group_id):
        raise HTTPException(403, "不在服务的群列表里")
    args = {key: value for key, value in body.args.items() if key != "group_id"}
    task = event_store.create_task(body.group_id, "maibot", "maibot:" + uuid.uuid4().hex, "MaiBot")
    event_store.update_task(task["id"], "done")
    registry = ToolRegistry(event_store, _onebot)
    return registry.execute(event_store.task(task["id"]), body.tool, args)


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
        "plugin_token_configured": bool(os.environ.get("QQBOT_PLUGIN_TOKEN", "").strip()),
        "onebot_endpoint": onebot_endpoint(),
        "chat_engine": "maibot",
        "model": task_model(),
        "capabilities": _capabilities
        or {task_model(): event_store.get_state("capabilities:" + task_model(), {})},
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
    return bool(supplied) and hmac.compare_digest(
        supplied.encode("utf-8"), expected.encode("utf-8")
    )


@app.post("/api/onebot/event")
async def receive_onebot_event(request: Request) -> dict[str, Any]:
    """Receive a reverse HTTP event and journal it."""
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
    if accepted and image_segments(event):
        # QQ image links expire within hours; copy them now, not when a task asks.
        image_executor.submit(image_cache.fetch_event, event)
    request = task_request(event) if accepted else None
    queued = False
    if request is not None and group_allowed(str(event.get("group_id", ""))):
        sender = event.get("sender") if isinstance(event.get("sender"), dict) else {}
        task = event_store.create_task(
            str(event.get("group_id", "")),
            str(event.get("user_id", "")),
            str(event.get("message_id") or EventJournal.event_key(event)),
            sender.get("nickname", ""),
        )
        if rate_limited(task["group_id"], task["user_id"]):
            event_store.update_task(task["id"], "skipped", "任务太频繁")
        else:
            queued = submit_task(task)
    # NapCat reads this body as a "quick operation"; keep it free of keys such
    # as reply/ban/kick so nothing here is ever acted on.
    return {"ok": True, "accepted": accepted, "task_queued": queued}


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
    return {
        "tasks": event_store.rows(
            "SELECT * FROM tasks ORDER BY updated DESC LIMIT ?", (max(1, min(limit, 200)),)
        )
    }


@app.get("/api/audit")
def audit(limit: int = 100) -> dict[str, Any]:
    rows = event_store.rows(
        "SELECT * FROM audit ORDER BY ts DESC LIMIT ?", (max(1, min(limit, 500)),)
    )
    return {"audit": json.loads(redact(json.dumps(rows, ensure_ascii=False)))}


@app.get("/api/tasks/{task_id}")
def task_status(task_id: str):
    task = event_store.task(task_id)
    if task is None:
        raise HTTPException(404, "任务不存在")
    return task


@app.get("/api/tricks")
def tricks(limit: int = 100):
    return {
        "items": event_store.rows(
            "SELECT * FROM memory_state WHERE kind='trick' ORDER BY updated DESC LIMIT ?",
            (max(1, min(limit, 500)),),
        )
    }


@app.get("/api/capabilities")
def capabilities():
    return health()["capabilities"]


def web_host() -> str:
    host = os.environ.get("QQBOT_WEB_HOST", "").strip() or "127.0.0.1"
    if host == "localhost":
        return "127.0.0.1"
    try:
        if ipaddress.ip_address(host).is_loopback:
            return host
    except ValueError:
        pass
    raise ValueError("QQBOT_WEB_HOST 必须是本机回环地址")


def web_port() -> int:
    # Not 8787: on Windows with Hyper-V/WSL that port often sits in an excluded
    # range and binding fails with WinError 10013.
    return int(os.environ.get("QQBOT_WEB_PORT", "").strip() or DEFAULT_WEB_PORT)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=web_host(), port=web_port())


if __name__ == "__main__":
    main()
