# -*- coding: utf-8 -*-
"""test_plan_atomic.py —— plan.json 原子性：读取方永远拿到完整 JSON 或旧版，不抛解析异常。

被测版本快照（详见 tests/README.md）：
  clashlab/overlay/tactics.py  mtime 2026-11-24 14:35:09
    sha256 758F854B73F3A8441333DA54A12BD0EE1FCCA1EF36035751F4284FE4EADBA6CC

场景全在 tempfile 临时目录里造，绝不碰真实 out/overlay/tactics/plan.json：
  1) 写一半中间态：.tmp 残骸留在同目录、目标文件仍是旧完整版 -> load_plan 拿旧完整版；
  2) _atomic_write_json 成功路径：目标完整、.tmp 被替换走、load_plan 拿到新版；
  3) 目标文件已损坏（半截 JSON）：load_plan 降级空结构，不抛解析异常。
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clashlab.overlay import tactics


def _plan_dir(root):
    return os.path.join(tactics._abs(root, tactics.OUT_DIR), tactics.PLAN_JSON)


class TestPlanAtomic(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="clashlab_atomic_")
        self.plan_path = _plan_dir(self.root)
        os.makedirs(os.path.dirname(self.plan_path), exist_ok=True)

    def test_leftover_tmp_does_not_corrupt_old_complete_file(self):
        """写一半中间态：旧完整 plan.json 在位，同目录留半截 .tmp 残骸。
        读取方只认目标文件，拿到旧完整 JSON，.tmp 被忽略，不抛异常。"""
        old_payload = {
            "ok": True, "goal": "三星", "model": "本地规则",
            "elapsed": 1.23, "created_at": "2026-11-24T10:00:00",
            "text": "OLD COMPLETE TEXT", "marks": {"threats": [], "route": []},
            "reason": "",
        }
        tactics._atomic_write_json(self.plan_path, old_payload)
        # 模拟写一半崩溃：.tmp 是半截 JSON，目标仍是旧完整版
        with open(self.plan_path + ".tmp", "w", encoding="utf-8") as f:
            f.write('{ "ok": true, "text": "half-written, broken')

        doc = tactics.load_plan(self.root)
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["text"], "OLD COMPLETE TEXT")
        self.assertEqual(doc["goal"], "三星")

        # 目标文件本身仍是可完整解析的旧版（读取方重读磁盘也不炸）
        with open(self.plan_path, "r", encoding="utf-8") as f:
            on_disk = json.load(f)
        self.assertEqual(on_disk["text"], "OLD COMPLETE TEXT")
        # .tmp 残骸仍在（读取方不负责清理，也不受它影响）
        self.assertTrue(os.path.exists(self.plan_path + ".tmp"))

    def test_atomic_write_success_replaces_completely(self):
        """成功路径：先写 .tmp（flush+fsync）再 os.replace，目标完整、.tmp 不留残骸。"""
        tactics._atomic_write_json(
            self.plan_path,
            {"ok": True, "text": "FIRST", "goal": "三星"})
        tactics._atomic_write_json(
            self.plan_path,
            {"ok": True, "text": "SECOND", "goal": "两星"})

        self.assertFalse(os.path.exists(self.plan_path + ".tmp"))
        doc = tactics.load_plan(self.root)
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["text"], "SECOND")
        self.assertEqual(doc["goal"], "两星")
        with open(self.plan_path, "r", encoding="utf-8") as f:
            on_disk = json.load(f)
        self.assertEqual(on_disk["text"], "SECOND")

    def test_corrupted_target_falls_back_without_raise(self):
        """目标文件已是损坏半截 JSON：load_plan 降级 ok=False 空结构，绝不抛解析异常。"""
        with open(self.plan_path, "w", encoding="utf-8") as f:
            f.write('{ "ok": true, "text": "broken, missing closing brace')
        # 不抛异常是第一断言点
        doc = tactics.load_plan(self.root)
        self.assertFalse(doc["ok"])
        self.assertEqual(doc["text"], "")
        self.assertEqual(doc["model"], "")
        self.assertEqual(doc["elapsed"], 0.0)

    def test_missing_file_falls_back_without_raise(self):
        """目标文件不存在：load_plan 降级空结构，不抛 FileNotFoundError。"""
        doc = tactics.load_plan(self.root)
        self.assertFalse(doc["ok"])
        self.assertEqual(doc["text"], "")

    def test_save_fallback_plan_roundtrip(self):
        """_save_fallback_plan 走同一条原子写；落盘后 load_plan 读回完整兜底 payload。"""
        payload = {
            "ok": False, "fallback": True, "goal": "三星",
            "model": "本地规则", "elapsed": 0.8,
            "created_at": "2026-11-24T10:00:00",
            "text": "【威胁排序】鹰炮 格(36,9)。\n【进攻路线】防空塔 格(15,30)。\n【兵种与法术】x。",
            "marks": {"threats": [{"label": "鹰炮", "tile": [36, 9], "rank": 1}],
                      "route": [{"label": "防空塔", "tile": [15, 30], "seq": 1}]},
            "reason": "simulated upstream failure",
        }
        tactics._save_fallback_plan(self.root, payload)
        doc = tactics.load_plan(self.root)
        # 兜底 payload 设计上 ok=False / fallback=True（见 start_plan 降级分支），
        # load_plan 只要求 dict 且带 text 即原样返回，不把 ok 改成 True。
        self.assertTrue(doc.get("text"), "兜底 payload 的 text 必须被读回")
        self.assertEqual(doc["fallback"], True)
        self.assertEqual(doc["text"], payload["text"])
        self.assertEqual(doc["marks"]["threats"][0]["tile"], [36, 9])


if __name__ == "__main__":
    unittest.main()
