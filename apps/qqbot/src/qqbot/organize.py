"""Organize a QQ essence export without modifying the original export."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any


KEYWORDS = {
    "datapack-minecraft": ("minecraft", "mcfunction", "数据包", "命令", "指令", "函数", "进度", "谓词", "战利品", "资源包"),
    "beet-toolchain": ("beet", "mecha", "bolt", "bookshelf", "python", "插件", "构建", "编译"),
    "tutorial-resource": ("教程", "文档", "资料", "链接", "网站", "wiki", "教程", "代码", "示例"),
}


def text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for segment in content:
        if not isinstance(segment, dict):
            continue
        data = segment.get("data") if isinstance(segment.get("data"), dict) else segment
        if segment.get("type") == "text" and isinstance(data, dict):
            parts.append(str(data.get("text", "")))
    return "\n".join(part for part in parts if part)


def classify(text: str, has_media: bool) -> str:
    lowered = text.casefold()
    scores = {category: sum(lowered.count(word.casefold()) for word in words) for category, words in KEYWORDS.items()}
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return "media-or-review" if has_media else "needs-review"


def stable_key(text: str, content: Any, media: list[dict[str, Any]] | None = None) -> str:
    """Identify duplicate messages while keeping distinct attachments separate."""
    media_keys = [
        {"type": item.get("type"), "source": item.get("source"), "file": item.get("file")}
        for item in (media or [])
    ]
    payload = json.dumps(
        {"text": text, "content": content, "media": media_keys},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def render_document(number: int, category: str, text: str, media: list[dict[str, Any]], duplicate_of: str | None) -> str:
    lines = ["---", f"category: {category}", "status: candidate", f"source_document: qq-{number:04d}"]
    if duplicate_of:
        lines.append(f"duplicate_of: {duplicate_of}")
    lines += ["---", "", text.strip() or "（仅包含媒体或未识别内容，待人工整理。）", ""]
    if media:
        lines += ["## 媒体", ""]
        for item in media:
            path = item.get("file") or item.get("error") or "未下载"
            lines.append(f"- `{item.get('type', 'unknown')}`: `{path}`")
    return "\n".join(lines) + "\n"


def organize(source: Path, output: Path) -> dict[str, Any]:
    data = json.loads(source.read_text(encoding="utf-8"))
    messages = data.get("messages", [])
    output.mkdir(parents=True, exist_ok=True)
    docs_dir = output / "documents"
    media_dir = output / "media"
    docs_dir.mkdir(exist_ok=True)
    media_dir.mkdir(exist_ok=True)
    seen: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    copied_media = 0
    for number, message in enumerate(messages, 1):
        text = text_from_content(message.get("content"))
        media = [item for item in message.get("media", []) if isinstance(item, dict)]
        category = classify(text, bool(media))
        key = stable_key(text, message.get("content"), media)
        duplicate_of = seen.get(key)
        document_id = f"qq-{number:04d}"
        seen.setdefault(key, document_id)
        local_media: list[dict[str, Any]] = []
        for media_index, item in enumerate(media):
            original = item.get("file")
            if not original:
                local_media.append(item)
                continue
            source_media = source.parent / "media" / Path(str(original)).name
            if source_media.exists():
                target = media_dir / f"{document_id}-{media_index:02d}-{source_media.name}"
                shutil.copy2(source_media, target)
                copied_media += 1
                local_media.append({"type": item.get("type"), "file": str(target.relative_to(output))})
            else:
                local_media.append({"type": item.get("type"), "error": "source media missing"})
        filename = docs_dir / f"{document_id}-{category}.md"
        filename.write_text(render_document(number, category, text, local_media, duplicate_of), encoding="utf-8")
        rows.append({"document": document_id, "category": category, "duplicate_of": duplicate_of, "has_media": bool(media)})
    counts = Counter(row["category"] for row in rows)
    index = {
        "schema_version": 1,
        "source": str(source),
        "original_preserved": True,
        "message_count": len(rows),
        "copied_media_count": copied_media,
        "duplicate_count": sum(row["duplicate_of"] is not None for row in rows),
        "category_counts": dict(sorted(counts.items())),
        "documents": rows,
    }
    (output / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "README.md").write_text(
        "# QQ 精华整理区\n\n原始导出只读保留；本目录是可审阅副本。`candidate` 内容进入正式知识库前必须人工核验版本、来源和 Minecraft 行为。重复项只标记，不删除原文。\n",
        encoding="utf-8",
    )
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description="整理 QQ 精华导出，不修改原始文件")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", default="runtime/private/qq_essence_organized", type=Path)
    args = parser.parse_args()
    result = organize(args.source.resolve(), args.output.resolve())
    print(f"整理完成：文档 {result['message_count']} 条，媒体 {result['copied_media_count']} 个，重复标记 {result['duplicate_count']} 条，输出 {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
