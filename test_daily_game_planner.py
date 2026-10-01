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


if __name__ == "__main__":
    unittest.main()
