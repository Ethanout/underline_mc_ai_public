"""Simulated clock tests separate activation, reinforcement and storage policy."""
from __future__ import annotations
import json
import os
import unittest
from unittest.mock import patch
from workspace_bootstrap import add_workspace_packages
add_workspace_packages()
from qqbot.memory_model import MemoryModel, MemoryParameters, MemoryService, retrievability
from qqbot.store import Store, dumps


def state(mid="1", **values):
    return {"id": mid, "category": "unrelated", "content": "偏好", "sources": [mid],
            "author": "admin", "strength": 100, "last_used": 0, "activation": 0, **values}


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.now = [100.0]
        self.model = MemoryModel(lambda: self.now[0], MemoryParameters(initial_strength=100, forgetting_threshold=.5))

    def test_power_law_activation_and_half_life(self):
        self.assertAlmostEqual(retrievability(100, 0, 100, .5), 2 ** -.5)
        item = state()
        self.model.activate(item)
        self.assertEqual(item["strength"], 100)
        initial = item["activation"]
        self.now[0] += self.model.params.activation_half_life
        self.assertAlmostEqual(self.model.decay_activation(item), initial / 2)

    def test_usage_spacing_repeat_penalty_and_evidence(self):
        short, long = state(), state("2")
        short_gain = self.model.reinforce(short, position="task:reply:0")
        self.now[0] = 1000
        long_gain = self.model.reinforce(long, position="task:reply:1")
        self.assertGreater(long_gain, short_gain)
        self.assertEqual(long["evidence"][0]["memory_id"], "2")
        a, b = state(), state("2")
        for _ in range(10): self.model.activate(b)
        self.assertLess(self.model.reinforce(b, position="b"), self.model.reinforce(a, position="a"))
        self.assertGreater(a["strength"], 100)
        with self.assertRaises(ValueError): self.model.reinforce(a)

    def test_merge_mean_remaining_sources_and_permanence(self):
        left, right = state(), state("2", strength=200)
        mean = (self.model.remaining_time(left) + self.model.remaining_time(right)) / 2
        merged = self.model.merge(left, right)
        self.assertAlmostEqual(self.model.remaining_time(merged), mean)
        self.assertEqual(merged["sources"], ["1", "2"])
        self.model.make_permanent(merged)
        self.assertEqual(merged["category"], "unrelated")
        self.assertEqual(self.model.simulate_forgetting([merged]), [])

    def test_sleep_order_compression_merge_and_simulation(self):
        self.now[0] = 1_000_000
        a = state(content="很长  " * 30)
        b = state("2", content="很长  " * 30)
        c = state("3", content="另一件事")
        result = self.model.sleep([a, b, c])
        actions = [action["action"] for action in result["actions"]]
        self.assertIn("compress", actions)
        self.assertIn("merge", actions)
        self.assertIn("would_forget", actions)
        self.assertLess(actions.index("compress"), actions.index("merge"))
        self.assertLess(actions.index("merge"), actions.index("would_forget"))
        self.assertEqual(len(result["states"]), 3)
        self.assertEqual(a["content"], "很长  " * 30)

    def test_service_no_delete_and_opt_in_recycle(self):
        store = Store(":memory:", clock=lambda: 10_000_000)
        item = state()
        store.write("INSERT INTO memory_state VALUES(?,?,?,?,?,?,?,?,?)", ("1", "g", "unrelated", "note", "admin", "偏好", dumps(["source"]), dumps(item), 0))
        service = MemoryService(store)
        with patch.dict(os.environ, {"QQBOT_MEMORY_FORGET_ENABLED": "0"}):
            service.sleep("g")
            self.assertEqual(len(store.rows("SELECT * FROM memory_state")), 1)
            self.assertEqual(store.rows("SELECT * FROM recycle_bin"), [])
            with self.assertRaises(PermissionError): service.record_use("g", "1", "reply")
        with patch.dict(os.environ, {"QQBOT_MEMORY_FORGET_ENABLED": "1"}):
            service.sleep("g")
            self.assertEqual(len(store.rows("SELECT * FROM recycle_bin")), 1)
            store.restore("1")
            self.assertEqual(service.load("g")[0]["category"], "unrelated")
        store.close()
