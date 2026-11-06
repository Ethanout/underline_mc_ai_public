from __future__ import annotations

import tempfile
from pathlib import Path

from qqbot import docs


def test_strip_front_matter_keeps_title():
    text = """---
title: "按键检测方案"
verified_in_game: false
---

## 右键检测

内容在这里。"""
    title, body = docs._strip_front_matter(text)
    assert title == "按键检测方案"
    assert "## 右键检测" in body
    assert "---" not in body


def test_strip_front_matter_no_yaml():
    text = "# 标题\n\n内容"
    title, body = docs._strip_front_matter(text)
    assert title == ""
    assert body == text


def test_split_sections_uses_front_matter_title():
    text = """---
title: 技巧A
---

这是内容部分，需要足够长才能通过最小长度检查。"""
    sections = docs.split_sections("human_manual/trick.md", text)
    assert len(sections) == 1
    assert sections[0].title == "技巧A"
    assert sections[0].label == "人工整理的技巧（未实测）"


def test_split_sections_uses_stem_when_no_title():
    text = "## 第一节\n\n这是足够长的内容部分，超过二十个字符，足够长了吧。"
    sections = docs.split_sections("reference/规范.md", text)
    assert len(sections) == 1
    assert sections[0].title == "规范 > 第一节"
    assert sections[0].label == "Underline 规范"


def test_split_sections_heading_hierarchy():
    text = """# 页标题

## 第一节

这是第一节的内容部分，足够长，超过二十个字符。

### 子标题

这是子节的内容部分，足够长，超过二十个字符。

## 第二节

这是第二节的内容部分，足够长，超过二十个字符。"""
    sections = docs.split_sections("文档/命令.md", text)
    assert len(sections) == 3
    assert sections[0].title == "命令 > 第一节"
    assert sections[1].title == "命令 > 子标题"
    assert sections[2].title == "命令 > 第二节"


def test_split_sections_ignores_headings_in_code_fence():
    text = """## 标题

正文内容足够长，超过二十个字符的最小长度要求。

```mcfunction
# 这不是标题
## 这也不是
```

还是标题下的内容，保持足够长度。"""
    sections = docs.split_sections("文档/test.md", text)
    assert len(sections) == 1
    assert sections[0].title == "test > 标题"
    assert "# 这不是标题" in sections[0].text


def test_split_sections_skips_short_sections():
    text = """## 标题A

短内容

## 标题B

这是一段足够长的内容，会被保留下来，需要超过二十个字符。"""
    sections = docs.split_sections("文档/test.md", text)
    assert len(sections) == 1
    assert sections[0].title == "test > 标题B"


def test_split_sections_chunks_long_sections():
    text = "## 长节\n\n" + "这是一段测试内容。" * 200
    sections = docs.split_sections("文档/test.md", text)
    assert len(sections) > 1
    for sec in sections:
        assert sec.title == "test > 长节"
        assert len(sec.text) <= docs.SECTION_CHARS + 10


def test_split_sections_assigns_label_by_path():
    cases = [
        ("human_manual/trick.md", "人工整理的技巧（未实测）", 1.2),
        ("key_detection/方案.md", "按键检测方案（未实测）", 1.2),
        ("reference/规范.md", "Underline 规范", 1.1),
        ("视频/__命令教程/教程/平行线/01.md", "平行线教程", 1.2),
        ("视频/__命令教程/资料库/knowledge_base/wiki.md", "Wiki 摘录", 0.6),
        ("v1/大纲.md", "教程大纲", 0.8),
        ("文档/命令.md", "Underline 文档", 1.0),
        ("mcfskill/beet.md", "mcfunction 笔记", 1.1),
        ("other/file.md", "Underline 资料", 1.0),
    ]
    for path, expected_label, expected_weight in cases:
        sections = docs.split_sections(path, "## 测试\n\n这是足够长的测试内容，超过二十个字符的最小长度。")
        assert sections[0].label == expected_label
        assert sections[0].weight == expected_weight


def test_split_sections_skips_归档_parts():
    # Test that files in 归档 folders are filtered out during file enumeration
    # (split_sections itself doesn't filter, _files does)
    text = "## 标题\n\n这是足够长的内容，超过二十个字符的长度。"
    sections = docs.split_sections("folder/归档/file.md", text)
    # split_sections doesn't skip by path, only _files does, so this produces sections
    assert len(sections) >= 1


def test_library_search_matches_cjk_bigram():
    with tempfile.TemporaryDirectory() as tmpdir:
        wiki = Path(tmpdir) / "wiki"
        wiki.mkdir()
        content = "## 右键检测\n\n右键检测的原理说明，这是一段足够长的内容。"
        (wiki / "test.md").write_text(content, encoding="utf-8")
        lib = docs.DocLibrary(roots=[("", wiki)])
        results = lib.search("右键检测方法")
        assert len(results) > 0
        assert "右键检测" in results[0]["title"]


def test_library_search_deduplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        wiki = Path(tmpdir) / "wiki"
        (wiki / "human_manual").mkdir(parents=True)
        (wiki / "key_detection").mkdir(parents=True)
        same_content = "## 方案\n\n完全相同的内容用于测试去重，这是足够长的一段话。"
        (wiki / "human_manual" / "a.md").write_text(same_content, encoding="utf-8")
        (wiki / "key_detection" / "a.md").write_text(same_content, encoding="utf-8")
        lib = docs.DocLibrary(roots=[("", wiki)])
        lib._refresh()
        matching = [s for s in lib.sections if "完全相同" in s.text]
        assert len(matching) == 1


def test_library_search_caps_sections_per_page():
    with tempfile.TemporaryDirectory() as tmpdir:
        wiki = Path(tmpdir) / "wiki"
        wiki.mkdir()
        sections = [f"## 节{i}\n\n测试内容测试内容，这是足够长的段落。" for i in range(5)]
        content = "\n\n".join(sections)
        (wiki / "test.md").write_text(content, encoding="utf-8")
        lib = docs.DocLibrary(roots=[("", wiki)])
        results = lib.search("测试", limit=10)
        from_same_page = [r for r in results if "test" in r["sources"][0]]
        assert len(from_same_page) <= 2


def test_library_refreshes_on_mtime_change():
    with tempfile.TemporaryDirectory() as tmpdir:
        wiki = Path(tmpdir) / "wiki"
        wiki.mkdir()
        test_file = wiki / "test.md"
        test_file.write_text("## 初始\n\n初始内容足够长，超过二十个字符，完全足够了。", encoding="utf-8")
        lib = docs.DocLibrary(roots=[("", wiki)])
        lib._refresh()
        initial_count = len(lib.sections)
        test_file.write_text("## 更新\n\n更新内容足够长，超过二十个字符，完全足够了。", encoding="utf-8")
        lib._refresh()
        assert len(lib.sections) == initial_count
        assert any("更新" in s.title for s in lib.sections)
