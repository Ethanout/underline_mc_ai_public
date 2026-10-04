"""Persist deterministic rhythm and emotion policies around injectable judges."""

from __future__ import annotations

import json
import math
import os
import random
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .reply import thinking_fields, token_budget

EMOTIONS = ("兴奋", "心情", "兴趣", "精力", "烦躁", "亲近")
BASELINE_NAMES = dict(
    zip(EMOTIONS, ("excitement", "mood", "interest", "energy", "irritation", "closeness"))
)
LOCAL_TIME = timezone(timedelta(hours=8))


def clip(value, low=0, high=1):
    return min(high, max(low, value))


@dataclass
class BrainParameters:
    profile_half_life: float = 30 * 86400
    emotion_half_life: float = 1800
    mention_weight: float = 3
    pickup_scale: float = 0.01
    active_min: float = 300
    active_max: float = 1200
    debounce_seconds: float = 8
    debounce_count: int = 5
    wait_limit: float = 20
    proactive_min_gap: float = 120
    proactive_max_per_hour: int = 6
    proactive_groups: tuple = ()
    judge_threshold: float = 0.5


JUDGE_PROMPT = """你是毯毯（群里的一只白猫，管数据库）的「要不要开口」判断器。你只做判断，不写回复。
输入是本群最近的聊天记录，每行有时间、消息 id、说话人；>> 标着这次需要关注的那条。

先判断说话的人说完没有：
- 同一个人几秒内连发、最后一句像没说完（半句话、刚说"等下""我发个图""还有"），finished=false，wait_seconds 给 3 到 15。
- 别人之间正在快速一来一回，也先等等。
- 说完了 finished=true，wait_seconds=0。

再判断要不要说（speak）：
- 被 @ 了，并且对方说完了：speak=true。
- 没被 @：只有能真的加点东西才说，比如知道答案而还没人答对、有不同看法、能接住一个梗、话题正好是毯毯熟的（数据包、MC、编程、伊桑）。
- 这些情况不说：只能附和"对""确实"；已经有人答对了；两个人在私聊式对话；话题和毯毯无关又接不上；刚说过话、再说就刷屏了。
- 拿不准就不说。

reply_to：要接的那条消息 id，没有就 null。
emotion_delta：这段聊天让毯毯的情绪怎么变，键只能用 兴奋、心情、兴趣、精力、烦躁、亲近，每个值在 -0.2 到 0.2，没变化就给 {}。被夸心情升，被连着考烦躁升，聊到喜欢的话题兴趣升。
stay：还想继续看群就 extend，无所谓 keep，想放下手机 leave。
why：一句中文说明理由。

只输出一个 JSON 对象，例如：
{"speak": false, "finished": true, "wait_seconds": 0, "why": "已经有人答对了", "reply_to": null, "emotion_delta": {"兴趣": 0.05}, "stay": "keep"}"""


def parse_judgment(raw):
    fallback = {
        "speak": False,
        "finished": True,
        "wait_seconds": 0,
        "why": "判断结果格式无效",
        "reply_to": None,
        "emotion_delta": {},
        "stay": "keep",
        "valid": False,
    }
    try:
        result = json.loads(raw) if isinstance(raw, str) else raw
        fields = {"speak", "finished", "wait_seconds", "why", "reply_to", "emotion_delta", "stay"}
        if not isinstance(result, dict) or not fields <= result.keys():
            return fallback
        if type(result["speak"]) is not bool or type(result["finished"]) is not bool:
            return fallback
        if not isinstance(result["why"], str) or not isinstance(result["emotion_delta"], dict):
            return fallback
        if result["reply_to"] is not None and not isinstance(result["reply_to"], (str, int)):
            return fallback
        if result["stay"] not in {"extend", "keep", "leave"}:
            return fallback
        wait = float(result["wait_seconds"])
        if not math.isfinite(wait):
            return fallback
        delta = {
            key: clip(float(value), -0.2, 0.2)
            for key, value in result["emotion_delta"].items()
            if key in EMOTIONS
        }
        if not all(math.isfinite(float(value)) for value in result["emotion_delta"].values()):
            return fallback
        return {**result, "wait_seconds": clip(wait, 0, 20), "emotion_delta": delta, "valid": True}
    except (ValueError, TypeError, OverflowError):
        return fallback


