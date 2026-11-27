# -*- coding: utf-8 -*-
import json, os, tempfile, unittest
from tools.labels_to_layout import convert

class T(unittest.TestCase):
    def test_convert(self):
        d = tempfile.mkdtemp()
        lp = os.path.join(d, "l.json")
        json.dump({"quad": [[0,0],[1,0],[1,1],[0,1]], "items": [
            {"image": "x.png", "tile": [5, 5], "size": 3, "type": "inferno-tower"},
            {"image": "x.png", "tile": [9, 9], "size": 2, "type": "__bg__"},
        ]}, open(lp, "w"))
        out = os.path.join(d, "layout.json")
        r = convert(lp, "t", out)
        self.assertEqual(r["buildings"], 1)
        lay = json.load(open(out))
        self.assertEqual(lay["buildings"][0]["type"], "inferno-tower")

if __name__ == "__main__":
    unittest.main()
