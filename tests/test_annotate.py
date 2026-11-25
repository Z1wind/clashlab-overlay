# -*- coding: utf-8 -*-
r"""tools/annotate 纯逻辑单测（不依赖 numpy / cv2 / 浏览器）。

覆盖：
  1. quad 解析（bases/th16/*/layout.json 的 note 变体）
  2. 坐标换算：tile<->px 单应、单元中心、floor 取整、边界 clamp、透视 quad
  3. layout schema 校验与规范化（与 bases/th16/NN/layout.json 同 schema）
  4. 预填合并（resume）与人工修改差异统计
  5. 保存/读取 round-trip、原子写、summary 聚合
  6. bases 目录发现（TH 分组 + 候选方案）
  7. 真实数据只读校验（quad 在图像内、每栋建筑 cell 中心回投命中自身）

运行：
  D:\Python313\python.exe -m unittest tests.test_annotate -v
  D:\Python313\python.exe -m unittest discover -s tests -v
"""
import copy
import json
import math
import os
import struct
import sys
import tempfile
import unittest
import zlib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANNOTATE_DIR = os.path.join(PROJECT_ROOT, "tools", "annotate")
if ANNOTATE_DIR not in sys.path:
    sys.path.insert(0, ANNOTATE_DIR)

import annotate_core as core  # noqa: E402

GRID = 44
QUAD_01 = [[1180.0, 90.0], [2150.0, 480.0], [1180.0, 1180.0], [500.0, 480.0]]
QUAD_SMALL = [[500.0, 12.0], [860.0, 215.0], [500.0, 456.0], [140.0, 215.0]]
QUAD_PERSPECTIVE = [[100.0, 0.0], [520.0, 120.0], [100.0, 420.0], [-280.0, 140.0]]


def _minimal_layout(**over):
    """最小合法 layout（与生产 schema 同构）。"""
    doc = {
        "name": "unit_min",
        "grid": 44,
        "note": "quad=[[100,0],[500,200],[100,400],[-300,200]]，单测样本",
        "buildings": [
            {"type": "cannon", "tile": [8, 2], "source": "manual", "conf": 0.6, "note": "右上重炮"},
            {"type": "town-hall", "tile": [18, 14], "source": "manual", "conf": 0.9, "note": "中央大本营"},
            {"type": "x-bow", "tile": [34, 6], "source": "manual", "conf": 0.7, "note": ""},
        ],
        "walls": [[0, 0], [0, 44], [43, 43], [20, 20]],
    }
    doc.update(over)
    return doc


