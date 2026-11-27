# -*- coding: utf-8 -*-
import unittest
from unittest import mock
from clashlab import cocapi


class T(unittest.TestCase):
    def test_clan_cached_members_th(self):
        fixture = {"name": "X", "tag": "#AAA", "members": [
            {"tag": "#P1", "name": "a", "townHallLevel": 16},
            {"tag": "#P2", "name": "b", "townHallLevel": 15},
            {"tag": "#P3", "name": "c"},
        ]}
        with mock.patch.object(cocapi, "_get", return_value=fixture):
            th = cocapi.cached_members_th("#AAA")
        self.assertEqual(th, {"#P1": 16, "#P2": 15})

    def test_static_names_and_level(self):
        with mock.patch.object(cocapi, "_get", side_effect=[["Barbarian"], {"name": "Town Hall", "max_level": 19}]):
            names = cocapi.static_names("troops")
            lv = cocapi.static_max_level("buildings", "Town Hall")
        self.assertEqual(names, ["Barbarian"])
        self.assertEqual(lv, 19)

    def test_clan_wars_filtered_path(self):
        seen = {}
        def fake(path, ttl=0, fresh=False):
            seen["path"] = path
            return {"items": [{"state": "warEnded"}]}
        with mock.patch.object(cocapi, "_get", side_effect=fake):
            items = cocapi.clan_wars_filtered("#AAA", war_type="cwl", limit=5)
        self.assertEqual(len(items), 1)
        self.assertIn("type=cwl", seen["path"])
        self.assertIn("limit=5", seen["path"])
        self.assertIn("%23AAA", seen["path"])

if __name__ == "__main__":
    unittest.main()
