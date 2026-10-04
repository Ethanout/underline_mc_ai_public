"""Small, local-only WebUI backend for the QQ essence exporter."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import threading
import uuid
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

APP_ROOT = Path(__file__).resolve().parent
STATIC_INDEX = APP_ROOT / "static" / "index.html"
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="qqbot-export")
jobs: dict[str, dict[str, Any]] = {}
jobs_lock = threading.Lock()

app = FastAPI(title="QQ Bot Exporter", version="0.1.0")
event_journal = EventJournal(Path(os.environ.get("QQBOT_EVENT_LOG", "runtime/private/qq_events.jsonl")))
# Own single worker: a slow image host must not hold up replies or export jobs.
image_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="qqbot-images")
image_cache = ImageCache(os.environ.get("QQBOT_IMAGE_DIR", DEFAULT_IMAGE_DIR))
reply_policy = ReplyPolicy(float(os.environ.get("QQBOT_REPLY_COOLDOWN", "1")))
reply_max_tokens = int(os.environ.get("QQBOT_REPLY_MAX_TOKENS", "220"))
reply_context_chars = int(os.environ.get("QQBOT_REPLY_CONTEXT_CHARS", "3000"))
reply_style_k = int(os.environ.get("QQBOT_STYLE_REPLY_K", "5"))

_style_memory_lock = threading.Lock()
_style_memory_instance = None


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
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "token_configured": str(bool(os.environ.get("ONEBOT_ACCESS_TOKEN"))).lower(),
        "onebot_endpoint": onebot_endpoint(),
        "observation_mode": "true",
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
    if accepted and image_segments(event):
        # QQ image links expire within hours; copy them now, not at ingestion.
        image_executor.submit(image_cache.fetch_event, event)
    text = addressed_text(event)
    if text is not None:
        executor.submit(reply_to_group, event, text)
    # NapCat reads this body as a "quick operation"; keep it free of keys such
    # as reply/ban/kick so nothing here is ever acted on.
    return {"ok": True, "accepted": accepted, "reply_queued": text is not None}


def reply_to_group(event: dict[str, Any], text: str) -> None:
    context = ReplyContext(str(event.get("group_id", "")), str(event.get("user_id", "")), text)
    if reply_policy.respond(context) is None:
        return
    key_path = os.environ.get("DEEPSEEK_KEY_FILE", "")
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key and key_path and Path(key_path).exists():
        api_key = Path(key_path).read_text(encoding="utf-8").strip()
    if not api_key:
        print("群回复跳过：未配置 DEEPSEEK_API_KEY")
        return
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
        answer = deepseek_reply(
            text,
            api_key,
            max_tokens=reply_max_tokens,
            sender_context=sender_context,
            recent_context=event_journal.recent_context(context.group_id, reply_context_chars),
            style_context=style_ctx,
        )
        result = exporter.api_call(
            onebot_endpoint(),
            os.environ.get("ONEBOT_ACCESS_TOKEN"),
            "send_group_msg",
            {"group_id": context.group_id, "message": answer},
            False,
        )
        message_id = str(result.get("message_id")) if isinstance(result, dict) and result.get("message_id") else None
        trigger_id = event.get("message_id")
        event_journal.append_bot_message(
            context.group_id,
            answer,
            message_id,
            reply_to=str(trigger_id) if trigger_id is not None else None,
        )
    except Exception as exc:
        print(f"群回复失败：{exc}")


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
