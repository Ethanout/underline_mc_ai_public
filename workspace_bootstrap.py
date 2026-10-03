"""Make the retained QQ bot package importable during local development."""
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_DIRS = (ROOT / "apps" / "qqbot" / "src",)


def add_workspace_packages() -> None:
    for source_dir in reversed(SOURCE_DIRS):
        value = str(source_dir)
        if value not in sys.path:
            sys.path.insert(0, value)
