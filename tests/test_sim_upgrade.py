# -*- coding: utf-8 -*-
import unittest
from clashlab.battle_sim import simulate

ARMY = {"miner": 21, "hog-rider": 11, "healer": 4}
LAY = {"buildings": [{"type": "town-hall", "tile": [20, 20]},
                     {"type": "cannon", "tile": [14, 14]},
                     {"type": "scattershot", "tile": [24, 16]}], "walls": []}

class T(unittest.TestCase):
    def test_spells_and_heroes_help(self):
        base = simulate(LAY, ARMY, th=16)
        buffed = simulate(LAY, ARMY, th=16, heroes=["queen", "king"],
                          spells={"rage": 2, "heal": 2, "freeze": 2})
        self.assertTrue(base["ok"] and buffed["ok"])
        self.assertGreater(buffed["army_dps"], base["army_dps"])
        self.assertGreaterEqual(buffed["survival"], base["survival"])
        self.assertLessEqual(buffed["th_ttk_s"], base["th_ttk_s"])

    def test_th_scaling(self):
        low = simulate(LAY, ARMY, th=12)
        high = simulate(LAY, ARMY, th=16)
        self.assertGreater(high["army_dps"], low["army_dps"])
        self.assertLessEqual(high["th_ttk_s"], low["th_ttk_s"])

    def test_cc_and_modifiers_present(self):
        r = simulate(LAY, ARMY, th=16, cc_dps=300, spells={"jump": 1})
        self.assertIn("modifiers", r)
        self.assertEqual(r["modifiers"]["cc_dps"], 300.0)
        self.assertGreater(r["exposure_dps"], simulate(LAY, ARMY, th=16)["exposure_dps"])

if __name__ == "__main__":
    unittest.main()
