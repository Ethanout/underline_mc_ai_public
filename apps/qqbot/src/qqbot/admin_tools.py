"""Host-account tools remain admin-only and redact credential output."""
from __future__ import annotations

import os
import re
import subprocess
import urllib.request
from pathlib import Path

from .settings import KEY_FILES


def protected_path(path):
    path = Path(path).resolve()
    if path.name == ".env" or "config" in {p.lower() for p in path.parts}:
        raise PermissionError("配置和密钥文件不能读进对话")
    for env in KEY_FILES:
        configured = os.environ.get(env)
        if configured:
            key_path = Path(configured).resolve()
            if path == key_path or path.is_relative_to(key_path.parent):
                raise PermissionError("配置和密钥文件不能读进对话")
    return path


def redact(text):
    text = re.sub(r"sk-[A-Za-z0-9_-]+", "[密钥已隐藏]", str(text))
    for name in KEY_FILES.values():
        secret = os.environ.get(name, "")
        if secret: text = text.replace(secret, "[密钥已隐藏]")
    return text


def install_admin_tools(registry, web_search=None, web_read=None, runner=subprocess.run):
    def read_file(task, args):
        path = protected_path(args["path"])
        with path.open("rb") as handle:
            raw = handle.read(1_000_001)
        if len(raw) > 1_000_000: raise ValueError("文件超过读取大小限制")
        return {"content": redact(raw.decode("utf-8"))}

    def write_file(task, args):
        path = protected_path(args["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(args["content"]), encoding="utf-8")
        return {"status": "written"}

    def command(task, args):
        timeout = max(1, min(120, float(args.get("timeout", 30))))
        try:
            result = runner(str(args["command"]), shell=True, capture_output=True, text=True, timeout=timeout)
            return {"returncode": result.returncode, "stdout": redact(result.stdout), "stderr": redact(result.stderr)}
        except subprocess.TimeoutExpired as exc:
            return {"error": "命令执行超时", "stdout": redact(exc.stdout or ""), "stderr": redact(exc.stderr or "")}

    def read_web(task, args):
        url = str(args["url"])
        if not url.startswith(("http://", "https://")): raise ValueError("网页地址必须是 HTTP 或 HTTPS")
        if web_read: return {"content": redact(web_read(url))}
        with urllib.request.urlopen(url, timeout=20) as response:
            return {"content": redact(response.read(1_000_000).decode("utf-8", errors="replace"))}

    def search_web(task, args):
        if not web_search: raise RuntimeError("网页搜索提供方未配置")
        return {"results": web_search(str(args["query"]))}

    for name, handler, props in (
        ("read_file", read_file, {"path": "string"}),
        ("write_file", write_file, {"path": "string", "content": "string"}),
        ("run_command", command, {"command": "string", "timeout": "number"}),
        ("web_read", read_web, {"url": "string"}),
        ("web_search", search_web, {"query": "string"}),
    ):
        registry.register(name, handler, admin_only=True, libraries=(), properties=props)
