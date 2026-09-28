"""Private-state behavior against representative groups from the checked-in export."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

import user_objectives as layer

SOURCE = json.loads((Path(__file__).parent / "fc27_interpreted.json").read_text(encoding="utf-8"))
NOW = "2026-09-27T12:30:06Z"


class UserObjectivesTests(unittest.TestCase):
    def setUp(self):
        self.state = layer.new_state()

    def test_in_game_deadline_for_null_source_is_effective_and_private(self):
        source = copy.deepcopy(SOURCE)
        layer.select(self.state, source, "25", NOW)
        layer.correct_deadline(self.state, source, "25", "2026-10-02T17:00:00+00:00", NOW)
        selected = layer.selected_view(self.state, source, NOW)["selected_groups"][0]
        self.assertIsNone(source["groups"][next(i for i, g in enumerate(source["groups"]) if g["id"] == "25")]["expires_at"])
        self.assertIsNone(selected["source_expires_at"])
        self.assertEqual(selected["effective_expires_at"], "2026-10-02T17:00:00Z")
        self.assertEqual(selected["deadline_corrections"][0]["source"], "fc27_in_game")
        self.assertEqual(layer.selected_view(self.state, source, "2026-10-02T17:00:00Z")["selected_groups"][0]["availability"], "expired")

    def test_later_source_deadline_and_conflicting_user_entries_are_preserved(self):
        source = copy.deepcopy(SOURCE)
        layer.select(self.state, source, "25", NOW)
        layer.correct_deadline(self.state, source, "25", "2026-10-02T17:00:00Z", NOW)
        later = copy.deepcopy(source)
        group = next(g for g in later["groups"] if g["id"] == "25")
        group["expires_at"] = "2026-10-04T17:00:00Z"
        result = layer.selected_view(self.state, later, NOW)["selected_groups"][0]
        self.assertEqual(result["effective_expires_at"], group["expires_at"])
        self.assertIn("source_deadline_conflict", result["review_flags"])
        self.assertEqual(result["deadline_corrections"][0]["expires_at"], "2026-10-02T17:00:00Z")
        layer.correct_deadline(self.state, source, "25", "2026-10-03T17:00:00Z", "2026-09-28T00:00:00Z")
        result = layer.selected_view(self.state, source, NOW)["selected_groups"][0]
        self.assertIsNone(result["effective_expires_at"])
        self.assertEqual(result["availability"], "needs_review")
        self.assertIn("conflicting_user_deadlines", result["review_flags"])
        self.assertEqual(len(result["deadline_corrections"]), 2)

    def test_unlisted_and_expired_selected_groups(self):
        source = copy.deepcopy(SOURCE)
        layer.select(self.state, source, "25", NOW)
        layer.select(self.state, source, "94", NOW)
        group = next(g for g in source["groups"] if g["id"] == "25")
        source["groups"].remove(group)
        source["removed_groups"].append({"id": "25", "title": group["title"], "expires_at": None, "first_missing_at": NOW})
        result = {g["group_id"]: g for g in layer.selected_view(self.state, source, "2026-10-05T00:00:00Z")["selected_groups"]}
        self.assertEqual(result["25"]["availability"], "unlisted")
        self.assertIn("unlisted_source_group", result["25"]["review_flags"])
        self.assertEqual(result["94"]["availability"], "expired")
        layer.correct_deadline(self.state, source, "25", "2026-10-03T00:00:00Z", NOW)
        self.assertEqual(layer.selected_view(self.state, source, "2026-10-05T00:00:00Z")["selected_groups"][0]["availability"], "expired")

    def test_source_text_change_retains_recorded_text_and_flags_review(self):
        source = copy.deepcopy(SOURCE)
        layer.select(self.state, source, "94", NOW)
        layer.record_progress(self.state, source, "94:1696", count=3, completed=False, updated_at=NOW)
        original = self.state["progress"]["94:1696"]["source_text"]
        changed = copy.deepcopy(source)
        group = next(g for g in changed["groups"] if g["id"] == "94")
        task = next(t for t in group["tasks"] if t["id"] == "94:1696")
        task["source_text"] += " Extra condition."
        task["source_fingerprint"] = "changed"
        group["source_fingerprint"] = "changed"
        layer.record_progress(self.state, changed, "94:1696", count=4, completed=False, updated_at="2026-09-28T00:00:00Z")
        result = layer.selected_view(self.state, changed, NOW)["selected_groups"][0]
        self.assertIn("source_group_changed", result["review_flags"])
        self.assertIn("source_task_changed", result["tasks"][0]["review_flags"])
        self.assertEqual(result["tasks"][0]["progress"]["source_text"], original)
        self.assertEqual(result["tasks"][0]["progress"]["count"], 4)
        group["tasks"] = [t for t in group["tasks"] if t["id"] != "94:1696"]
        missing = layer.selected_view(self.state, changed, NOW)["selected_groups"][0]
        self.assertIn("stored_task_unlisted", missing["review_flags"])
        self.assertEqual(missing["unmatched_progress"][0]["source_text"], original)

    def test_daily_and_weekly_progress_require_explicit_distinct_cycles(self):
        layer.select(self.state, SOURCE, "61", NOW)
        layer.select(self.state, SOURCE, "80", NOW)
        with self.assertRaisesRegex(ValueError, "cycle start"):
            layer.record_progress(self.state, SOURCE, "61:464", count=1, completed=True, updated_at=NOW)
        layer.record_progress(self.state, SOURCE, "61:464", count=1, completed=True, updated_at=NOW,
                              cycle_start_utc="2026-09-27T07:00:00Z")
        layer.record_progress(self.state, SOURCE, "80:718", count=3, completed=False, updated_at=NOW,
                              cycle_start_utc="2026-09-24T07:00:00Z")
        old = {g["group_id"]: g for g in layer.selected_view(self.state, SOURCE, NOW,
                 {"61": "2026-09-27T07:00:00Z", "80": "2026-09-24T07:00:00Z"})["selected_groups"]}
        self.assertTrue(old["61"]["tasks"][0]["progress"]["completed"])
        self.assertEqual(old["80"]["tasks"][0]["progress"]["count"], 3)
        new = {g["group_id"]: g for g in layer.selected_view(self.state, SOURCE, NOW,
                 {"61": "2026-09-28T07:00:00Z", "80": "2026-10-01T07:00:00Z"})["selected_groups"]}
        self.assertIsNone(new["61"]["tasks"][0]["progress"])
        self.assertIsNone(new["80"]["tasks"][0]["progress"])
        self.assertEqual(len(self.state["progress"]), 2)
        self.assertIn("cycle_start_required", layer.selected_view(self.state, SOURCE, NOW)["selected_groups"][0]["review_flags"])

    def test_storage_round_trip_and_invalid_timestamps(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.json"
            layer.select(self.state, SOURCE, "25", NOW)
            layer.save_state(path, self.state)
            self.assertEqual(layer.load_state(path), self.state)
        with self.assertRaisesRegex(ValueError, "UTC"):
            layer.correct_deadline(self.state, SOURCE, "25", "2026-10-02T20:00:00+03:00", NOW)
        with self.assertRaisesRegex(ValueError, "UTC"):
            layer.record_progress(self.state, SOURCE, "94:1696", count=1, completed=False, updated_at="2026-09-27T12:00:00")


if __name__ == "__main__":
    unittest.main()
