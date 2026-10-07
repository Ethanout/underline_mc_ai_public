"""Read-only search over Underline's own teaching material and mcfunction notes.

The sources are plain Markdown folders kept next to this repository:
``UNDERLINE_WIKI_ROOT`` (平行线 tutorials, hand-written tricks, command docs,
saved Wiki pages) and ``MCFSKILL_ROOT`` (the mcfunction engineering notes).
Files are split at headings so a hit points at one section, not a whole page.
The index is rebuilt only when a file is added, removed or modified.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_WIKI_ROOT = "../underline_wiki"
DEFAULT_MCFSKILL_ROOT = "../mcfskill"
SKIPPED_PARTS = ("归档", "Adobe Premiere Pro", ".git", "node_modules")
SKIPPED_NAMES = ("复制清单.md", "README.md", "LICENSE")
SECTION_CHARS = 1500
CJK = re.compile(r"[一-鿿]")
HEADING = re.compile(r"^(#{1,4})\s+(.+?)\s*#*\s*$")

# (folder prefix, label, weight).  First match wins; weight orders ties.
KINDS = (
    ("human_manual/", "人工整理的技巧（未实测）", 1.2),
    ("key_detection/", "按键检测方案（未实测）", 1.2),
    ("reference/", "Underline 规范", 1.1),
    ("language/", "Underline 规范", 1.1),
    ("视频/__命令教程/教程/", "平行线教程", 1.2),
    ("视频/__命令教程/资料库/knowledge_base/", "Wiki 摘录", 0.6),
    ("v1/", "教程大纲", 0.8),
    ("文档/", "Underline 文档", 1.0),
    ("mcfskill/", "mcfunction 笔记", 1.1),
)


@dataclass(frozen=True)
class Section:
    path: str
    title: str
    text: str
    label: str
    weight: float


def _root(env: str, default: str) -> Path:
    raw = os.environ.get(env, "").strip() or default
    path = Path(raw).expanduser()
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def default_roots() -> list[tuple[str, Path]]:
    """(display prefix, folder).  The mcfunction notes are only their references."""
    return [
        ("", _root("UNDERLINE_WIKI_ROOT", DEFAULT_WIKI_ROOT)),
        ("mcfskill/", _root("MCFSKILL_ROOT", DEFAULT_MCFSKILL_ROOT) / "references"),
    ]


def _kind(path: str) -> tuple[str, float]:
    for prefix, label, weight in KINDS:
        if path.startswith(prefix):
            return label, weight
    return "Underline 资料", 1.0


def _strip_front_matter(text: str) -> tuple[str, str]:
    """Drop a YAML header, keeping its title if it has one."""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end < 0:
        return "", text
    title = ""
    for line in text[3:end].splitlines():
        if line.startswith("title:"):
            title = line.split(":", 1)[1].strip().strip("\"'")
    return title, text[end + 4 :]


def split_sections(path: str, text: str) -> list[Section]:
    label, weight = _kind(path)
    title, body = _strip_front_matter(text.lstrip("﻿"))
    page = title or Path(path).stem.replace("_-_中文_Minecraft_Wiki", "")
    sections, heading, lines = [], "", []

    def flush():
        content = "\n".join(lines).strip()
        if len(content) < 20:
            return
        name = f"{page} > {heading}" if heading and heading != page else page
        for start in range(0, len(content), SECTION_CHARS):
            sections.append(Section(path, name, content[start : start + SECTION_CHARS], label, weight))

    in_code = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
        match = None if in_code else HEADING.match(line)
        if match:
            flush()
            heading, lines = re.sub(r"<[^>]+>", "", match.group(2)).strip(), []
        else:
            lines.append(line)
    flush()
    return sections


def _files(roots):
    for prefix, root in roots:
        if not root.is_dir():
            continue
        for file in root.rglob("*"):
            if file.suffix.lower() not in {".md", ".mcfunction"} or file.name in SKIPPED_NAMES:
                continue
            relative = file.relative_to(root).as_posix()
            if any(part in relative for part in SKIPPED_PARTS):
                continue
            yield prefix + relative, file


def terms(query: str) -> list[str]:
    return [term.lower() for term in query.split() if term.strip()]


def _bigrams(term: str) -> list[str]:
    return [term[i : i + 2] for i in range(len(term) - 1)]


class DocLibrary:
    def __init__(self, roots=None):
        self.roots = roots
        self._signature = None
        self.sections: list[Section] = []

    def _refresh(self):
        files = sorted(_files(self.roots if self.roots is not None else default_roots()))
        signature = tuple((path, file.stat().st_mtime_ns) for path, file in files)
        if signature == self._signature:
            return
        sections, seen = [], set()
        for path, file in files:
            try:
                text = file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for section in split_sections(path, text):
                # human_manual and key_detection share some files; keep the first copy.
                digest = hashlib.sha1(section.text.encode("utf-8")).hexdigest()
                if digest not in seen:
                    seen.add(digest)
                    sections.append(section)
        self.sections, self._signature = sections, signature

    def _score(self, section: Section, query_terms: list[str]) -> float:
        head = (section.path + " " + section.title).lower()
        body = section.text.lower()
        score, matched = 0.0, 0
        for term in query_terms:
            if term in head:
                score, matched = score + 4, matched + 1
            elif term in body:
                score, matched = score + 1 + min(body.count(term), 5) * 0.3, matched + 1
            elif CJK.search(term) and len(term) > 2:
                # Chinese has no spaces: "右键检测方法" should still find "右键检测".
                pieces = _bigrams(term)
                hit = sum(piece in head or piece in body for piece in pieces)
                if hit * 2 >= len(pieces):
                    score, matched = score + hit / len(pieces), matched + 1
        if matched * 2 < len(query_terms) or not matched:
            return 0.0
        return score * matched / len(query_terms) * section.weight

    def search(self, query: str, limit: int = 5) -> list[dict]:
        query_terms = terms(query)
        if not query_terms:
            return []
        self._refresh()
        scored = [(self._score(section, query_terms), section) for section in self.sections]
        scored = sorted((item for item in scored if item[0] > 0), key=lambda item: -item[0])
        results, pages = [], {}
        for score, section in scored:
            # At most two sections from one page, so one long Wiki page cannot fill the list.
            if pages.get(section.path, 0) >= 2:
                continue
            pages[section.path] = pages.get(section.path, 0) + 1
            results.append(
                {
                    "id": f"doc:{section.path}#{section.title}",
                    "label": section.label,
                    "title": section.title,
                    "content": section.text,
                    "sources": [section.path],
                    "score": round(score, 2),
                }
            )
            if len(results) >= limit:
                break
        return results


_library: DocLibrary | None = None


def library() -> DocLibrary:
    global _library
    if _library is None:
        _library = DocLibrary()
    return _library