class Brain:
    def __init__(
        self,
        store=None,
        group_id="",
        clock=time.time,
        rng=None,
        baselines=None,
        parameters=None,
        probability_fn=None,
    ):
        self.store, self.group_id, self.clock = store, str(group_id), clock
        self.rng = rng or random.Random()
        self.params = parameters or BrainParameters()
        self.probability_fn = probability_fn or (
            lambda activity, rate, energy: (
                1 - math.exp(-self.params.pickup_scale * activity * rate * energy)
            )
        )
        self.baselines = baselines or {name: 0.5 for name in EMOTIONS}
        saved = store.get_state("brain:" + self.group_id, {}) if store else {}
        self.emotions = saved.get("emotions", dict(self.baselines))
        self.profile = saved.get("profile", [0.0] * 168)
        self.last_update = saved.get("last_update", self.clock())
        self.active_until = saved.get("active_until", 0)
        self.pending = saved.get("pending", [])
        self.last_message = saved.get("last_message", 0)
        self.recent_times = saved.get("recent_times", [])
        self.sent_times = saved.get("sent_times", [])
        self.version = saved.get("version", 0)
        self.last_judgment = saved.get("last_judgment", {})
        self.lock = threading.RLock()

    @staticmethod
    def slot(timestamp):
        local = datetime.fromtimestamp(timestamp, LOCAL_TIME)
        return local.weekday() * 24 + local.hour

    def save(self):
        if self.store:
            self.store.set_state(
                "brain:" + self.group_id,
                {
                    key: getattr(self, key)
                    for key in (
                        "emotions",
                        "profile",
                        "last_update",
                        "active_until",
                        "pending",
                        "last_message",
                        "recent_times",
                        "sent_times",
                        "version",
                        "last_judgment",
                    )
                },
            )
            history = self.store.get_state("brain_history:" + self.group_id, [])
            entry = {"at": self.clock(), "emotions": dict(self.emotions)}
            if not history or history[-1] != entry:
                self.store.set_state("brain_history:" + self.group_id, (history + [entry])[-1000:])

    def decay(self):
        now = self.clock()
        elapsed = max(0, now - self.last_update)
        profile_factor = 2 ** (-elapsed / max(1, self.params.profile_half_life))
        self.profile = [value * profile_factor for value in self.profile]
        emotion_factor = 2 ** (-elapsed / max(1, self.params.emotion_half_life))
        for name in EMOTIONS:
            baseline = self.baselines[name]
            self.emotions[name] = clip(baseline + (self.emotions[name] - baseline) * emotion_factor)
        self.last_update = now

    def event(self, mentioned=False, question_count=0, praised=False, timestamp=None):
        with self.lock:
            self.decay()
            now = self.clock()
            timestamp = now if timestamp is None else timestamp
            self.profile[self.slot(timestamp)] += self.params.mention_weight if mentioned else 1
            self.emotions["兴趣"] = clip(self.emotions["兴趣"] + (0.12 if mentioned else 0))
            self.emotions["心情"] = clip(self.emotions["心情"] + (0.08 if praised else 0))
            self.emotions["精力"] = clip(
                self.emotions["精力"] - min(0.2, max(0, question_count) * 0.02)
            )
            self.pending.append(now)
            self.recent_times = [t for t in self.recent_times if now - t <= 60] + [now]
            self.last_message = now
            self.version += 1
            if mentioned:
                self.pick_up()
            self.save()

    def rebuild_profile(self, messages):
        now = self.clock()
        self.profile = [0.0] * 168
        for row in messages:
            raw = json.loads(row["raw"])
            mentioned = any(
                s.get("type") == "at"
                and str(s.get("data", {}).get("qq")) == str(raw.get("self_id"))
                for s in json.loads(row["segments"])
            )
            weight = self.params.mention_weight if mentioned else 1
            self.profile[self.slot(row["ts"])] += weight * 2 ** (
                -max(0, now - row["ts"]) / self.params.profile_half_life
            )
        self.last_update = now
        self.save()

    def pick_up(self):
        duration = self.rng.uniform(self.params.active_min, self.params.active_max)
        mood_scale = 0.75 + 0.25 * self.emotions["心情"] + 0.5 * self.emotions["精力"]
        duration = clip(duration * mood_scale, self.params.active_min, self.params.active_max)
        self.active_until = max(self.active_until, self.clock() + duration)

    def should_pick_up(self):
        self.decay()
        recent_rate = len([t for t in self.recent_times if self.clock() - t <= 60]) / 60
        probability = clip(
            self.probability_fn(
                self.profile[self.slot(self.clock())], recent_rate, self.emotions["精力"]
            )
        )
        return self.rng.random() < probability

    def tick(self):
        with self.lock:
            self.decay()
            if self.clock() >= self.active_until and self.should_pick_up():
                self.pick_up()
            self.save()
            return self.clock() < self.active_until

    def judgment_due(self):
        if not self.pending:
            return False
        now = self.clock()
        quiet = now - self.pending[-1] >= self.params.debounce_seconds
        burst = (
            len([t for t in self.pending if now - t <= self.params.debounce_seconds])
            >= self.params.debounce_count
        )
        return quiet or burst

    def apply_judgment(self, decision):
        self.decay()
        for key, value in decision["emotion_delta"].items():
            self.emotions[key] = clip(self.emotions[key] + clip(value, -0.2, 0.2))
        if decision["stay"] == "extend":
            self.active_until = max(self.active_until, self.clock()) + 300
        if decision["stay"] == "leave":
            self.active_until = self.clock()
        self.last_judgment = {**decision, "at": self.clock()}
        self.save()

    def tendency(self):
        return clip(
            (
                self.emotions["兴奋"]
                + self.emotions["兴趣"]
                + self.emotions["精力"]
                + 1
                - self.emotions["烦躁"]
            )
            / 4
        )

    def gap_scale(self):
        return clip(2 - 1.5 * self.tendency(), 0.5, 2)

    def can_proactively_speak(self):
        if self.group_id not in self.params.proactive_groups:
            return False
        if self.tendency() < self.params.judge_threshold:
            return False
        now = self.clock()
        self.sent_times = [t for t in self.sent_times if now - t < 3600]
        if len(self.sent_times) >= self.params.proactive_max_per_hour:
            return False
        if (
            self.sent_times
            and now - self.sent_times[-1] < self.params.proactive_min_gap * self.gap_scale()
        ):
            return False
        return True

    def mark_sent(self, mentioned=False):
        if not mentioned:
            self.sent_times.append(self.clock())
        self.save()

    def prompt_suffix(self):
        self.decay()
        return " ".join(f"{key}{value:.2f}" for key, value in self.emotions.items())


