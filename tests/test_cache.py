# -*- coding: utf-8 -*-
"""test_cache.py —— mtime 缓存失效：knowledge.load_cards / tactics.load_local。

被测版本快照（详见 tests/README.md）：
  clashlab/overlay/tactics.py mtime 2026-11-24 14:35:09
    sha256 758F854B73F3A8441333DA54A12BD0EE1FCCA1EF36035751F4284FE4EADBA6CC
  clashlab/knowledge.py      mtime 2026-11-24 13:39:31
    sha256 1BF3745AD70FDE02501E24E2DEA61F78061AD5A73B7BD9ECA06B357971AA78BE

规则：同 mtime 命中缓存（同一对象，不重读盘）；改 mtime 后必失效重读（新对象、新内容）。
全部用 tempfile 临时文件造，不改真实 knowledge/tactics 与 out/ 数据。
"""
import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clashlab import knowledge
from clashlab.overlay import tactics


def _bump(path):
    """把 mtime 推到未来几秒，确保与旧 mtime 不相等。"""
    future = time.time() + 60
    os.utime(path, (future, future))


class TestKnowledgeCardCache(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="clashlab_kb_")
        self.card_path = os.path.join(self.dir, "a.json")
        self.card = {
            "id": "t1", "th": 14, "army": ["edrag"],
            "pattern": "edrag_rush", "confidence": 0.8,
            "source": {"title": "雷龙冲本", "site": "test", "url": ""},
            "key_points": ["铺雷龙"],
        }
        with open(self.card_path, "w", encoding="utf-8") as f:
            json.dump(self.card, f, ensure_ascii=False)

    def test_same_mtime_hits_cache_same_object(self):
        first = knowledge.load_cards(self.dir)
        second = knowledge.load_cards(self.dir)
        self.assertIs(first, second, "同 mtime 必须返回缓存的同一对象")
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]["id"], "t1")

    def test_mtime_change_invalidates_cache_and_rereads(self):
        first = knowledge.load_cards(self.dir)
        # 改内容 + 推 mtime（同秒写盘可能 mtime 相等，显式 bump 兜底）
        self.card["id"] = "t2"
        with open(self.card_path, "w", encoding="utf-8") as f:
            json.dump(self.card, f, ensure_ascii=False)
        _bump(self.card_path)

        second = knowledge.load_cards(self.dir)
        self.assertIsNot(first, second, "mtime 变化后必须重读，不能返回旧缓存对象")
        self.assertEqual(second[0]["id"], "t2")
        # 再调一次走新缓存：与第二次同对象
        third = knowledge.load_cards(self.dir)
        self.assertIs(second, third)

    def test_missing_dir_returns_empty(self):
        self.assertEqual(knowledge.load_cards(os.path.join(self.dir, "nope")), [])


class TestLoadLocalCache(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="clashlab_local_")
        os.makedirs(os.path.join(self.root, "out", "prebattle"))
        self.info_path = os.path.join(self.root, "out", "prebattle", "info.json")
        self.info = {
            "th": 14,
            "exposed": [
                {"type": "air-defense", "tile": [15, 30],
                 "dps": 300, "edge_dist": 3},
            ],
            "blind": [], "defense_counts": {},
            "core_cover_dps": None, "centroid": None, "layout_id": "x",
        }
        with open(self.info_path, "w", encoding="utf-8") as f:
            json.dump(self.info, f, ensure_ascii=False)

    def test_same_mtime_hits_cache_same_object(self):
        first = tactics.load_local(self.root, th=14)
        second = tactics.load_local(self.root, th=14)
        self.assertIs(first, second, "同 mtime 必须返回缓存的同一对象")
        self.assertTrue(first["ok"])
        self.assertEqual(first["rows"][0]["name"], "防空塔")
        self.assertEqual(first["rows"][0]["tile"], [15.0, 30.0])
        self.assertEqual(first["rows"][0]["dps"], 300)

    def test_mtime_change_invalidates_cache_and_rereads(self):
        first = tactics.load_local(self.root, th=14)
        self.info["exposed"][0]["dps"] = 999
        with open(self.info_path, "w", encoding="utf-8") as f:
            json.dump(self.info, f, ensure_ascii=False)
        _bump(self.info_path)

        second = tactics.load_local(self.root, th=14)
        self.assertIsNot(first, second, "mtime 变化后必须重读，不能返回旧缓存对象")
        self.assertEqual(second["rows"][0]["dps"], 999)
        third = tactics.load_local(self.root, th=14)
        self.assertIs(second, third)

    def test_missing_source_falls_back_without_raise(self):
        doc = tactics.load_local(os.path.join(self.root, "no_such_root"), th=14)
        self.assertFalse(doc["ok"])
        self.assertEqual(doc["rows"], [])


if __name__ == "__main__":
    unittest.main()
