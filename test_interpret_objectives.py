"""Behavior checks using task IDs and descriptions from the verified FC 27 export."""

import copy
import json
import unittest
from pathlib import Path

import interpret_objectives as layer


RAW = json.loads((Path(__file__).parent / "fc27_objectives.json").read_text(encoding="utf-8"))


class InterpretationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.groups = {g["id"]: g for g in layer.interpret_export(RAW)["groups"]}
        cls.tasks = {t["id"]: t for g in cls.groups.values() for t in g["tasks"]}

    def test_real_export_is_accounted_for_and_source_text_is_preserved(self):
        self.assertEqual(len(self.groups), 43)
        self.assertEqual(len(self.tasks), 162)
        source = {t["id"]: t["description"] for g in RAW["groups"] for t in g["tasks"]}
        self.assertEqual({tid: t["source_text"] for tid, t in self.tasks.items()}, source)
        self.assertTrue(all(t["kind"] == "match" or t["kind"] == "dependency" or t["kind"] == "checklist" for t in self.tasks.values()))

    def test_alternative_modes_keep_difficulty_on_squad_battles_only(self):
        task = self.tasks["65:474"]
        self.assertEqual(task["target"], {"unit": "matches", "count": 10, "scope": "separate_matches"})
        self.assertIn({"type": "result", "value": "win"}, task["conditions"])
        options = task["mode_options"]
        self.assertEqual([o["mode"] for o in options], ["squad_battles", "rivals", "champions", "live_events", "rush"])
        self.assertEqual([o["minimum_difficulty"] for o in options], ["Semi-Pro", None, None, None, None])
        remaining = layer.eligible_mode_options(options, {"squad_battles", "rivals"}, {o["mode"] for o in options})
        self.assertEqual([o["mode"] for o in remaining], ["champions", "live_events", "rush"])
        self.assertEqual([o["mode"] for o in self.tasks["25:141"]["mode_options"]], ["pve_live_events", "pvp_live_events"])

    def test_any_fut_expands_only_to_available_nonexcluded_modes(self):
        options = self.tasks["113:1759"]["mode_options"]
        self.assertEqual([o["mode"] for o in layer.eligible_mode_options(options, {"squad_battles"}, {"rivals", "squad_battles", "rush"})], ["rivals", "rush"])

    def test_separate_matches_and_player_squad_conditions(self):
        task = self.tasks["82:726"]
        self.assertEqual(task["target"], {"unit": "matches", "count": 3, "scope": "separate_matches"})
        self.assertEqual(task["conditions"][:2], [{"type": "goals", "minimum_per_match": 2}, {"type": "goal_style", "value": "Finesse"}])
        self.assertEqual(self.tasks["109:1739"]["conditions"][1], {"type": "squad", "minimum": 1, "trait": "Destined for Glory player", "slot": "starting_11"})
        self.assertEqual(len([c for c in self.tasks["98:1709"]["conditions"] if c["type"] == "squad"]), 2)
        self.assertEqual(self.tasks["59:275"]["conditions"][1]["minimum"], "all")

    def test_player_scoring_and_assisting_roles_in_cumulative_tasks(self):
        examples = (
            ("Score 5 goals by a Spanish player in any FUT game mode.", "scoring_player", "Spanish"),
            ("Score 5 goals by an English winger in any FUT game mode.", "scoring_player", "English winger"),
            ("Assist 10 goals by an Argentinian player in any FUT game mode.", "assisting_player", "Argentinian"),
        )
        for text, role, trait in examples:
            target, _ = layer.parse_match_target(text)
            self.assertEqual(target["scope"], "cumulative")
            self.assertIn({"type": role, "trait": trait, "must_start": True}, layer.parse_conditions(text))

    def test_match_count_and_squad_clauses_do_not_become_event_names(self):
        for group_id, expected in (("109", "Destined for Glory Exhibition"),
                                   ("88", "Season 1: Ones to Watch Exhibition"),
                                   ("82", "Ones We Watched World Class Challenge"),
                                   ("86", "Ones We Watched Professional Challenge")):
            events = {option["event"] for task in self.groups[group_id]["tasks"]
                      for option in task["mode_options"] if option["event"]}
            self.assertEqual(events, {expected})

    def test_cumulative_checklist_and_dependencies(self):
        self.assertEqual(self.tasks["58:270"]["target"], {"unit": "goals", "count": 500, "scope": "cumulative"})
        self.assertEqual(self.tasks["42:205"]["target"], {"unit": "matches", "count": 15, "scope": "separate_matches"})
        self.assertEqual(self.tasks["123:1809"]["kind"], "checklist")
        self.assertEqual(self.tasks["72:510"]["target"]["count"], 35000)
        self.assertEqual(self.tasks["28:152"]["dependency"]["group_id"], "27")
        self.assertEqual(self.tasks["79:716"]["dependency"], {"group_id": "80", "group_title": "Season 1: Ones to Watch Exhibition Weekly Play", "completions": 4, "distinct_periods": True})

    def test_ambiguity_and_period_identity(self):
        self.assertEqual(self.tasks["113:1758"]["status"], "parsed")
        self.assertEqual(self.tasks["113:1758"]["mode_options"], [{"mode": "any_fut", "event": None, "minimum_difficulty": None}])
        self.assertIn({"type": "scoring_player", "trait": "Preferred Position: LM", "must_start": True},
                      self.tasks["113:1758"]["conditions"])
        self.assertIn("cumulative_vs_single_match_unclear", self.tasks["25:140"]["review_reasons"])
        self.assertEqual(self.tasks["108:1734"]["prerequisites"], [{"task_id": "108:1733", "relation": "access_qualification", "status": "confirmed"}])
        repeat = self.groups["61"]["repeat"]
        self.assertEqual(repeat["cadence"], "daily")
        self.assertIsNone(repeat["reset_schedule"])
        with self.assertRaisesRegex(ValueError, "cycle start"):
            layer.progress_key("61:464", None, repeat)
        self.assertNotEqual(layer.progress_key("61:464", "2026-09-27T07:00:00Z", repeat), layer.progress_key("61:464", "2026-09-28T07:00:00Z", repeat))
        self.assertEqual(layer.progress_key("94:1696", None, self.groups["94"]["repeat"]), "94:1696")

    def test_omitted_mode_on_a_parsed_match_task_means_any_fut_mode(self):
        task = {"id": "example:1", "title": "Example",
                "description": "Score in 2 separate matches using a French player.", "rewards": []}
        interpreted = layer.interpret_task(task, {"id": "example"}, {})
        self.assertEqual(interpreted["status"], "parsed")
        self.assertEqual(interpreted["mode_options"],
                         [{"mode": "any_fut", "event": None, "minimum_difficulty": None}])

    def test_changed_text_deadline_and_unlisting_are_reported(self):
        new = copy.deepcopy(RAW)
        new["fetched_at"] = "2099-01-01T00:00:00Z"
        self.assertEqual(layer.changes(RAW, new), [])
        new["groups"][0]["expires_at"] = "2026-10-05T06:59:59Z"
        new["groups"][0]["tasks"][0]["description"] += " Extra condition."
        report = layer.changes(RAW, new)
        self.assertEqual(report, [{"group_id": "94", "change": "updated", "fields": ["expires_at"], "task_ids": ["94:1696"]}])
        new["groups"] = [g for g in new["groups"] if g["id"] != "94"]
        self.assertIn({"group_id": "94", "change": "removed"}, layer.changes(RAW, new))


if __name__ == "__main__":
    unittest.main()
