# -*- coding: utf-8 -*-
"""test_tactics_parse.py —— tactics.parse_plan_marks 正/负用例。

被测版本快照（详见 tests/README.md，他人改文件后需重录）：
  clashlab/overlay/tactics.py  mtime 2026-11-24 14:35:09
    sha256 758F854B73F3A8441333DA54A12BD0EE1FCCA1EF36035751F4284FE4EADBA6CC
  clashlab/knowledge.py       mtime 2026-11-24 13:39:31
    sha256 1BF3745AD70FDE02501E24E2DEA61F78061AD5A73B7BD9ECA06B357971AA78BE

纯离线：只调 parse_plan_marks / 段辅助，不读盘、不联网、不起覆盖层。
每个用例都断言「解析结果的字段值」，不只断言没抛异常。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clashlab.overlay import tactics


def _threat_text(threat_line, route_line="按 dps 降序清边后拆除：防空塔 格(15,30)。"):
    return (
        f"【威胁排序】{threat_line}。\n"
        f"【进攻路线】{route_line}\n"
        f"【兵种与法术】本地规则建议：先清边铺主力，具体配比待联网模型复核。\n"
    )


class TestParsePlanMarksPositive(unittest.TestCase):
    """必须过：全角括号/逗号、tile(36,9) 无「格」字、裸鹰炮(0,9)、小数格(36.0,9.0)。"""

    def test_fullwidth_paren_and_comma(self):
        """全角括号（）+ 全角逗号，威胁点与路线点都要落到正确格。"""
        text = _threat_text("鹰炮格（36，9）", "防空塔 格（15，30）")
        out = tactics.parse_plan_marks({"text": text})
        self.assertEqual(len(out["threats"]), 1)
        t = out["threats"][0]
        self.assertEqual(t["label"], "鹰炮")
        self.assertEqual(t["tile"], [36, 9])
        self.assertEqual(t["rank"], 1)
        self.assertEqual(len(out["route"]), 1)
        r = out["route"][0]
        self.assertEqual(r["label"], "防空塔")
        self.assertEqual(r["tile"], [15, 30])
        self.assertEqual(r["seq"], 1)

    def test_tile_english_paren_without_ge_char(self):
        """`tile(36,9)`：无「格」字、英文括号/逗号，标签仍由回找窗命中。"""
        text = _threat_text("鹰炮 tile(36,9)")
        out = tactics.parse_plan_marks({"text": text})
        self.assertEqual(len(out["threats"]), 1)
        t = out["threats"][0]
        self.assertEqual(t["label"], "鹰炮")
        self.assertEqual(t["tile"], [36, 9])
        self.assertEqual(t["rank"], 1)

    def test_bare_label_directly_before_paren(self):
        """裸 `鹰炮(0,9)`：标签紧贴半角括号，无格字无空格。"""
        text = _threat_text("鹰炮(0,9)")
        out = tactics.parse_plan_marks({"text": text})
        self.assertEqual(len(out["threats"]), 1)
        t = out["threats"][0]
        self.assertEqual(t["label"], "鹰炮")
        self.assertEqual(t["tile"], [0, 9])
        self.assertEqual(t["rank"], 1)

    def test_decimal_tile_rounded_to_int(self):
        """小数 `格(36.0,9.0)`：捕获浮点后 round 成整数格号。"""
        text = _threat_text("大本营 格(36.0,9.0)")
        out = tactics.parse_plan_marks({"text": text})
        self.assertEqual(len(out["threats"]), 1)
        t = out["threats"][0]
        self.assertEqual(t["label"], "大本营")
        self.assertEqual(t["tile"], [36, 9])
        self.assertIsInstance(t["tile"][0], int)
        self.assertIsInstance(t["tile"][1], int)

    def test_plain_string_input_accepted(self):
        """plan 也允许直接传文本字符串（非 dict），同样解析。"""
        text = _threat_text("鹰炮 格(36,9)")
        out = tactics.parse_plan_marks(text)
        self.assertEqual(len(out["threats"]), 1)
        self.assertEqual(out["threats"][0]["tile"], [36, 9])

    def test_rank_and_seq_numbering(self):
        """段内多点：threats rank 从 1 递增，route seq 从 1 递增，顺序保留。"""
        text = (
            "【威胁排序】鹰炮 格(36,9)；防空塔 格(15,30)；法师塔 格(25,12)。\n"
            "【进攻路线】防空塔 格(15,30) → 法师塔 格(25,12) → 大本营 格(20,20)。\n"
            "【兵种与法术】本地规则建议。\n"
        )
        out = tactics.parse_plan_marks({"text": text})
        ranks = [t["rank"] for t in out["threats"]]
        self.assertEqual(ranks, [1, 2, 3])
        self.assertEqual([t["tile"] for t in out["threats"]],
                         [[36, 9], [15, 30], [25, 12]])
        seqs = [r["seq"] for r in out["route"]]
        self.assertEqual(seqs, [1, 2, 3])
        self.assertEqual([r["label"] for r in out["route"]],
                         ["防空塔", "法师塔", "大本营"])


class TestParsePlanMarksNegative(unittest.TestCase):
    """必须拒：方括号、无标签裸坐标、越界、绕开区、缺三段标题。"""

    def test_bracket_coordinates_rejected(self):
        """方括号 `格[36.0,9.0]` 不是合法括号对，匹配不到，threats 为空。"""
        text = _threat_text("格[36.0,9.0]")
        out = tactics.parse_plan_marks({"text": text})
        self.assertEqual(out["threats"], [])

    def test_naked_coordinate_without_label_rejected(self):
        """无已知建筑名的裸坐标：回找窗找不到标签，不画（R1：不猜标签）。"""
        text = _threat_text("先处理 格(20,20)")
        out = tactics.parse_plan_marks({"text": text})
        self.assertEqual(out["threats"], [])

    def test_out_of_range_high_rejected(self):
        """格号 >43 越界：格(44,1) 跳过。"""
        text = _threat_text("鹰炮 格(44,1)")
        out = tactics.parse_plan_marks({"text": text})
        self.assertEqual(out["threats"], [])

    def test_out_of_range_low_rejected(self):
        """格号 <0 越界：格(-1,5) 跳过。"""
        text = _threat_text("鹰炮 格(-1,5)")
        out = tactics.parse_plan_marks({"text": text})
        self.assertEqual(out["threats"], [])

    def test_avoid_zone_coordinate_rejected(self):
        """绕开区裸坐标：上下文命中 绕开/避开/重区/覆盖/盲区，route 不抓该点；
        但同段合法威胁点仍保留。"""
        text = (
            "【威胁排序】鹰炮 格(36,9)。\n"
            "【进攻路线】绕开格(10,10)重区，再从侧面进。\n"
            "【兵种与法术】本地规则建议。\n"
        )
        out = tactics.parse_plan_marks({"text": text})
        self.assertEqual(len(out["threats"]), 1)
        self.assertEqual(out["threats"][0]["tile"], [36, 9])
        self.assertEqual(out["route"], [])

    def test_missing_section_headers_rejected(self):
        """缺三段式标题：两段都取不到，返回空结构，不抛异常。"""
        out = tactics.parse_plan_marks({"text": "今天先打东边，再打西边，注意防空。"})
        self.assertEqual(out, {"threats": [], "route": []})

    def test_empty_text_rejected(self):
        """空文本 / 空白文本：返回空结构。"""
        self.assertEqual(tactics.parse_plan_marks({"text": ""}),
                         {"threats": [], "route": []})
        self.assertEqual(tactics.parse_plan_marks({"text": "   "}),
                         {"threats": [], "route": []})
        self.assertEqual(tactics.parse_plan_marks(None),
                         {"threats": [], "route": []})


if __name__ == "__main__":
    unittest.main()
