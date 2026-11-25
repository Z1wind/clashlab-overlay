# -*- coding: utf-8 -*-
"""P3b-3 战术输出接线测试：risks 与 LLM 消息里都要出现「布局弱点」。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FS = [{"key": "town-hall-protection", "severity": "weak",
       "text": "大本营偏北侧（中心度 0.42）→ 从他侧切入可少破一层墙。", "detail": {}},
      {"key": "air-coverage", "severity": "critical",
       "text": "对空覆盖 0% → 空军路线全开。", "detail": {}}]


class TestTacticalWiring(unittest.TestCase):
    def test_risks_includes_findings(self):
        from clashlab import prebattle
        info = {"defense_counts": {"air-defense": 1}, "enemy_cc": 40,
                "enemy_hero_levels": {"queen": None, "king": None, "warden": None, "rc": None},
                "defense_findings": FS, "unknown": []}
        rs = prebattle.risks(info)
        self.assertTrue(any("布局弱点" in r for r in rs), rs)
        self.assertTrue(any("大本营" in r or "对空" in r for r in rs), rs)

    def test_prompt_block_renders(self):
        from clashlab.defense_findings import prompt_block
        block = prompt_block({"defense_findings": FS})
        self.assertIn("布局弱点", block)
        self.assertIn("大本营", block)
        self.assertIn("对空", block)
        self.assertEqual(prompt_block({"defense_findings": []}), "")

    def test_marks_messages_contain_findings(self):
        from clashlab import prompts
        msgs, _st = prompts.build_marks_messages("简报", {"draw_calls": []}, style="terse",
                                                cards=None, prebattle={"defense_findings": FS})
        joined = "\n".join(m["content"] for m in msgs)
        self.assertIn("布局弱点", joined)
        self.assertIn("大本营", joined)


if __name__ == "__main__":
    unittest.main()
