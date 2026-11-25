# -*- coding: utf-8 -*-
"""clashlab.baselink 单元测试。

覆盖三层：
1. 真实链接（本项目 bases/th16/{01,03,04,05,06}/source.json 的 copy_link）：
   解析、payload 24 字节结构、opaque-token 判定、无法解码的诚实降级；
2. 构造样本（合成 COCL 二进制 + JSON 布局，多种压缩容器）：
   端到端覆盖「payload -> 解压 -> 阵型 -> layout.json schema」的解码逻辑；
3. 错误路径：非法 scheme/host/action/id、坏 base64url、坏 COCL/JSON 结构。
"""
import base64
import bz2
import glob
import gzip
import json
import lzma
import os
import sys
import unittest
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clashlab import baselink  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: 本项目 5 条真实链接（原文抄自 bases/th16/*/source.json 的 copy_link 字段）
REAL_URLS = [
    "https://link.clashofclans.com/en?action=OpenLayout&id=TH16%3AWB%3AAAAAEAAAAALcZibtGVUmqwp_G3t1bCs3",
    "https://link.clashofclans.com/en?action=OpenLayout&id=TH16%3AWB%3AAAAAEAAAAALj9WFNVNIhUth-maHuon5r",
    "https://link.clashofclans.com/en?action=OpenLayout&id=TH16%3AWB%3AAAAAEAAAAALjAvPkepIe-Af5wQ9gP0VL",
    "https://link.clashofclans.com/en?action=OpenLayout&id=TH16%3AWB%3AAAAAEAAAAALe-fUBf4QAmyjlXXoj21FY",
    "https://link.clashofclans.com/en?action=OpenLayout&id=TH16%3AHV%3AAAAAEAAAAALkH4AWLkrpPc2b-wskhFUt",
]

#: 合成 COCL 样本（仅测试用，不是真实游戏格式）
COCL_BUILDINGS = [("town-hall", 18, 14), ("cannon", 0, 0), ("air-defense", 43, 43)]
COCL_WALLS = [(0, 1), (1, 0), (43, 42)]

#: 合成 JSON 布局样本
JSON_LAYOUT = {
    "grid": 44,
    "buildings": [
        {"type": "town-hall", "tile": [18, 14]},
        {"type": "cannon", "tile": [0, 0]},
    ],
    "walls": [[0, 1], [1, 0]],
}

CONTAINERS = {
    "raw": lambda raw: raw,
    "zlib": zlib.compress,
    "gzip": gzip.compress,
    "bz2": bz2.compress,
    "lzma": lzma.compress,
}


def b64url(raw):
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def make_url(payload, th=16, village="WB", lang="en"):
    from urllib.parse import quote

    ident = "TH%d:%s:%s" % (th, village, payload)
    return "https://link.clashofclans.com/%s?action=OpenLayout&id=%s" % (lang, quote(ident, safe=""))


def real_sample_urls():
    return list(REAL_URLS)


class TestRealLinks(unittest.TestCase):
    def test_parse_real_links(self):
        self.assertEqual(len(real_sample_urls()), 5)
        for url in real_sample_urls():
            with self.subTest(url=url[-12:]):
                link = baselink.parse_link(url)
                self.assertEqual(link.town_hall, 16)
                self.assertIn(link.village, ("HV", "WB"))
                self.assertEqual(link.village_name, baselink.VILLAGE_NAMES[link.village])
                self.assertEqual(len(link.payload), 32)
                raw = baselink.decode_payload(link.payload)
                self.assertEqual(len(raw), 24)

    def test_real_links_have_identical_envelope_prefix(self):
        prefixes = set()
        for url in real_sample_urls():
            raw = baselink.decode_payload(baselink.parse_link(url).payload)
            prefixes.add(raw[:8].hex())
            env = baselink.parse_envelope(raw)
            self.assertEqual(env.declared_length, 16)
            self.assertEqual(env.kind, 2)
            self.assertEqual(len(env.value), 16)
            self.assertTrue(env.consistent)
        self.assertEqual(len(prefixes), 1, "5 条真实样本的 8 字节信封头应完全一致")

    def test_first_real_sample_exact_bytes(self):
        raw = baselink.decode_payload(baselink.parse_link(REAL_URLS[0]).payload)
        self.assertEqual(
            raw.hex(),
            "0000001000000002dc6626ed195526ab0a7f1b7b756c2b37",
        )

    def test_real_links_are_opaque_and_not_decodable(self):
        for url in real_sample_urls():
            with self.subTest(url=url[-12:]):
                report = baselink.analyze_link(url)
                self.assertFalse(report["decoded"])
                self.assertIsNone(report["codec"])
                self.assertEqual(report["payload_kind"], "opaque-token-v1")
                self.assertEqual(report["building_count"], 0)
                self.assertEqual(report["wall_count"], 0)
                self.assertGreaterEqual(len(report["codec_attempts"]), 10)
                self.assertTrue(all(not a["ok"] for a in report["codec_attempts"]))
                self.assertTrue(all(a["detail"] for a in report["codec_attempts"]))
                opaque = report["opaque_token"]
                self.assertEqual(opaque["raw_len"], 24)
                self.assertEqual(opaque["declared_length"], 16)
                self.assertEqual(opaque["value_len"], 16)
                self.assertIn("不透明", opaque["conclusion"])

    def test_real_links_on_disk_match_embedded_samples(self):
        pattern = os.path.join(ROOT, "bases", "th16", "*", "source.json")
        paths = sorted(glob.glob(pattern))
        if not paths:
            self.skipTest("bases/th16/*/source.json 不存在")
        found = []
        for path in paths:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            link = data.get("copy_link")
            if link:
                found.append(link)
        self.assertGreaterEqual(len(found), 5)
        for url in found:
            with self.subTest(url=url[-12:]):
                parsed = baselink.parse_link(url)
                self.assertEqual(parsed.town_hall, 16)
                self.assertEqual(len(parsed.payload), 32)
                self.assertEqual(len(baselink.decode_payload(parsed.payload)), 24)


