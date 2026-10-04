"""Bounded, audited model-adjustable settings exclude identity and secrets."""
from __future__ import annotations

import os

BOUNDS = {
    "proactive_min_gap": (30, 3600, 120, "QQBOT_PROACTIVE_MIN_GAP"),
    "proactive_max_per_hour": (0, 30, 6, "QQBOT_PROACTIVE_MAX_PER_HOUR"),
    "active_min_seconds": (300, 1200, 300, "QQBOT_ACTIVE_MIN_SECONDS"),
    "active_max_seconds": (300, 1200, 1200, "QQBOT_ACTIVE_MAX_SECONDS"),
    "judge_threshold": (0, 1, .5, "QQBOT_JUDGE_THRESHOLD"),
    "reply_max_tokens": (16, 4096, 220, "QQBOT_REPLY_MAX_TOKENS"),
    "style_k": (0, 20, 5, "QQBOT_STYLE_REPLY_K"),
    **{f"baseline_{name}": (0, 1, .5, f"QQBOT_BASELINE_{name.upper()}") for name in
       ("excitement", "mood", "interest", "energy", "irritation", "closeness")},
}


class RuntimeSettings:
    def __init__(self, store):
        self.store = store

    def get(self, name):
        low, high, default, env = BOUNDS[name]
        rows = self.store.rows("SELECT value FROM runtime_overrides WHERE name=?", (name,))
        return rows[0]["value"] if rows else max(low, min(high, float(os.environ.get(env, default))))

    def adjust(self, name, value, reason):
        if name not in BOUNDS:
            raise ValueError("参数不在可调整白名单中")
        if not str(reason).strip():
            raise ValueError("调整参数必须说明理由")
        low, high, _, _ = BOUNDS[name]
        import math
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("参数必须是有限数值")
        rows = self.store.rows("SELECT updated FROM runtime_overrides WHERE name=?", (name,))
        now = self.store.clock()
        if rows and now - rows[0]["updated"] < 600:
            raise ValueError("同一参数 10 分钟内只能调整一次")
        clipped = max(low, min(high, number))
        self.store.write("INSERT OR REPLACE INTO runtime_overrides VALUES(?,?,?,?)", (name, clipped, str(reason), now))
        return {"name": name, "value": clipped, "clipped": clipped != number, "reason": reason}