def _png_bytes(width, height):
    """构造一个纯色 RGB PNG（只用标准库），用于 image_size 测试。"""
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class QuadParseTests(unittest.TestCase):
    def test_parse_quad_layout01_style(self):
        note = ("TH16 anti-3star 人工标注 v2。quad=[[1180,90],[2150,480],"
                "[1180,1180],[500,480]]，Calib.from_quad，reproj_error=0.0。")
        self.assertEqual(core.parse_quad(note), QUAD_01)

    def test_parse_quad_labeled_and_trailing_variants(self):
        note = ("quad(上,右,下,左)=[[500,12],[860,215],[500,456],[140,215]]，"
                "Calib.from_quad（包络标定）")
        self.assertEqual(core.parse_quad(note), QUAD_SMALL)
        note2 = ("quad=[[1278,27],[2087,668],[1306,1215],[454,618]]（RANSAC 拟合四条外墙外线交点）")
        self.assertEqual(core.parse_quad(note2)[3], [454.0, 618.0])

    def test_parse_quad_missing_returns_none(self):
        self.assertIsNone(core.parse_quad(""))
        self.assertIsNone(core.parse_quad("没有定标信息的人工说明"))
        self.assertIsNone(core.parse_quad(None))

    def test_parse_quad_malformed_returns_none(self):
        self.assertIsNone(core.parse_quad("quad=[[1,2],[3,4]]"))
        self.assertIsNone(core.parse_quad("quad=[[1,2],[3,4],[5,6],[7,8],[9,10]]"))
        self.assertIsNone(core.parse_quad("quad=[[1,a],[3,4],[5,6],[7,8]]"))
        self.assertIsNone(core.parse_quad("quad=[[1,2],[3,4],[5,6],[7]]"))


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.H = core.homography_from_quad(QUAD_01, GRID)
        self.Hinv = core.invert3x3(self.H)

    def test_homography_maps_four_corners_exactly(self):
        for (gx, gy), (px, py) in zip(
                [(0, 0), (GRID, 0), (GRID, GRID), (0, GRID)], QUAD_01):
            x, y = core.tile_to_px(self.H, gx, gy)
            self.assertAlmostEqual(x, px, places=6)
            self.assertAlmostEqual(y, py, places=6)

    def test_cell_center_roundtrip_all_cells(self):
        for tx in range(0, GRID, 5):
            for ty in range(0, GRID, 7):
                px, py = core.cell_to_px(self.H, tx, ty)
                self.assertEqual(core.px_to_cell(self.Hinv, px, py, GRID), (tx, ty))

    def test_px_to_tile_center_convention(self):
        # 单元格 (8,2) 的几何中心 = (8.5, 2.5)，floor 回投必须是 (8,2)
        px, py = core.tile_to_px(self.H, 8.5, 2.5)
        self.assertAlmostEqual(core.px_to_tile(self.Hinv, px, py)[0], 8.5, places=6)
        self.assertEqual(core.px_to_cell(self.Hinv, px, py, GRID), (8, 2))
        # 中心格内任意抖动都不能跨格
        for dx, dy in ((-0.3, -0.3), (0.3, 0.3), (-0.49, 0.0), (0.0, 0.49)):
            px, py = core.tile_to_px(self.H, 8.5 + dx, 2.5 + dy)
            self.assertEqual(core.px_to_cell(self.Hinv, px, py, GRID), (8, 2))

    def test_px_to_cell_clamp_behaviour(self):
        out_px = core.tile_to_px(self.H, -3.0, GRID + 6.0)
        self.assertEqual(core.px_to_cell(self.Hinv, out_px[0], out_px[1], GRID, clamp=True), (0, GRID - 1))
        self.assertIsNone(core.px_to_cell(self.Hinv, out_px[0], out_px[1], GRID, clamp=False))

    def test_perspective_quad_roundtrip(self):
        H = core.homography_from_quad(QUAD_PERSPECTIVE, GRID)
        Hinv = core.invert3x3(H)
        for tx, ty in ((0, 0), (1, 1), (10, 30), (22, 22), (42, 7), (43, 43)):
            px, py = core.cell_to_px(H, tx, ty)
            self.assertEqual(core.px_to_cell(Hinv, px, py, GRID), (tx, ty))

    def test_inverse_roundtrip_composition(self):
        for x, y in ((0.0, 0.0), (1234.5, 678.25), (2150.0, 480.0), (900.0, 1100.0)):
            ix, iy = core.apply_h(self.Hinv, x, y)
            rx, ry = core.apply_h(self.H, ix, iy)
            self.assertAlmostEqual(rx, x, places=5)
            self.assertAlmostEqual(ry, y, places=5)

    def test_order_diamond_normalizes_shuffled_quad(self):
        shuffled = [QUAD_01[1], QUAD_01[3], QUAD_01[0], QUAD_01[2]]
        self.assertEqual(core.order_diamond(shuffled), QUAD_01)

    def test_degenerate_quad_raises(self):
        with self.assertRaises(ValueError):
            core.homography_from_quad([[0, 0], [10, 0], [20, 0], [30, 0]], GRID)

    def test_geometry_for_layout(self):
        geo = core.geometry_for_layout(_minimal_layout())
        self.assertIsNotNone(geo)
        self.assertEqual(geo["grid"], 44)
        self.assertEqual(geo["quad"], [[100.0, 0.0], [500.0, 200.0], [100.0, 400.0], [-300.0, 200.0]])
        self.assertEqual(len(geo["H"]), 3)
        self.assertIsNone(core.geometry_for_layout(_minimal_layout(note="无 quad")))


