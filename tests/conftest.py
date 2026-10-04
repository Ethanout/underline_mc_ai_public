"""Tests must not load a user's credentials or make network requests."""

from __future__ import annotations

import os
import socket
import tempfile
import urllib.request
from pathlib import Path

import pytest

# Set isolation before importing qqbot, whose package initializer loads settings.
_runtime = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
os.environ["QQBOT_ENV_FILE"] = str(Path(_runtime.name) / "absent.env")
os.environ["QQBOT_DB"] = str(Path(_runtime.name) / "test.db")
os.environ["NAPCAT_DIR"] = ""
for _name in (
    "DEEPSEEK_KEY_FILE",
    "QQBOT_EMBED_API_KEY_FILE",
    "ONEBOT_ACCESS_TOKEN_FILE",
    "QQBOT_EVENT_TOKEN_FILE",
    "DEEPSEEK_API_KEY",
    "QQBOT_EMBED_API_KEY",
    "ONEBOT_ACCESS_TOKEN",
    "QQBOT_EVENT_TOKEN",
):
    os.environ.pop(_name, None)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise RuntimeError("离线测试禁止网络请求")

    monkeypatch.setattr(urllib.request, "urlopen", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
