# -*- coding: utf-8 -*-
import unittest
from unittest import mock
from clashlab import cocapi

class T(unittest.TestCase):
    def test_clan_th_distribution(self):
        with mock.patch.object(cocapi, "cached_members_th", return_value={"#A":16,"#B":16,"#C":15}):
            d = cocapi.clan_th_distribution("#X")
        self.assertEqual(d["dist"], {16:2, 15:1})
        self.assertEqual(d["map"]["#A"], 16)

    def test_resolve_attaches_dist(self):
        with mock.patch.object(cocapi, "_search_player_best", return_value={"name":"x","tag":"#P","th":16,"clan":{"name":"c","tag":"#C"}}), \
             mock.patch.object(cocapi, "search_player", return_value=[]), \
             mock.patch.object(cocapi, "war_members", return_value=None), \
             mock.patch.object(cocapi, "clan_th_distribution", return_value={"map":{"#P":16},"dist":{16:1}}):
            res = cocapi.resolve_opponent("x", "c", fresh=True)
        self.assertEqual(res.get("clan_th_dist"), {16:1})

if __name__ == "__main__":
    unittest.main()