class TestLinkParsing(unittest.TestCase):
    def test_parse_id_direct(self):
        link = baselink.parse_id("TH16:WB:AAAAEAAAAALcZibtGVUmqwp_G3t1bCs3")
        self.assertEqual(link.town_hall, 16)
        self.assertEqual(link.village, "WB")
        self.assertEqual(link.payload, "AAAAEAAAAALcZibtGVUmqwp_G3t1bCs3")

    def test_parse_unencoded_colons(self):
        url = (
            "https://link.clashofclans.com/en?action=OpenLayout"
            "&id=TH16:WB:AAAAEAAAAALcZibtGVUmqwp_G3t1bCs3"
        )
        link = baselink.parse_link(url)
        self.assertEqual(link.payload, "AAAAEAAAAALcZibtGVUmqwp_G3t1bCs3")

    def test_language_paths(self):
        cases = [
            ("/en", "en"),
            ("/en-US", "en-US"),
            ("", ""),
            ("/", ""),
        ]
        for lang, expected in cases:
            with self.subTest(lang=lang):
                url = "https://link.clashofclans.com%s?action=OpenLayout&id=TH16%%3AWB%%3AAAAAEAAAAALcZibtGVUmqwp_G3t1bCs3" % lang
                self.assertEqual(baselink.parse_link(url).language, expected)

    def test_reject_invalid_links(self):
        base = "https://link.clashofclans.com/en?action=OpenLayout&id=TH16%3AWB%3AAAAEAAAAALcZibtGVUmqwp_G3t1bCs3"
        cases = [
            ("", "empty_url"),
            ("http://link.clashofclans.com/en?action=OpenLayout&id=TH16%3AWB%3AAAA", "bad_scheme"),
            ("https://evil.test/en?action=OpenLayout&id=TH16%3AWB%3AAAA", "bad_host"),
            (base + "#frag", "bad_fragment"),
            ("https://link.clashofclans.com/en?action=OpenVillage&id=TH16%3AWB%3AAAA", "bad_action"),
            ("https://link.clashofclans.com/en?action=OpenLayout", "bad_query"),
            ("https://link.clashofclans.com/en?action=OpenLayout&id=TH16%3AWB%3AAAA&id=x", "bad_query"),
            ("https://link.clashofclans.com/en?action=OpenLayout&id=TH16%3AWB%3AAAA&x=1", "bad_query"),
            ("https://link.clashofclans.com/foo/bar?action=OpenLayout&id=TH16%3AWB%3AAAA", "bad_path"),
            ("https://link.clashofclans.com/en?action=OpenLayout&id=TH0%3AWB%3AAAA", "bad_id"),
            ("https://link.clashofclans.com/en?action=OpenLayout&id=TH16%3AXX%3AAAA", "bad_id"),
            ("https://link.clashofclans.com/en?action=OpenLayout&id=TH16%3AWB%3Aabc!", "bad_id"),
            ("https://link.clashofclans.com/en?action=OpenLayout&id=not-a-link", "bad_id"),
        ]
        for url, code in cases:
            with self.subTest(code=code, url=url[:70]):
                with self.assertRaises(baselink.BaseLinkError) as ctx:
                    baselink.parse_link(url)
                self.assertEqual(ctx.exception.code, code)


