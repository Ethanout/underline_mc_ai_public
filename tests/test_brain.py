"""Offline tests with a simulated clock, RNG and judge."""
from __future__ import annotations
import unittest
from workspace_bootstrap import add_workspace_packages
add_workspace_packages()
from qqbot.brain import Brain, BrainParameters, TurnCoordinator, parse_judgment
from qqbot.store import Store


def decision(**values):
    return {"speak": True, "finished": True, "wait_seconds": 2, "why": "能接话", "reply_to": None,
            "emotion_delta": {}, "stay": "keep", **values}


class FixedRandom:
    def random(self): return 0
    def uniform(self, low, high): return low


class BrainTests(unittest.TestCase):
    def setUp(self):
        self.now = [1_000_000.]
        self.params = BrainParameters(proactive_groups=("g",))
        self.brain = Brain(group_id="g", clock=lambda: self.now[0], rng=FixedRandom(), parameters=self.params)

    def advance(self, seconds): self.now[0] += seconds

    def test_profile_decay_emotion_recovery_mention_and_rebuild(self):
        self.brain.event(mentioned=True, question_count=10)
        self.assertGreater(self.brain.active_until, self.now[0])
        self.assertEqual(self.brain.profile[self.brain.slot(self.now[0])], 3)
        tired = self.brain.emotions["精力"]
        self.advance(self.params.emotion_half_life)
        self.brain.decay()
        self.assertGreater(self.brain.emotions["精力"], tired)
        count = sum(self.brain.profile)
        self.advance(self.params.profile_half_life)
        self.brain.decay()
        self.assertAlmostEqual(sum(self.brain.profile), count / 2)
        store = Store(":memory:")
        store.append({"post_type": "message", "message_type": "group", "group_id": "g", "message_id": "1",
            "user_id": "a", "self_id": "bot", "time": self.now[0], "message": [{"type": "at", "data": {"qq": "bot"}}]})
        self.brain.rebuild_profile(store.messages("g"))
        self.assertEqual(sum(self.brain.profile), 3)
        store.close()

    def test_two_debounce_paths(self):
        self.brain.event()
        self.assertFalse(self.brain.judgment_due())
        self.advance(8)
        self.assertTrue(self.brain.judgment_due())
        self.brain.pending = []
        for _ in range(5): self.brain.event(); self.advance(1)
        self.assertTrue(self.brain.judgment_due())

    def test_wait_limit_bad_json_and_delta_clipping(self):
        calls = []
        def judge(transcript, mentioned):
            calls.append(transcript)
            return decision(finished=False, wait_seconds=7, emotion_delta={"兴趣": 9, "烦躁": -9})
        turn = TurnCoordinator(self.brain, judge, self.advance)
        started = self.now[0]
        result = turn.wait_for_finished(lambda: "转录", True)
        self.assertEqual(self.now[0] - started, 20)
        self.assertFalse(result["finished"])
        self.assertEqual(result["emotion_delta"], {"兴趣": .2, "烦躁": -.2})
        for raw in ("bad", {}, {"speak": True}, decision(wait_seconds="NaN")):
            self.assertFalse(parse_judgment(raw)["speak"])
        self.assertTrue(0 <= self.brain.emotions["兴趣"] <= 1)

    def test_regenerate_once_and_drop_proactive_on_new_messages(self):
        turn = TurnCoordinator(self.brain, lambda *a: decision(), self.advance)
        generated, sent = [], []
        def generate(transcript, regenerate):
            generated.append(regenerate)
            self.brain.event()
            return "新回复" if regenerate else "旧回复"
        result = turn.respond(lambda: "转录", generate, lambda text, target: sent.append(text), mentioned=True)
        self.assertTrue(result["regenerated"])
        self.assertEqual(generated, [False, True])
        self.assertEqual(sent, ["新回复"])
        result = turn.respond(lambda: "转录", generate, lambda *args: self.fail("主动回复应放弃"))
        self.assertFalse(result["sent"])

    def test_whitelist_gap_hourly_and_persistence(self):
        self.brain.params.proactive_groups = ()
        self.assertFalse(self.brain.can_proactively_speak())
        self.brain.params.proactive_groups = ("g",)
        self.assertTrue(self.brain.can_proactively_speak())
        self.brain.mark_sent()
        self.assertFalse(self.brain.can_proactively_speak())
        self.advance(300)
        self.brain.sent_times = [self.now[0] - 300] * 6
        self.assertFalse(self.brain.can_proactively_speak())
        self.brain.sent_times = []
        self.assertTrue(.5 <= self.brain.gap_scale() <= 2)
        store = Store(":memory:")
        brain = Brain(store, "g", lambda: self.now[0], FixedRandom())
        brain.event(mentioned=True)
        reopened = Brain(store, "g", lambda: self.now[0], FixedRandom())
        self.assertEqual(reopened.emotions, brain.emotions)
        self.assertEqual(reopened.profile, brain.profile)
        store.close()

    def test_pickup_probability_is_injectable(self):
        self.brain.probability_fn = lambda *args: 1
        self.assertTrue(self.brain.should_pick_up())
        self.brain.tick()
        self.assertTrue(300 <= self.brain.active_until - self.now[0] <= 1200)
