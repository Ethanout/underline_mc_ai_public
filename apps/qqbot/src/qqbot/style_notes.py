"""A privacy-preserving placeholder records cadence without storing quotations."""

from __future__ import annotations

import statistics


def refresh_notes(store, group_id):
    previous = store.get_state("style_notes_cursor:" + str(group_id), 0)
    rows = [row for row in store.messages(group_id) if not row["is_bot"] and row["ts"] > previous]
    if not rows:
        return store.get_state("style_notes:" + str(group_id), "暂无风格笔记。")
    lengths = [len(store.text(row)) for row in rows]
    # TODO(人工调): use a tuned style-note model prompt after evaluating privacy.
    # Only aggregate cadence metrics enter the static prefix, not names or quotes.
    note = f"新增 {len(rows)} 条群友发言。中位句长 {statistics.median(lengths):g} 字。学说话节奏时保持毯毯的人设。"
    store.set_state("style_notes:" + str(group_id), note)
    store.set_state("style_notes_cursor:" + str(group_id), max(row["ts"] for row in rows))
    return note
