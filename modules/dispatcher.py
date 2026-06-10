"""
任务调度器
=========
统一管理后台任务：启动、状态查询、取消。
app.py 和 opencode 都通过此模块调度业务逻辑。
"""
import asyncio
import threading
import uuid
import time
import traceback
from dataclasses import dataclass, field
from typing import Callable, Any, Optional


@dataclass
class TaskInfo:
    task_id: str
    name: str
    status: str = "pending"          # pending | running | done | failed | cancelled
    progress: float = 0.0            # 0.0 ~ 1.0
    log: list[str] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    _cancel_event: threading.Event = field(default_factory=threading.Event)

    def cancel_requested(self) -> bool:
        return self._cancel_event.is_set()


_tasks: dict[str, TaskInfo] = {}
_lock = threading.Lock()


def start(name: str, fn: Callable, *args, **kwargs) -> str:
    """启动后台任务，返回 task_id"""
    task_id = uuid.uuid4().hex[:8]
    info = TaskInfo(task_id=task_id, name=name)
    with _lock:
        _tasks[task_id] = info

    def _run():
        info.status = "running"
        info.started_at = time.time()
        try:
            info.result = fn(*args, cancel_event=info._cancel_event, **kwargs)
            info.status = "cancelled" if info.cancel_requested() else "done"
        except Exception as e:
            info.error = f"{e}\n{traceback.format_exc()}"
            info.status = "failed"
        finally:
            info.finished_at = time.time()

    t = threading.Thread(target=_run, daemon=True, name=f"task-{task_id}")
    t.start()
    return task_id


def start_async(name: str, coro_fn: Callable, *args, **kwargs) -> str:
    """启动异步后台任务"""
    task_id = uuid.uuid4().hex[:8]
    info = TaskInfo(task_id=task_id, name=name)
    with _lock:
        _tasks[task_id] = info

    def _run():
        info.status = "running"
        info.started_at = time.time()
        loop = asyncio.new_event_loop()
        try:
            info.result = loop.run_until_complete(
                coro_fn(*args, cancel_event=info._cancel_event, **kwargs)
            )
            info.status = "cancelled" if info.cancel_requested() else "done"
        except Exception as e:
            info.error = f"{e}\n{traceback.format_exc()}"
            info.status = "failed"
        finally:
            loop.close()
            info.finished_at = time.time()

    t = threading.Thread(target=_run, daemon=True, name=f"task-{task_id}")
    t.start()
    return task_id


def cancel(task_id: str) -> bool:
    """请求取消任务"""
    with _lock:
        info = _tasks.get(task_id)
    if not info:
        return False
    info._cancel_event.set()
    return True


def status(task_id: str) -> Optional[dict]:
    """获取任务状态"""
    with _lock:
        info = _tasks.get(task_id)
    if not info:
        return None
    return _info_to_dict(info)


def list_tasks() -> list[dict]:
    """列出所有任务"""
    with _lock:
        return [_info_to_dict(info) for info in _tasks.values()]


def _info_to_dict(info: TaskInfo) -> dict:
    return {
        "task_id": info.task_id,
        "name": info.name,
        "status": info.status,
        "progress": info.progress,
        "log": info.log[-20:],
        "error": info.error,
        "result": info.result,
        "started_at": info.started_at,
        "finished_at": info.finished_at,
        "duration": (info.finished_at or time.time()) - info.started_at if info.started_at else None,
    }