class TurnCoordinator:
    def __init__(self, brain, judge, sleeper=time.sleep):
        self.brain, self.judge, self.sleep = brain, judge, sleeper

    def wait_for_finished(self, transcript, mentioned):
        started = self.brain.clock()
        decision = parse_judgment(self.judge(transcript(), mentioned))
        self.brain.apply_judgment(decision)
        while decision["valid"] and not decision["finished"]:
            remaining = self.brain.params.wait_limit - (self.brain.clock() - started)
            if remaining <= 0:
                break
            self.sleep(min(remaining, max(0.1, decision["wait_seconds"])))
            decision = parse_judgment(self.judge(transcript(), mentioned))
            self.brain.apply_judgment(decision)
        return decision

    def respond(self, transcript, generate, send, mentioned=False):
        with self.brain.lock:
            if not mentioned and not self.brain.can_proactively_speak():
                return {"sent": False, "why": "白名单或限速"}
        decision = self.wait_for_finished(transcript, mentioned)
        if not decision["speak"]:
            with self.brain.lock:
                self.brain.pending = [
                    t for t in self.brain.pending if t > self.brain.last_judgment["at"]
                ]
                self.brain.save()
            return {"sent": False, "why": decision["why"]}
        version = self.brain.version
        answer = generate(transcript(), False)
        regenerated = False
        if self.brain.version != version:
            if not mentioned:
                return {"sent": False, "why": "生成期间有新消息"}
            answer = generate(transcript(), True)
            regenerated = True
        with self.brain.lock:
            if not mentioned and (
                self.brain.version != version or not self.brain.can_proactively_speak()
            ):
                return {"sent": False, "why": "发送前有新消息或达到限速"}
            send(answer, decision.get("reply_to"))
            self.brain.mark_sent(mentioned)
            self.brain.pending = []
            self.brain.save()
        return {"sent": True, "regenerated": regenerated}


def model_judge(post, model=None, effort=None, audit=None, capabilities=None):
    def judge(transcript, mentioned):
        selected = model or os.environ.get("QQBOT_JUDGE_MODEL", "deepseek-flash")
        thinking = effort or os.environ.get("QQBOT_JUDGE_REASONING_EFFORT", "low")
        if thinking != "none" and capabilities is not None and not capabilities.get("thinking"):
            raise RuntimeError("判断模型不支持思考参数")
        # First draft from the plan's criteria; check real decisions in
        # /api/audit (judge rows carry "why") before tightening it.
        instruction = JUDGE_PROMPT
        payload = {
            "model": selected,
            "max_tokens": token_budget(300, thinking),
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": transcript + f"\n本次被@：{mentioned}"},
            ],
            **thinking_fields(thinking),
        }
        message = post(payload)["choices"][0]["message"]
        if audit:
            audit({"reasoning_length": len(message.get("reasoning_content") or "")})
        return message.get("content", "")

    return judge
