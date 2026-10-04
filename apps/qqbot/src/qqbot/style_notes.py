"""Style notes: a short, regularly refreshed description of how a group talks.

The notes sit in the stable part of the reply prompt (they change about once a
day), so they must describe *habits* -- favourite words and memes, sentence
length, punctuation and emoji, how people pick up each other's lines -- not
carry anyone's words or names.  The model is told that, and the result is also
checked here: a note that repeats a long stretch of any source line, or names
a speaker, is thrown away and the cadence-only fallback is kept instead.
Prompts cannot be trusted to keep privacy; the check is what enforces it.

毯毯's own lines are excluded, so the notes learn from the group, not from the
bot copying itself.
"""

from __future__ import annotations

import os
import statistics

from .reply import thinking_fields, token_budget

MAX_SOURCE_LINES = 400
MAX_SOURCE_CHARS = 20000
MAX_NOTE_CHARS = 800
# A shared run this long is treated as a quotation rather than a habit.
QUOTE_RUN = 12

NOTE_PROMPT = (
    "你在帮一只叫毯毯的群聊猫猫整理「这个群平时怎么说话」的笔记。"
    "根据旧笔记和新的群聊记录，输出一份更新后的笔记，600 字以内，纯文本，不用 Markdown。\n"
    "写这些：常用词和口头禅、流行的梗、句子长短、标点和表情习惯、怎么接话和吐槽。\n"
    "不要写：任何人的名字或 QQ 号、原句照抄（超过十个字的原话都不行）、"
    "具体的私事、聊天内容摘要。只写说话习惯，不写聊了什么。\n"
    "旧笔记里还成立的保留，过时的删掉。"
)


def _cadence(rows, texts):
    lengths = [len(text) for text in texts] or [0]
    return (
        f"新增 {len(rows)} 条群友发言。中位句长 {statistics.median(lengths):g} 字。"
        "学说话节奏时保持毯毯的人设。"
    )


def _quotes_source(note, texts):
    """True if ``note`` shares a ``QUOTE_RUN``-character stretch with any line."""
    compact = "".join(note.split())
    for text in texts:
        line = "".join(text.split())
        for start in range(0, len(line) - QUOTE_RUN + 1):
            if line[start : start + QUOTE_RUN] in compact:
                return True
    return False


def _names_speaker(note, rows):
    for row in rows:
        for key in ("nickname", "card", "user_id"):
            value = str(row[key] if key in row.keys() else "").strip()
            if len(value) >= 2 and value in note:
                return True
    return False


def refresh_notes(store, group_id, post=None, model=None):
    """Update the group's notes from messages since the last run.

    ``post`` is the injectable DeepSeek call; without it (or when the result
    fails the privacy check) only aggregate cadence is recorded.
    """
    group = str(group_id)
    previous = store.get_state("style_notes_cursor:" + group, 0)
    rows = [row for row in store.messages(group) if not row["is_bot"] and row["ts"] > previous]
    old = store.get_state("style_notes:" + group, "暂无风格笔记。")
    if not rows:
        return old
    texts = [store.text(row).strip() for row in rows]
    texts = [text for text in texts if text]
    note = _cadence(rows, texts)
    if post is not None and texts:
        store.set_state("style_notes_error:" + group, "")
        sample, size = [], 0
        for text in reversed(texts[-MAX_SOURCE_LINES:]):
            if size + len(text) > MAX_SOURCE_CHARS:
                break
            sample.append(text)
            size += len(text) + 1
        sample.reverse()
        effort = os.environ.get("QQBOT_JUDGE_REASONING_EFFORT", "low")
        payload = {
            "model": model or os.environ.get("QQBOT_JUDGE_MODEL", "deepseek-flash"),
            "max_tokens": token_budget(900, effort),
            "messages": [
                {"role": "system", "content": NOTE_PROMPT},
                # One line per message, no speaker names: the model never sees them.
                {"role": "user", "content": f"旧笔记：\n{old}\n\n新的群聊记录：\n" + "\n".join(sample)},
            ],
            **thinking_fields(effort),
        }
        try:
            data = post(payload)
            candidate = str(data["choices"][0]["message"].get("content") or "").strip()
        except Exception as exc:  # noqa: BLE001 - keep the cadence fallback
            store.set_state("style_notes_error:" + group, type(exc).__name__)
            candidate = ""
        candidate = candidate[:MAX_NOTE_CHARS]
        if candidate and not _quotes_source(candidate, texts) and not _names_speaker(candidate, rows):
            note = candidate + "\n（学的是语气，人设优先：毯毯还是毯毯。）"
        elif candidate:
            store.set_state("style_notes_error:" + group, "笔记引用了原句或名字，已丢弃")
    store.set_state("style_notes:" + group, note)
    store.set_state("style_notes_cursor:" + group, max(row["ts"] for row in rows))
    return note
