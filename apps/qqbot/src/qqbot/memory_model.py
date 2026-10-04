"""Cognitive-inspired scores with separate, reversible engineering policies.

Power-law forgetting, spacing, retrieval practice and interference motivate the
score functions. Compression, source merging, thresholds and permanent storage
are engineering policies, not claims about measured human recall probability.
"""
from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher

from .store import dumps


def retrievability(now, last_used, strength, decay):
    if strength <= 0 or decay <= 0:
        raise ValueError("记忆强度和衰减指数必须大于零")
    return (1 + max(0, now - last_used) / strength) ** (-decay)


@dataclass
class MemoryParameters:
    initial_strength: float = 86400
    decay: float = .5
    retrieval_threshold: float = .1
    activation_half_life: float = 3600
    hit_gain: float = .15
    reinforcement_gain: float = 3600
    spacing_scale: float = 86400
    repeat_window: float = 600
    repeat_penalty: float = .5
    interference_rate: float = .05
    compression_activation: float = .2
    compression_min_chars: int = 80
    merge_similarity: float = .9
    merge_max_chars: int = 600
    forgetting_threshold: float = .05
    low_value_threshold: float = .2
    permanent_strength: float = 31536000
    permanent_min_uses: int = 20

    @classmethod
    def configured(cls, store=None, group_id=None):
        defaults = asdict(cls())
        override = store.get_state(f"memory_parameters:{group_id}", {}) if store else {}
        for name, default in defaults.items():
            raw = override.get(name, os.environ.get("QQBOT_MEMORY_" + name.upper(), default))
            defaults[name] = type(default)(raw)
        return cls(**defaults)


class MemoryModel:
    def __init__(self, clock=time.time, parameters=None, decay=None, activation_half_life=None):
        self.clock = clock
        self.params = parameters or MemoryParameters()
        if decay is not None: self.params.decay = decay
        if activation_half_life is not None: self.params.activation_half_life = activation_half_life

    def score(self, state):
        return retrievability(self.clock(), state.get("last_used", state.get("created", self.clock())),
                              state.get("strength", self.params.initial_strength), self.params.decay)

    def decay_activation(self, state):
        elapsed = max(0, self.clock() - state.get("activation_at", self.clock()))
        state["activation"] = state.get("activation", 0) * 2 ** (-elapsed / max(1, self.params.activation_half_life))
        state["activation_at"] = self.clock()
        return state["activation"]

    def activate(self, state, amount=None):
        self.decay_activation(state)
        state["activation"] = min(1, state["activation"] + (self.params.hit_gain if amount is None else amount))
        if self.clock() - state.get("last_hit", -float("inf")) <= self.params.repeat_window:
            state["repeat_hits"] = state.get("repeat_hits", 0) + 1
        else:
            state["repeat_hits"] = 0
        state["last_hit"] = self.clock()
        return state["activation"]

    def reinforce(self, state, quality=1, position=""):
        if not state.get("id") or not str(position).strip():
            raise ValueError("实际使用必须记录记忆 ID 和使用位置")
        now = self.clock()
        last = state.get("last_used", state.get("created", now))
        interval = max(0, now - last)
        score = self.score(state)
        spacing = math.log1p(interval / max(1, self.params.spacing_scale))
        repeats = state.get("repeat_hits", 0) if now - state.get("last_hit", -float("inf")) <= self.params.repeat_window else 0
        penalty = 1 / (1 + self.params.repeat_penalty * repeats)
        gain = self.params.reinforcement_gain * max(0, min(1, quality)) * (.1 + 1 - score) * (1 + spacing) * penalty
        state["strength"] = state.get("strength", self.params.initial_strength) + gain
        state["last_used"] = now
        state.setdefault("evidence", []).append({"memory_id": state["id"], "position": position, "quality": quality, "at": now})
        if state["strength"] >= self.params.permanent_strength and len(state["evidence"]) >= self.params.permanent_min_uses:
            self.make_permanent(state)
        return gain

    def interfere(self, state, amount=1):
        state["strength"] = max(1, state.get("strength", self.params.initial_strength) *
                                (1 - min(.9, self.params.interference_rate * max(0, amount))))

    @staticmethod
    def make_permanent(state):
        # Storage policy does not alter library, authorship or access rights.
        state["permanent"] = True

    def remaining_time(self, state):
        threshold = self.params.forgetting_threshold
        lifetime = state.get("strength", self.params.initial_strength) * (threshold ** (-1 / self.params.decay) - 1)
        return max(0, state.get("last_used", self.clock()) + lifetime - self.clock())

    def merge(self, left, right):
        if left["category"] != right["category"]:
            raise ValueError("不能合并不同类别的记忆")
        remaining = (self.remaining_time(left) + self.remaining_time(right)) / 2
        merged = {**left}
        merged["sources"] = list(dict.fromkeys(left.get("sources", []) + right.get("sources", [])))
        merged["evidence"] = left.get("evidence", []) + right.get("evidence", [])
        merged["content"] = left["content"] if left["content"] == right["content"] else left["content"] + "\n" + right["content"]
        merged["last_used"] = self.clock()
        merged["strength"] = max(1e-9, remaining / (self.params.forgetting_threshold ** (-1 / self.params.decay) - 1))
        merged["permanent"] = left.get("permanent", False) or right.get("permanent", False)
        merged["merged_from"] = list(dict.fromkeys(left.get("merged_from", [left["id"]]) + right.get("merged_from", [right["id"]])))
        merged["merged_remaining_time"] = remaining
        return merged

    def simulate_forgetting(self, states):
        return [state for state in states if state.get("category") != "related" and not state.get("permanent")
                and not state.get("merged_into") and self.score(state) < self.params.forgetting_threshold
                and state.get("value", 0) <= self.params.low_value_threshold]

    def sleep(self, states, compressor=None, similarity=None):
        compressor = compressor or (lambda text: " ".join(text.split()))
        similarity = similarity or (lambda a, b: SequenceMatcher(None, a, b).ratio())
        working = [json.loads(dumps(state)) for state in states]
        actions = []
        for state in working:
            if state.get("category") == "related" or state.get("merged_into"): continue
            self.decay_activation(state)
            if state["activation"] <= self.params.compression_activation and len(state["content"]) >= self.params.compression_min_chars:
                compressed = compressor(state["content"])
                if compressed and len(compressed) < len(state["content"]):
                    state.setdefault("revisions", []).append(state["content"])
                    state["content"] = compressed
                    actions.append({"action": "compress", "id": state["id"]})
                else:
                    state["cannot_compress"] = True
            else:
                state["cannot_compress"] = len(state["content"]) < self.params.compression_min_chars
        for index, left in enumerate(working):
            if left.get("category") == "related" or left.get("merged_into"): continue
            for right in working[index + 1:]:
                if right.get("merged_into") or right["category"] != left["category"] or right.get("author") != left.get("author"): continue
                if max(len(left["content"]), len(right["content"])) > self.params.merge_max_chars: continue
                if similarity(left["content"], right["content"]) >= self.params.merge_similarity:
                    left.update(self.merge(left, right))
                    right["merged_into"] = left["id"]
                    actions.append({"action": "merge", "ids": [left["id"], right["id"]]})
        forgotten = [state for state in self.simulate_forgetting(working) if state.get("cannot_compress", True)]
        actions.extend({"action": "would_forget", "id": state["id"]} for state in forgotten)
        return {"states": working, "actions": actions, "would_forget": [state["id"] for state in forgotten]}