class TestPayloadDecoding(unittest.TestCase):
    def test_decode_payload_padding(self):
        payload = "AAAAEAAAAALcZibtGVUmqwp_G3t1bCs3"
        raw = baselink.decode_payload(payload)
        self.assertEqual(len(raw), 24)
        self.assertEqual(baselink.decode_payload(payload + "="), raw)

    def test_decode_payload_rejects_bad_chars(self):
        with self.assertRaises(baselink.BaseLinkError) as ctx:
            baselink.decode_payload("abc!")
        self.assertEqual(ctx.exception.code, "bad_payload_chars")

    def test_decode_payload_rejects_mod1_length(self):
        with self.assertRaises(baselink.BaseLinkError) as ctx:
            baselink.decode_payload("abcde")
        self.assertEqual(ctx.exception.code, "bad_payload_base64")

    def test_decode_payload_rejects_empty(self):
        with self.assertRaises(baselink.BaseLinkError) as ctx:
            baselink.decode_payload("")
        self.assertEqual(ctx.exception.code, "empty_payload")

    def test_envelope_short_raw(self):
        env = baselink.parse_envelope(b"\x00\x01")
        self.assertIsNone(env.declared_length)
        self.assertIsNone(env.kind)
        self.assertEqual(env.value, b"\x00\x01")

    def test_envelope_length_mismatch_flagged(self):
        env = baselink.parse_envelope(b"\x00\x00\x00\x05\x00\x00\x00\x02abc")
        self.assertEqual(env.declared_length, 5)
        self.assertEqual(env.kind, 2)
        self.assertFalse(env.consistent)

    def test_classify_payload(self):
        opaque = bytes.fromhex("0000001000000002" + "aa" * 16)
        self.assertEqual(baselink.classify_payload(opaque), "opaque-token-v1")
        self.assertEqual(
            baselink.classify_payload(baselink.encode_cocl_layout(COCL_BUILDINGS)),
            "cocl-synthetic",
        )
        self.assertEqual(baselink.classify_payload(zlib.compress(b"hello")), "compressed-candidate")
        self.assertEqual(baselink.classify_payload(b"\x00\x01"), "unknown")


