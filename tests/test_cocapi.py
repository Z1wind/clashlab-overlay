# -*- coding: utf-8 -*-
"""cocapi 解析测试（离线 mock，不发请求）。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PLAYER_ITEMS = [
    {"attackerTag": "#AAA", "attackerName": "a", "defenderTag": "#QCRJPL2RJ", "defenderName": "z",
     "attackerTownhall": 15, "defenderTownhall": 16, "stars": 3, "destructionPercentage": 100},
    {"attackerTag": "#QCRJPL2RJ", "attackerName": "z", "defenderTag": "#BBB", "defenderName": "b",
     "attackerTownhall": 16, "defenderTownhall": 14, "stars": 2, "destructionPercentage": 80},
]
WAR = {"state": "inWar", "teamSize": 20, "startTime": "a", "endTime": "b",
       "clan": {"tag": "#C1", "members": [{"tag": "#P1", "name": "x", "townhallLevel": 16, "mapPosition": 1}]},
       "opponent": {"tag": "#C2", "members": [{"tag": "#P2", "name": "y", "townhallLevel": 15, "mapPosition": 2},
                                             {"tag": "#P3", "name": "z", "townhallLevel": 14, "mapPosition": 3}]}}


class TestCocapi(unittest.TestCase):
    def test_player_th_from_defense(self):
        from clashlab import cocapi
        cocapi._cache.clear()
        cocapi.player_war_attacks = lambda tag: PLAYER_ITEMS
        self.assertEqual(cocapi.player_th("#QCRJPL2RJ"), 16)

    def test_player_th_unknown(self):
        from clashlab import cocapi
        cocapi.player_war_attacks = lambda tag: []
        self.assertIsNone(cocapi.player_th("#NONE"))

    def test_enemy_th_map(self):
        from clashlab import cocapi
        cocapi.clan_wars = lambda tag: [WAR]
        self.assertEqual(cocapi.enemy_th_map("#C1"), {"#P2": 15, "#P3": 14})

    def test_war_members_shape(self):
        from clashlab import cocapi
        cocapi.clan_wars = lambda tag: [WAR]
        w = cocapi.war_members("#C1")
        self.assertEqual(w["state"], "inWar")
        self.assertEqual(len(w["opponent"]["members"]), 2)

    def test_apply_th_levels(self):
        from clashlab import cocapi
        lay = {"buildings": [{"type": "cannon", "tile": [3, 3]},
                             {"type": "ghost-tower", "tile": [4, 4]}]}
        res = cocapi.apply_th_levels(lay, 16)
        self.assertGreaterEqual(res["updated"], 1)
        self.assertEqual(res["skipped"], 1)
        self.assertGreater(lay["buildings"][0]["level"], 1)

    def test_enc_accepts_hash_or_plain(self):
        from clashlab import cocapi
        self.assertEqual(cocapi._enc("QCRJPL2RJ"), cocapi._enc("#QCRJPL2RJ"))


if __name__ == "__main__":
    unittest.main()