class SchemaTests(unittest.TestCase):
    def test_valid_minimal_layout_passes(self):
        self.assertEqual(core.validate_layout(_minimal_layout()), [])

    def test_root_type_checks(self):
        self.assertTrue(core.validate_layout([]))
        self.assertTrue(core.validate_layout({"grid": 44}))
        self.assertTrue(core.validate_layout(_minimal_layout(name="")))
        self.assertTrue(core.validate_layout(_minimal_layout(grid=0)))
        self.assertTrue(core.validate_layout(_minimal_layout(grid="44")))
        self.assertTrue(core.validate_layout(_minimal_layout(grid=True)))

    def test_grid_mismatch_with_expected_grid(self):
        doc = _minimal_layout(grid=44)
        self.assertTrue(core.validate_layout(doc, grid=40))

    def test_buildings_checks(self):
        bad_type = copy.deepcopy(_minimal_layout())
        bad_type["buildings"][0]["type"] = "cannonn"
        self.assertTrue(core.validate_layout(bad_type))

        bad_tile = copy.deepcopy(_minimal_layout())
        bad_tile["buildings"][0]["tile"] = [45, 2]
        self.assertTrue(core.validate_layout(bad_tile))

        # 生产数据里存在贴边 tile=44（01 阵），预填原样保存必须合法
        edge_tile = copy.deepcopy(_minimal_layout())
        edge_tile["buildings"][0]["tile"] = [44, 2]
        self.assertEqual(core.validate_layout(edge_tile), [])

        neg_tile = copy.deepcopy(_minimal_layout())
        neg_tile["buildings"][0]["tile"] = [-1, 2]
        self.assertTrue(core.validate_layout(neg_tile))

        float_tile = copy.deepcopy(_minimal_layout())
        float_tile["buildings"][0]["tile"] = [8.5, 2]
        self.assertTrue(core.validate_layout(float_tile))

        bool_tile = copy.deepcopy(_minimal_layout())
        bool_tile["buildings"][0]["tile"] = [True, 2]
        self.assertTrue(core.validate_layout(bool_tile))

        bad_conf = copy.deepcopy(_minimal_layout())
        bad_conf["buildings"][0]["conf"] = 1.5
        self.assertTrue(core.validate_layout(bad_conf))

        self.assertTrue(core.validate_layout(_minimal_layout(buildings={})))

    def test_walls_boundary_allowed(self):
        self.assertIn([0, 44], _minimal_layout()["walls"])
        self.assertEqual(core.validate_layout(_minimal_layout()), [])
        bad = _minimal_layout(walls=[[0, 45]])
        self.assertTrue(core.validate_layout(bad))
        bad2 = _minimal_layout(walls=[[1]])
        self.assertTrue(core.validate_layout(bad2))

    def test_normalize_layout_canonical_schema(self):
        doc = _minimal_layout()
        doc["extra_root"] = "drop-me"
        doc["buildings"][0]["px"] = [1, 2]
        doc["buildings"][1].pop("note")
        out = core.normalize_layout(doc)
        self.assertEqual(list(out.keys()), ["name", "grid", "note", "buildings", "walls"])
        self.assertEqual(list(out["buildings"][0].keys()), ["type", "tile", "source", "conf", "note"])
        self.assertNotIn("extra_root", out)
        self.assertNotIn("px", out["buildings"][0])
        self.assertEqual(out["buildings"][1]["note"], "")
        self.assertEqual(out["buildings"][1]["source"], "manual")


