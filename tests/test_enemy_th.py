# -*- coding: utf-8 -*-
import unittest
from unittest import mock
from clashlab import cocapi

WAR = {"state": "warEnded", "team_size": 15,
       "opponent": {"tag": "#OPP", "members": [{"tag": "#P1", "name": "a", "th": 15, "pos": 1}]}}

class T(unittest.TestCase):
    def test_enemy_th_prefers_cached(self):
        with mock.patch.object(cocapi, "war_members", return_value=WAR), \
             mock.patch.object(cocapi, "cached_members_th", return_value={"#P1": 16, "#P2": 14}):
            th = cocapi.enemy_th_map("#MY")
        self.assertEqual(th["#P1"], 16)   # cached 覆盖战争里的旧值
        self.assertEqual(th["#P2"], 14)

    def test_enemy_th_fallback_to_war(self):
        with mock.patch.object(cocapi, "war_members", return_value=WAR), \
             mock.patch.object(cocapi, "cached_members_th", return_value={}):
            th = cocapi.enemy_th_map("#MY")
        self.assertEqual(th, {"#P1": 15})

if __name__ == "__main__":
    unittest.main()
