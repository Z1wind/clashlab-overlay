# -*- coding: utf-8 -*-
import os, tempfile, unittest
from clashlab import battle_report

LAY = {"name": "t", "buildings": [{"type": "town-hall", "tile": [20, 20]},
                                  {"type": "air-defense", "tile": [16, 16]},
                                  {"type": "cannon", "tile": [24, 24]}], "walls": []}

class T(unittest.TestCase):
    def test_build(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "l.json")
        import json
        json.dump(LAY, open(p, "w"))
        out = os.path.join(d, "r.html")
        r = battle_report.build(p, out_path=out, th=16)
        self.assertTrue(r["ok"])
        self.assertGreater(r["bytes"], 3000)
        t = open(out, encoding="utf-8").read()
        self.assertIn("战报", t)
        self.assertIn("进攻模拟", t)

if __name__ == "__main__":
    unittest.main()