class TestSyntheticCodecs(unittest.TestCase):
    """构造样本覆盖解码逻辑：COCL 二进制 + JSON 布局 x 多种容器。"""

    def test_cocl_roundtrip_all_containers(self):
        blob = baselink.encode_cocl_layout(COCL_BUILDINGS, COCL_WALLS)
        for name, pack in CONTAINERS.items():
            with self.subTest(container=name):
                payload = b64url(pack(blob))
                result = baselink.decode_layout_payload(baselink.decode_payload(payload))
                self.assertTrue(result.ok, result.attempts)
                expected_codec = "cocl-raw" if name == "raw" else "cocl+" + name
                self.assertEqual(result.codec, expected_codec)
                self.assertIsNotNone(result.layout)
                self.assertEqual(list(result.layout.buildings), COCL_BUILDINGS)
                self.assertEqual(list(result.layout.walls), COCL_WALLS)
                self.assertEqual(result.payload_kind, "cocl-synthetic")
                ok_attempts = [a for a in result.attempts if a.ok]
                self.assertEqual(len(ok_attempts), 1)
                self.assertEqual(ok_attempts[0].codec, expected_codec)

    def test_json_roundtrip_all_containers(self):
        blob = json.dumps(JSON_LAYOUT).encode("utf-8")
        for name, pack in CONTAINERS.items():
            with self.subTest(container=name):
                payload = b64url(pack(blob))
                result = baselink.decode_layout_payload(baselink.decode_payload(payload))
                self.assertTrue(result.ok, result.attempts)
                expected_codec = "json-raw" if name == "raw" else "json+" + name
                self.assertEqual(result.codec, expected_codec)
                self.assertEqual(list(result.layout.buildings), [("town-hall", 18, 14), ("cannon", 0, 0)])
                self.assertEqual(list(result.layout.walls), [(0, 1), (1, 0)])

    def test_cocl_rejects_bad_grid(self):
        blob = bytearray(baselink.encode_cocl_layout(COCL_BUILDINGS))
        blob[5] = 45  # grid 字段
        result = baselink.decode_layout_payload(bytes(blob))
        self.assertFalse(result.ok)
        self.assertIn("grid=45", " ".join(a.detail for a in result.attempts))

    def test_cocl_rejects_unknown_type_and_truncation(self):
        blob = bytearray(baselink.encode_cocl_layout(COCL_BUILDINGS))
        blob[10] = 99  # 第一条建筑的 type_id
        self.assertFalse(baselink.decode_layout_payload(bytes(blob)).ok)
        truncated = baselink.encode_cocl_layout(COCL_BUILDINGS)[:-1]
        self.assertFalse(baselink.decode_layout_payload(truncated).ok)

    def test_cocl_encoder_validates(self):
        with self.assertRaises(baselink.LayoutDecodeError):
            baselink.encode_cocl_layout([("unknown-type", 0, 0)])
        with self.assertRaises(baselink.LayoutDecodeError):
            baselink.encode_cocl_layout([("cannon", 44, 0)])
        with self.assertRaises(baselink.LayoutDecodeError):
            baselink.encode_cocl_layout([("cannon", 0, 0)], walls=[(0, 44)])

    def test_json_rejects_bad_grid_and_tiles(self):
        bad_grid = json.dumps({"grid": 45, "buildings": []}).encode("utf-8")
        self.assertFalse(baselink.decode_layout_payload(bad_grid).ok)
        bad_tile = json.dumps(
            {"grid": 44, "buildings": [{"type": "cannon", "tile": [44, 0]}]}
        ).encode("utf-8")
        self.assertFalse(baselink.decode_layout_payload(bad_tile).ok)
        missing = json.dumps({"grid": 44}).encode("utf-8")
        self.assertFalse(baselink.decode_layout_payload(missing).ok)


