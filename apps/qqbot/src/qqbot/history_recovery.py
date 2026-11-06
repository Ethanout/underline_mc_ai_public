"""Backfill available group history without replaying commands or replies."""
import time


def recover_history(store, journal, onebot, groups, max_pages=20):
    if not onebot("get_status", {}).get("online"):
        return
    for group in groups:
        key = "history_recovery:" + str(group)
        previous = store.get_state(key, {})
        cutoff = previous.get("checked_at", 0)
        started = time.time()
        cursor = None
        added = 0
        seen = set()
        complete = False
        try:
            for _ in range(max_pages):
                params = {"group_id": int(group), "count": 100, "reverseOrder": False}
                if cursor is not None:
                    params["message_seq"] = cursor
                data = onebot("get_group_msg_history", params)
                rows = data.get("messages", [])
                if not rows:
                    complete = True
                    break
                fresh = [row for row in rows if str(row.get("message_id")) not in seen]
                if not fresh:
                    break
                for row in sorted(fresh, key=lambda row: row.get("time", 0)):
                    seen.add(str(row.get("message_id")))
                    event = {**row, "post_type": "message", "message_type": "group",
                             "group_id": str(group), "history_recovered": True}
                    added += int(journal.append(event))
                oldest = min(rows, key=lambda row: row.get("time", 0))
                if oldest.get("time", 0) <= cutoff or len(rows) < 100:
                    complete = True
                    break
                cursor = oldest.get("message_seq")
                if cursor is None:
                    break
            store.set_state(key, {"checked_at": started if complete else cutoff,
                                  "attempted_at": started, "added": added,
                                  "complete": complete,
                                  "missing": None if complete else "历史分页不足或接口缺少序号；缺失范围尚未补齐"})
        except Exception as exc:
            store.set_state(key, {**previous, "attempted_at": started,
                                  "error": str(exc), "complete": False})
