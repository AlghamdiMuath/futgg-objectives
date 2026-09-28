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
        self.assertTrue(with_modes["snapshot"]["plan"]["match_blocks"])
        third = browser_api.update_json("progress", '{"task_id":"94:1696","count":2,"completed":false}',
            json.dumps(with_modes["state"]), json.dumps(with_modes["settings"]), now)
        saved = json.loads(third)
        roundtrip = json.loads(browser_api.snapshot_json(json.dumps(saved["state"]),
            json.dumps(saved["settings"]), now))
        task = next(t for t in roundtrip["view"]["selected_groups"][0]["tasks"] if t["id"] == "94:1696")
        self.assertEqual(task["progress"]["count"], 2)
        self.assertEqual(roundtrip["plan"]["match_blocks"][0]["qualifying_matches"], 13)

    def test_rejects_progress_before_selection(self):
        with self.assertRaisesRegex(ValueError, "Select the group"):
            browser_api.update_json("progress", '{"task_id":"94:1696","count":1,"completed":false}',
                                    None, None, "2026-09-28T18:30:00Z")


if __name__ == "__main__":
    unittest.main()