class PrefillDiffTests(unittest.TestCase):
    def setUp(self):
        self.layout = core.normalize_layout(_minimal_layout())

    def test_resolve_prefill_falls_back_to_layout(self):
        doc, src = core.resolve_prefill(self.layout, None)
        self.assertEqual(src, "layout")
        self.assertEqual(doc, self.layout)

    def test_resolve_prefill_prefers_valid_annotated(self):
        annotated = copy.deepcopy(self.layout)
        annotated["buildings"][0]["type"] = "mortar"
        doc, src = core.resolve_prefill(self.layout, annotated)
        self.assertEqual(src, "annotated")
        self.assertEqual(doc["buildings"][0]["type"], "mortar")

    def test_resolve_prefill_ignores_invalid_annotated(self):
        broken = copy.deepcopy(self.layout)
        broken["buildings"][0]["type"] = "not-a-type"
        doc, src = core.resolve_prefill(self.layout, broken)
        self.assertEqual(src, "layout")
        self.assertEqual(doc, self.layout)

    def test_diff_unchanged(self):
        diff = core.diff_layout(self.layout, copy.deepcopy(self.layout))
        self.assertEqual(diff["edits"], 0)
        self.assertEqual(diff["unchanged"], 3)

    def test_diff_retyped(self):
        after = copy.deepcopy(self.layout)
        after["buildings"][0]["type"] = "mortar"
        diff = core.diff_layout(self.layout, after)
        self.assertEqual((diff["retyped"], diff["moved"], diff["added"], diff["removed"]), (1, 0, 0, 0))
        self.assertEqual(diff["edits"], 1)

    def test_diff_moved(self):
        after = copy.deepcopy(self.layout)
        after["buildings"][2]["tile"] = [30, 10]
        diff = core.diff_layout(self.layout, after)
        self.assertEqual((diff["moved"], diff["retyped"]), (1, 0))
        self.assertEqual(diff["edits"], 1)

    def test_diff_added_and_removed(self):
        after = copy.deepcopy(self.layout)
        after["buildings"].append(
            {"type": "archer-tower", "tile": [10, 10], "source": "manual", "conf": 1.0, "note": ""})
        diff = core.diff_layout(self.layout, after)
        self.assertEqual((diff["added"], diff["removed"]), (1, 0))
        after2 = copy.deepcopy(self.layout)
        after2["buildings"].pop(1)
        diff2 = core.diff_layout(self.layout, after2)
        self.assertEqual((diff2["added"], diff2["removed"]), (0, 1))
        self.assertEqual(diff2["edits"], 1)

    def test_with_provenance_is_idempotent(self):
        note = ("原始说明；tools/annotate 人工校正 2026-01-01T00:00:00+08:00"
                "（edits=2；candidate=layout）")
        out = core.with_provenance(note, 3, "altA", stamp="2026-01-02T00:00:00+08:00")
        self.assertTrue(out.startswith("原始说明；tools/annotate 人工校正 2026-01-02"))
        self.assertIn("edits=3", out)
        self.assertIn("candidate=altA", out)
        self.assertEqual(out.count("tools/annotate 人工校正"), 1)

    def test_diff_combined(self):
        after = copy.deepcopy(self.layout)
        after["buildings"][0]["type"] = "wizard-tower"   # retyped
        after["buildings"][1]["tile"] = [19, 14]         # moved
        after["buildings"].pop(2)                        # removed
        after["buildings"].append(
            {"type": "bomb-tower", "tile": [5, 40], "source": "manual", "conf": 1.0, "note": ""})
        diff = core.diff_layout(self.layout, after)
        self.assertEqual(diff["edits"], 4)
        self.assertEqual(diff["unchanged"], 0)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="annot_storage_")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_load_roundtrip_unicode(self):
        doc = core.normalize_layout(_minimal_layout(note="中文说明 ✓ quad=[[1,2],[3,4],[5,6],[7,8]]"))
        path = os.path.join(self.tmp, "out", "annotate", "01_annotated.json")
        core.write_json_atomic(path, doc)
        self.assertTrue(os.path.isfile(path))
        back = core.load_json(path)
        self.assertEqual(back, doc)
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        self.assertIn("中文说明", raw)          # ensure_ascii=False
        self.assertFalse(raw.startswith("\ufeff"))  # 不写 BOM

    def test_atomic_write_no_tmp_left(self):
        path = os.path.join(self.tmp, "x", "y.json")
        core.write_json_atomic(path, {"a": 1})
        core.write_json_atomic(path, {"a": 2})
        left = [n for n in os.listdir(os.path.dirname(path)) if n.endswith(".tmp") or ".tmp." in n]
        self.assertEqual(left, [])
        self.assertEqual(core.load_json(path), {"a": 2})

    def test_load_missing_returns_none(self):
        self.assertIsNone(core.load_json(os.path.join(self.tmp, "nope.json")))

    def test_load_invalid_json_returns_none(self):
        path = os.path.join(self.tmp, "bad.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write("{not json")
        self.assertIsNone(core.load_json(path))

    def test_paths_helpers(self):
        self.assertEqual(core.annotated_rel_path("01"), os.path.join("out", "annotate", "01_annotated.json"))
        self.assertEqual(core.summary_rel_path(), os.path.join("out", "annotate", "summary.json"))
        self.assertTrue(core.annotated_path(self.tmp, "01").endswith("01_annotated.json"))

    def test_image_size_png(self):
        path = os.path.join(self.tmp, "tiny.png")
        with open(path, "wb") as f:
            f.write(_png_bytes(3, 2))
        self.assertEqual(core.image_size(path), (3, 2))

    def test_image_size_missing_or_unknown(self):
        self.assertIsNone(core.image_size(os.path.join(self.tmp, "nope.png")))
        bad = os.path.join(self.tmp, "x.bin")
        with open(bad, "wb") as f:
            f.write(b"not an image")
        self.assertIsNone(core.image_size(bad))

    def test_summary_roundtrip_and_upsert(self):
        doc = core.normalize_layout(_minimal_layout())
        diff = core.diff_layout(doc, doc)
        entry = core.make_summary_entry("01", "th16", doc, diff, 12345, status="done", candidate="layout")
        summary = core.build_summary([entry])
        self.assertEqual(summary["totals"]["bases"], 1)
        self.assertEqual(summary["totals"]["done"], 1)
        self.assertEqual(summary["totals"]["buildings"], 3)
        path = core.summary_path(self.tmp)
        core.write_json_atomic(path, summary)
        loaded = core.load_summary(path)
        self.assertEqual(loaded["bases"][0]["base"], "01")

        entry2 = dict(entry, base="02", manual_edits=2)
        updated = core.upsert_summary(loaded, entry2)
        self.assertEqual(len(updated["bases"]), 2)
        self.assertEqual(core.load_summary(os.path.join(self.tmp, "nope.json"))["bases"], [])


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="annot_discover_")
        bases = os.path.join(self.tmp, "bases")
        for rel, files in {
            "th16/01": ["base.png", "layout.json"],
            "th16/02": ["base.png", "layout.json", "layouts/altA.json"],
            "th15/01": ["base.png", "layout.json"],
            "th16/03": ["base.png"],  # 缺 layout.json，应跳过
        }.items():
            d = os.path.join(bases, *rel.split("/"))
            os.makedirs(d, exist_ok=True)
            for f in files:
                p = os.path.join(d, *f.split("/"))
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8") as fh:
                    if p.endswith(".json"):
                        fh.write(json.dumps(_minimal_layout(), ensure_ascii=False))
                    else:
                        fh.write("")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_discover_bases_sorted_and_skips_incomplete(self):
        bases = core.discover_bases(self.tmp, "th16")
        self.assertEqual([b["id"] for b in bases], ["01", "02"])
        self.assertEqual(bases[1]["candidates"][0]["id"], "altA")
        self.assertEqual(bases[0]["candidates"], [])

    def test_discover_groups_sorted_numeric(self):
        groups = core.discover_groups(self.tmp)
        self.assertEqual([g["th"] for g in groups], ["th15", "th16"])
        self.assertEqual(groups[1]["label"], "TH16")
        self.assertEqual([b["id"] for b in groups[1]["bases"]], ["01", "02"])


class RealDataTests(unittest.TestCase):
    """只读校验生产数据：quad 在 base.png 像素内、手工标注的 tile 回投自洽。"""

    @classmethod
    def setUpClass(cls):
        cls.bases = os.path.join(PROJECT_ROOT, "bases", "th16")
        cls.ids = sorted(
            n for n in (os.listdir(cls.bases) if os.path.isdir(cls.bases) else [])
            if os.path.isfile(os.path.join(cls.bases, n, "layout.json")))

    def _require(self):
        if not self.ids:
            self.skipTest("bases/th16 不存在，跳过生产数据校验")

    def test_production_layouts_pass_schema(self):
        self._require()
        for bid in self.ids:
            with self.subTest(base=bid):
                doc = core.load_json(os.path.join(self.bases, bid, "layout.json"))
                self.assertIsNotNone(doc)
                self.assertEqual(core.validate_layout(doc), [])

    def test_production_quads_in_image_bounds_and_cells_roundtrip(self):
        self._require()
        for bid in self.ids:
            with self.subTest(base=bid):
                base_dir = os.path.join(self.bases, bid)
                doc = core.load_json(os.path.join(base_dir, "layout.json"))
                geo = core.geometry_for_layout(doc)
                self.assertIsNotNone(geo, f"{bid} 缺 quad")
                size = core.image_size(os.path.join(base_dir, "base.png"))
                self.assertIsNotNone(size, f"{bid} 读不到 base.png 尺寸")
                w, h = size
                for qx, qy in geo["quad"]:
                    self.assertGreaterEqual(qx, -30)
                    self.assertGreaterEqual(qy, -30)
                    self.assertLessEqual(qx, w + 30)
                    self.assertLessEqual(qy, h + 30)
                for b in doc["buildings"]:
                    tx, ty = b["tile"]
                    self.assertTrue(0 <= tx <= doc["grid"] and 0 <= ty <= doc["grid"])
                    if tx >= doc["grid"] or ty >= doc["grid"]:
                        continue  # 生产数据有贴边 clamp 到 grid 的条目，单元中心落在域外
                    px, py = core.cell_to_px(geo["H"], tx, ty)
                    self.assertEqual(core.px_to_cell(geo["Hinv"], px, py, doc["grid"]), (tx, ty))

    def test_production_types_covered_by_palette(self):
        self._require()
        for bid in self.ids:
            doc = core.load_json(os.path.join(self.bases, bid, "layout.json"))
            for b in doc["buildings"]:
                self.assertIn(b["type"], core.ALLOWED_TYPES, f"{bid} 类型 {b['type']} 不在调色板内")
                self.assertIn(b["type"], core.TYPE_CN)
                self.assertIn(b["type"], core.TYPE_SIZE)

    def test_palette_shape(self):
        self.assertGreaterEqual(len(core.PALETTE), 9)
        self.assertEqual(len(set(core.PALETTE)), len(core.PALETTE))
        self.assertEqual(core.ALLOWED_TYPES, frozenset(core.PALETTE))
        self.assertGreaterEqual(core.PALETTE_HOTKEY_COUNT, 9)


if __name__ == "__main__":
    unittest.main(verbosity=2)
