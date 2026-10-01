"""Browser storage adapter keeps the planner's existing behavior."""

import json
import unittest
from pathlib import Path

import browser_api


class BrowserApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = (Path(__file__).parent / "fc27_interpreted.json").read_text(encoding="utf-8")
        browser_api.initialize(source)

    def test_private_progress_survives_snapshot_roundtrip(self):
        now = "2026-09-28T18:30:00Z"
        first = browser_api.update_json("select", '{"group_id":"94","selected":true}', None, None, now)
        selected = json.loads(first)
        self.assertEqual(selected["snapshot"]["view"]["selected_groups"][0]["group_id"], "94")
        second = browser_api.update_json("settings", json.dumps({"available_modes": ["squad_battles"],
            "excluded_modes": [], "cycles": {}}), json.dumps(selected["state"]),
            json.dumps(selected["settings"]), now)
        with_modes = json.loads(second)
        self.assertTrue(with_modes["snapshot"]["daily_plan"]["recommendations"])
        third = browser_api.update_json("progress", '{"task_id":"94:1696","count":2,"completed":false}',
            json.dumps(with_modes["state"]), json.dumps(with_modes["settings"]), now)
        saved = json.loads(third)
        roundtrip = json.loads(browser_api.snapshot_json(json.dumps(saved["state"]),
            json.dumps(saved["settings"]), now))
        task = next(t for t in roundtrip["view"]["selected_groups"][0]["tasks"] if t["id"] == "94:1696")
        self.assertEqual(task["progress"]["count"], 2)
        self.assertTrue(roundtrip["daily_plan"]["recommendations"])
        self.assertNotIn("plan", roundtrip)

    def test_rejects_progress_before_selection(self):
        with self.assertRaisesRegex(ValueError, "Select the group"):
            browser_api.update_json("progress", '{"task_id":"94:1696","count":1,"completed":false}',
                                    None, None, "2026-09-28T18:30:00Z")

    def test_match_checkin_updates_multiple_tasks_atomically(self):
        now = "2026-09-28T18:30:00Z"
        selected = json.loads(browser_api.update_json("select", '{"group_id":"94","selected":true}',
                                                       None, None, now))
        checked_in = json.loads(browser_api.update_json("progress_batch", json.dumps({"entries": [
            {"task_id": "94:1696", "count": 1, "completed": False},
            {"task_id": "94:1695", "count": 2, "completed": False}]}),
            json.dumps(selected["state"]), json.dumps(selected["settings"]), now))
        saved = {task["id"]: task["progress"] for task in
                 checked_in["snapshot"]["view"]["selected_groups"][0]["tasks"]}
        self.assertEqual(saved["94:1696"]["count"], 1)
        self.assertEqual(saved["94:1695"]["count"], 2)

        with self.assertRaises(ValueError):
            browser_api.update_json("progress_batch", json.dumps({"entries": [
                {"task_id": "94:1696", "count": 3, "completed": False},
                {"task_id": "94:1695", "count": -1, "completed": False}]}),
                json.dumps(checked_in["state"]), json.dumps(checked_in["settings"]), now)
        unchanged = json.loads(browser_api.snapshot_json(json.dumps(checked_in["state"]),
                                                         json.dumps(checked_in["settings"]), now))
        values = {task["id"]: task["progress"]["count"] for task in
                  unchanged["view"]["selected_groups"][0]["tasks"] if task["progress"]}
        self.assertEqual(values, {"94:1696": 1, "94:1695": 2})

    def test_daily_landing_builds_ten_recipes_without_selecting_challenges(self):
        now = "2026-10-01T12:00:00Z"
        snapshot = json.loads(browser_api.snapshot_json(None, None, now))
        planner = snapshot["daily_plan"]
        categories = {group["id"]: group["category"].casefold() for group in snapshot["groups"]}
        self.assertEqual(len(planner["recommendations"]), 10)
        self.assertEqual(snapshot["view"]["selected_groups"], [])
        self.assertFalse(any(categories[item["group_id"]] in {"milestones", "mastery"}
                             for recipe in planner["recommendations"]
                             for item in recipe["objectives"]))

    def test_daily_batch_checkin_records_progress_and_generates_the_next_batch(self):
        now = "2026-10-01T12:00:00Z"
        result = json.loads(browser_api.update_json("daily_done", "{}", None, None, now))
        self.assertEqual(len(result["snapshot"]["daily_plan"]["recommendations"]), 10)
        self.assertTrue(result["state"]["progress"])
        self.assertEqual(result["snapshot"]["view"]["selected_groups"], [])

    def test_excluding_every_mode_leaves_no_filler_recommendations(self):
        now = "2026-10-01T12:00:00Z"
        snapshot = json.loads(browser_api.snapshot_json(None, None, now))
        all_modes = snapshot["mode_catalog"]
        updated = json.loads(browser_api.update_json("settings", json.dumps({
            "available_modes": [], "excluded_modes": all_modes, "reward_priority": "balanced"}),
            None, None, now))
        self.assertEqual(updated["snapshot"]["daily_plan"]["recommendations"], [])
        self.assertFalse(updated["snapshot"]["daily_plan"]["has_more"])


if __name__ == "__main__":
    unittest.main()
