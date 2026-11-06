"""Install the official adapter beside NapCat without changing MaiBot core files."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from .maibot import maibot_dir


def install(directory: Path, *, root: Path | None = None):
    root = root or Path(__file__).resolve().parents[4]
    source = root / "apps/maibot_plugin/qq_official_adapter"
    target = directory.resolve() / "plugins/underline_qq_official"
    if not (directory / "bot.py").is_file():
        raise ValueError("指定目录不是麦麦工作区：缺少 bot.py")
    target.mkdir(parents=True, exist_ok=True)
    for path in source.iterdir():
        if path.suffix not in {".py", ".json", ".md"}:
            continue
        destination = target / path.name
        if destination.exists() and destination.read_bytes() != path.read_bytes():
            shutil.copy2(destination, destination.with_suffix(destination.suffix + ".bak"))
        shutil.copy2(path, destination)
    config = target / "config.toml"
    if not config.exists():
        token_file = Path(os.environ.get("QQBOT_PLUGIN_TOKEN_FILE", "config/api/qqbot_plugin.txt"))
        if not token_file.is_absolute():
            token_file = root / token_file
        port = int(os.environ.get("QQBOT_WEB_PORT", "18787"))
        config.write_text(
            '[plugin]\nenabled = true\nconfig_version = "1.0.0"\n\n[service]\n'
            f'service_url = "http://127.0.0.1:{port}"\n'
            f'token_file = {json.dumps(token_file.resolve().as_posix(), ensure_ascii=False)}\n'
            'state_dir = "data/qq_official_adapter"\n', encoding="utf-8",
        )
    if not (target / ".git").exists():
        subprocess.run(["git", "init", str(target)], check=True, capture_output=True)
    return target


def main():
    directory = maibot_dir()
    if directory is None:
        raise SystemExit("请先在 .env 配置 MAIBOT_DIR")
    print(f"官方 QQ 适配器已安装：{install(directory)}")
    print("重载麦麦插件后，在资料服务首页添加官方机器人。原 NapCat 配置保留。")
    return 0
