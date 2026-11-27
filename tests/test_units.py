# -*- coding: utf-8 -*-
import unittest
from clashlab import units

class T(unittest.TestCase):
    def test_troop_fields(self):
        for t in units.troop_list():
            for k in ("id", "zh", "en", "dps", "hp", "house", "role", "color", "glyph"):
                self.assertIn(k, t)
            self.assertGreaterEqual(t["hp"], 0)
            self.assertLessEqual(len(t["glyph"]), 2)

    def test_spell_fields(self):
        for s in units.spell_list():
            for k in ("id", "zh", "en", "radius", "duration", "use", "color", "glyph"):
                self.assertIn(k, s)

    def test_army_totals(self):
        army = {"miner": 2, "healer": 1}
        self.assertEqual(units.army_dps(army), 260)
        self.assertEqual(units.army_hp(army), 4400)

if __name__ == "__main__":
    unittest.main()
