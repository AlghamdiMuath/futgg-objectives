"""Public browser API coverage for daily recommendation behavior."""

import copy
import json
import unittest
from pathlib import Path

import browser_api


SOURCE = json.loads((Path(__file__).parent / "fc27_interpreted.json").read_text(encoding="utf-8"))
NOW = "2026-10-01T12:00:00Z"


def pack_scenario(packs):
    groups = []
    template = next(group for group in SOURCE["groups"] if group["id"] == "109")
    for index, (event, pack) in enumerate(packs, 1):
        group = copy.deepcopy(template)
        group_id = f"pack-test-{index}"
        task = copy.deepcopy(group["tasks"][0])
        group.update({"id": group_id, "title": event, "category": "live-events",
                      "starts_at": None, "expires_at": None, "completion_rewards": [],
                      "source_fingerprint": f"group-{index}", "tasks": [task]})
        task.update({"id": f"{group_id}:1", "source_text": f"Play 1 match in {event} Live Event.",
                     "kind": "match", "status": "parsed", "review_reasons": [],
                     "target": {"unit": "matches", "count": 1, "scope": "separate_matches"},
                     "mode_options": [{"mode": "live_events", "event": event,
                                       "minimum_difficulty": None}],
                     "conditions": [], "rewards": [pack], "source_fingerprint": f"task-{index}"})
        groups.append(group)
    result = copy.deepcopy(SOURCE)
    result["groups"] = groups
    result["removed_groups"] = []
    return result


class DailyPlannerApiTests(unittest.TestCase):
    def recommendations(self, packs):
        browser_api.initialize(json.dumps(pack_scenario(packs)))
        return json.loads(browser_api.snapshot_json(None, None, NOW))["daily_plan"]["recommendations"]

    def test_two_rating_point_pack_gap_overrides_player_count(self):
        recommendations = self.recommendations([
            ("Event A", "2X 84+ Gold Players Pack"),
            ("Event B", "5X 82+ Gold Players Pack"),
        ])
        self.assertEqual(recommendations[0]["route"]["event"], "Event A")

    def test_player_count_wins_when_rating_gap_is_below_two(self):
        recommendations = self.recommendations([
            ("Event A", "5X 82+ Gold Players Pack"),
            ("Event B", "2X 81+ Gold Players Pack"),
        ])
        self.assertEqual(recommendations[0]["route"]["event"], "Event A")

    def test_reward_choice_filters_groups_and_does_not_fill_ten_matches(self):
        browser_api.initialize(json.dumps(pack_scenario([
            ("SP event", "100 SP"),
            ("Pack event", "2X 84+ Gold Players Pack"),
            ("Coin event", "1,000 Coins"),
            ("Other points event", "100 Points"),
        ])))
        settings = {**browser_api.DEFAULT_SETTINGS, "reward_priority": "season_points"}
        plan = json.loads(browser_api.snapshot_json(None, json.dumps(settings), NOW))["daily_plan"]
        self.assertEqual([recipe["route"]["event"] for recipe in plan["recommendations"]],
                         ["SP event"])
        self.assertFalse(plan["has_more"])

        settings["reward_priority"] = "balanced"
        all_rewards = json.loads(browser_api.snapshot_json(None, json.dumps(settings), NOW))["daily_plan"]
        self.assertEqual(len(all_rewards["recommendations"]), 4)

    def test_cumulative_goal_target_suggests_one_match_at_a_time(self):
        scenario = pack_scenario([("Goals event", "100 SP")])
        task = scenario["groups"][0]["tasks"][0]
        task["source_text"] = "Score 20 goals in Goals event Live Event."
        task["target"] = {"unit": "goals", "count": 20, "scope": "cumulative"}
        task["conditions"] = []
        browser_api.initialize(json.dumps(scenario))
        settings = {**browser_api.DEFAULT_SETTINGS, "reward_priority": "season_points"}
        plan = json.loads(browser_api.snapshot_json(None, json.dumps(settings), NOW))["daily_plan"]
        self.assertEqual(len(plan["recommendations"]), 1)

    def test_group_completion_reward_counts_for_reward_choice(self):
        scenario = pack_scenario([("Group SP event", "2X 84+ Gold Players Pack")])
        scenario["groups"][0]["completion_rewards"] = ["100 SP"]
        browser_api.initialize(json.dumps(scenario))
        settings = {**browser_api.DEFAULT_SETTINGS, "reward_priority": "season_points"}
        plan = json.loads(browser_api.snapshot_json(None, json.dumps(settings), NOW))["daily_plan"]
        self.assertEqual(len(plan["recommendations"]), 1)


if __name__ == "__main__":
    unittest.main()