class MemoryService:
    def __init__(self, store):
        self.store = store

    def load(self, group_id):
        result = []
        for row in self.store.rows("SELECT * FROM memory_state WHERE group_id=?", (str(group_id),)):
            state = json.loads(row["state"])
            state.update({key: row[key] for key in ("id", "category", "kind", "author", "content")})
            state["sources"] = json.loads(row["sources"])
            state.setdefault("created", row["updated"])
            state.setdefault("last_used", row["updated"])
            result.append(state)
        return result

    def model(self, group_id):
        return MemoryModel(self.store.clock, MemoryParameters.configured(self.store, group_id))

    def save(self, state):
        self.store.write("UPDATE memory_state SET state=?,content=?,sources=?,updated=? WHERE id=?",
            (dumps(state), state["content"], dumps(state["sources"]), self.store.clock(), state["id"]))

    def activate_candidates(self, group_id, text):
        if not text.strip(): return
        model = self.model(group_id)
        threshold = float(os.environ.get("QQBOT_MEMORY_MATCH_THRESHOLD", ".4"))
        for state in self.load(group_id):
            if state.get("merged_into"): continue
            if SequenceMatcher(None, text, state["content"]).ratio() >= threshold or text in state["content"]:
                model.activate(state)
                self.save(state)

    def record_use(self, group_id, memory_id, position, quality=1, allow_unrelated=False):
        state = next((s for s in self.load(group_id) if s["id"] == memory_id), None)
        if state is None: raise ValueError("当前群中没有该记忆")
        if state["category"] != "related" and not allow_unrelated: raise PermissionError("不能读取无关库")
        gain = self.model(group_id).reinforce(state, quality, position)
        self.save(state)
        return {"memory_id": memory_id, "gain": gain, "position": position}

    def sleep(self, group_id):
        result = self.model(group_id).sleep(self.load(group_id))
        for state in result["states"]:
            self.save(state)
        if os.environ.get("QQBOT_MEMORY_FORGET_ENABLED", "0").lower() in {"1", "true"}:
            for mid in result["would_forget"]:
                rows = self.store.rows("SELECT * FROM memory_state WHERE id=? AND group_id=?", (mid, str(group_id)))
                if rows: self.store.recycle(rows[0])
        self.store.set_state(f"memory_sleep:{group_id}", {"at": self.store.clock(), "actions": result["actions"], "would_forget": result["would_forget"]})
        return result