class TestLayoutSchema(unittest.TestCase):
    def test_to_layout_json_schema_exact(self):
        blob = baselink.encode_cocl_layout(COCL_BUILDINGS, COCL_WALLS)
        result = baselink.decode_layout_payload(blob)
        layout = baselink.to_layout_json(result.layout, name="synthetic")
        self.assertEqual(sorted(layout.keys()), ["buildings", "grid", "name", "note", "walls"])
        self.assertEqual(layout["grid"], 44)
        self.assertEqual(layout["name"], "synthetic")
        self.assertEqual(len(layout["buildings"]), len(COCL_BUILDINGS))
        for entry in layout["buildings"]:
            self.assertEqual(sorted(entry.keys()), ["conf", "note", "source", "tile", "type"])
            self.assertEqual(entry["source"], "baselink")
            self.assertEqual(entry["conf"], 1.0)
            self.assertEqual(len(entry["tile"]), 2)
            self.assertTrue(0 <= entry["tile"][0] < 44 and 0 <= entry["tile"][1] < 44)
        self.assertEqual(layout["walls"], [[x, y] for x, y in COCL_WALLS])
        json.dumps(layout)  # 必须可 JSON 序列化

    def test_to_layout_json_matches_existing_layout_schema(self):
        pattern = os.path.join(ROOT, "bases", "th16", "01", "layout.json")
        if not os.path.exists(pattern):
            self.skipTest("bases/th16/01/layout.json 不存在")
        with open(pattern, encoding="utf-8") as fh:
            reference = json.load(fh)
        blob = baselink.encode_cocl_layout(COCL_BUILDINGS, COCL_WALLS)
        layout = baselink.to_layout_json(baselink.decode_layout_payload(blob).layout, name="x")
        self.assertEqual(set(layout.keys()), set(reference.keys()))
        if reference.get("buildings"):
            self.assertEqual(set(layout["buildings"][0].keys()), set(reference["buildings"][0].keys()))

    def test_build_layout_from_link_synthetic(self):
        blob = baselink.encode_cocl_layout(COCL_BUILDINGS, COCL_WALLS)
        url = make_url(b64url(zlib.compress(blob)))
        layout = baselink.build_layout_from_link(url, name="from-link")
        self.assertEqual(layout["name"], "from-link")
        self.assertEqual(len(layout["buildings"]), 3)
        self.assertEqual(layout["buildings"][0]["type"], "town-hall")
        self.assertEqual(layout["buildings"][0]["tile"], [18, 14])

    def test_build_layout_from_real_link_allow_empty(self):
        layout = baselink.build_layout_from_link(REAL_URLS[0])
        self.assertEqual(layout["grid"], 44)
        self.assertEqual(layout["buildings"], [])
        self.assertEqual(layout["walls"], [])
        self.assertIn("无法离线解码", layout["note"])
        with self.assertRaises(baselink.LayoutDecodeError):
            baselink.build_layout_from_link(REAL_URLS[0], allow_empty=False)

    def test_undecodable_layout_name(self):
        link = baselink.parse_link(REAL_URLS[0])
        layout = baselink.undecodable_layout(link, "reason")
        self.assertEqual(layout["note"], "reason")
        self.assertTrue(layout["name"].startswith("baselink_th16_WB_"))
        self.assertEqual(layout["grid"], 44)

    def test_analyze_link_json_serializable(self):
        report = baselink.analyze_link(REAL_URLS[0])
        text = json.dumps(report, ensure_ascii=False)
        self.assertIn("opaque-token-v1", text)
        self.assertEqual(report["link"]["town_hall"], 16)
        self.assertIsNone(report["decoded_layout"])

    def test_analyze_synthetic_link_report(self):
        blob = baselink.encode_cocl_layout(COCL_BUILDINGS, COCL_WALLS)
        report = baselink.analyze_link(make_url(b64url(gzip.compress(blob))))
        self.assertTrue(report["decoded"])
        self.assertEqual(report["codec"], "cocl+gzip")
        self.assertEqual(report["building_count"], 3)
        self.assertEqual(report["wall_count"], 3)
        self.assertEqual(report["decoded_layout"]["buildings"][0], ["town-hall", 18, 14])
        json.dumps(report, ensure_ascii=False)

    def test_known_layout_types_cover_project_inventory(self):
        expected = {
            "air-defense", "air-sweeper", "archer-tower", "bomb-tower", "cannon",
            "clan-castle", "eagle-artillery", "firespitter", "hidden-tesla",
            "inferno-tower", "monolith", "mortar", "ricochet-cannon", "scattershot",
            "spell-tower", "town-hall", "wizard-tower", "x-bow",
        }
        self.assertEqual(set(baselink.KNOWN_LAYOUT_TYPES), expected)
        self.assertEqual(set(baselink.SYNTHETIC_BUILDING_TYPES.values()), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
