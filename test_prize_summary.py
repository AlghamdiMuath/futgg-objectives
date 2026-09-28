"""Reward summaries must use only labels present in the export."""

import json
import unittest
from pathlib import Path

from prize_summary import summarize


GROUPS = {g["id"]: g for g in json.loads(
    (Path(__file__).parent / "fc27_interpreted.json").read_text(encoding="utf-8"))["groups"]}


class PrizeSummaryTests(unittest.TestCase):
    def test_player_name_has_no_invented_rating(self):
        prize = summarize(GROUPS["113"])
        self.assertEqual(prize["main"], {"kind": "player", "label": "Shunsuke Mito", "rating": None})
        self.assertIsNone(prize["rating"])
        self.assertEqual(prize["pack_quality"], {"minimum_rating": 83, "player_count": 4})

    def test_coin_amount_and_pack_quality_from_completion_labels(self):
        coins = summarize(GROUPS["123"])
        self.assertEqual(coins["main"]["label"], "1,000 Coins")
        self.assertEqual(coins["coins"], 1250)
        pack = summarize(GROUPS["72"])
        self.assertEqual(pack["pack_quality"], {"minimum_rating": 84, "player_count": 2})
        self.assertEqual(pack["best_pack_label"], "2X 84+ Gold Players Pack")

    def test_unrated_pack_stays_unranked(self):
        prize = summarize(GROUPS["90"])
        self.assertEqual(prize["main"]["kind"], "pack")
        self.assertIsNone(prize["pack_quality"])

    def test_listed_rewards_make_other_prizes_visible_without_summing(self):
        prize = summarize(GROUPS["87"])
        self.assertEqual(prize["main"]["label"], "Savinho")
        self.assertEqual(prize["coins"], 16000)
        self.assertTrue(prize["has_player"])
        self.assertEqual(summarize(GROUPS["52"])["coins"], 50000)

    def test_players_listed_outside_completion_prize_are_named(self):
        gallery = summarize(GROUPS["81"])
        self.assertEqual(gallery["main"]["label"], "Evo Unlock")
        self.assertTrue(gallery["has_player"])
        self.assertEqual(gallery["other_players"], ["Jesús Corona"])
        self.assertEqual(summarize(GROUPS["25"])["other_players"], ["Victor Lindelöf"])
        self.assertEqual(summarize(GROUPS["113"])["other_players"], [])

    def test_pack_count_distinguishes_pack_quantity_from_players_per_pack(self):
        single = summarize({"completion_rewards": [], "available_rewards": ["3 x 75+ Gold Player Pack"]})
        self.assertEqual(single["pack_quality"], {"minimum_rating": 75, "player_count": 1})
        four = summarize({"completion_rewards": [], "available_rewards": ["1 x 4x 83+ Gold Players Pack"]})
        self.assertEqual(four["pack_quality"], {"minimum_rating": 83, "player_count": 4})

    def test_missing_prize_is_unknown(self):
        self.assertEqual(summarize({"completion_rewards": []})["main"],
                         {"kind": "unknown", "label": "Unknown"})


if __name__ == "__main__":
    unittest.main()
