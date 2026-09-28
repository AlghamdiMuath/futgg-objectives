"""Planner behavior against the checked-in FC 27 interpreted export."""

import copy
import json
import unittest
from pathlib import Path

import plan_objectives as planner
import user_objectives as users


SOURCE = json.loads((Path(__file__).parent / "fc27_interpreted.json").read_text(encoding="utf-8"))
NOW = "2026-09-27T12:30:06Z"


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.state = users.new_state()

    def plan(self, group_ids, modes, excluded=(), cycles=None, source=SOURCE, now=NOW):
        for group_id in group_ids:
            if group_id not in self.state["selections"]:
                users.select(self.state, source, group_id, NOW)
        view = users.selected_view(self.state, source, now, cycles)
        return planner.build_plan(source, view, set(modes), set(excluded))

    def test_identical_squad_battles_win_tiers_share_fifteen_qualifying_matches(self):
        result = self.plan(["94"], ["squad_battles"])
        self.assertEqual(len(result["match_blocks"]), 1)
        block = result["match_blocks"][0]
        self.assertEqual(block["qualifying_matches"], 15)
        self.assertEqual(block["conditions"], [{"type": "result", "value": "win"}])
        self.assertEqual(block["mode_option"]["minimum_difficulty"], "World Class")
        self.assertEqual({item["task_id"] for item in block["tasks"]},
                         {"94:1696", "94:1695", "94:1694"})
        self.assertEqual(result["unscheduled_tasks"], [])

    def test_current_cycle_progress_only_and_excluded_mode_alternative(self):
        users.record_progress(self.state, SOURCE, "65:474", count=4, completed=False,
                              updated_at=NOW, cycle_start_utc="2026-09-24T07:00:00Z")
        old = self.plan(["65"], ["squad_battles", "rivals", "rush"], ["squad_battles"],
                        {"65": "2026-09-24T07:00:00Z"})
        win = next(block for block in old["match_blocks"] if any(t["task_id"] == "65:474" for t in block["tasks"]))
        self.assertEqual(win["qualifying_matches"], 6)
        self.assertEqual(win["mode_option"]["mode"], "rivals")
        new = self.plan(["65"], ["squad_battles", "rivals", "rush"], ["squad_battles"],
                        {"65": "2026-09-25T07:00:00Z"})
        new_win = next(block for block in new["match_blocks"] if any(t["task_id"] == "65:474" for t in block["tasks"]))
        self.assertEqual(new_win["qualifying_matches"], 10)
        self.assertIn("65:472", {t["task_id"] for t in new["unscheduled_tasks"]})
        without_cycle = self.plan(["65"], ["rivals"])
        self.assertEqual(without_cycle["match_blocks"], [])
        self.assertIn("group_cycle_start_required", without_cycle["unscheduled_tasks"][0]["reasons"])

    def test_review_cumulative_and_no_mode_are_reported(self):
        result = self.plan(["25", "113", "58"], ["live_events", "rivals", "squad_battles"])
        reasons = {task["task_id"]: task["reasons"] for task in result["unscheduled_tasks"]}
        self.assertIn("cumulative_vs_single_match_unclear", reasons["25:140"])
        self.assertIn("mode_unspecified", reasons["113:1758"])
        self.assertIn("match_count_not_bounded", reasons["58:270"])
        self.assertEqual(next(t for t in result["unscheduled_tasks"] if t["task_id"] == "58:270")["target"]["count"], 500)

    def test_effective_expiry_conflict_and_source_change_block(self):
        users.select(self.state, SOURCE, "25", NOW)
        users.correct_deadline(self.state, SOURCE, "25", "2026-10-02T17:00:00Z", NOW)
        expired = self.plan(["25"], ["live_events"], now="2026-10-02T17:00:00Z")
        self.assertFalse(expired["match_blocks"])
        self.assertIn("availability_expired", expired["unscheduled_tasks"][0]["reasons"])
        users.correct_deadline(self.state, SOURCE, "25", "2026-10-03T17:00:00Z", NOW)
        conflict = self.plan(["25"], ["live_events"])
        self.assertIn("group_conflicting_user_deadlines", conflict["unscheduled_tasks"][0]["reasons"])
        changed = copy.deepcopy(SOURCE)
        users.select(self.state, changed, "94", NOW)
        task = next(g for g in changed["groups"] if g["id"] == "94")["tasks"][0]
        users.record_progress(self.state, changed, task["id"], count=3, completed=False, updated_at=NOW)
        task["source_fingerprint"] = "changed"
        result = self.plan(["94"], ["squad_battles"], source=changed)
        flagged = next(t for t in result["unscheduled_tasks"] if t["task_id"] == task["id"])
        self.assertIn("source_task_changed", flagged["reasons"])

    def test_parent_mode_exclusion_and_event_separation(self):
        result = self.plan(["25", "82", "83"], ["pve_live_events", "pvp_live_events", "live_events"], ["live_events"])
        self.assertEqual(result["match_blocks"], [])
        self.assertIn("no_permitted_mode", next(t for t in result["unscheduled_tasks"] if t["task_id"] == "25:141")["reasons"])
        result = self.plan(["82", "83"], ["live_events"])
        events = {block["mode_option"]["event"] for block in result["match_blocks"]}
        self.assertGreater(len(events), 1)

    def test_same_live_event_has_one_route_name_but_keeps_distinct_conditions(self):
        result = self.plan(["109"], ["live_events"])
        self.assertEqual({block["mode_option"]["event"] for block in result["match_blocks"]},
                         {"Destined for Glory Exhibition"})
        self.assertGreater(len(result["match_blocks"]), 1)

    def test_daily_progress_requires_explicit_current_cycle(self):
        users.record_progress(self.state, SOURCE, "61:464", count=1, completed=True,
                              updated_at=NOW, cycle_start_utc="2026-09-26T07:00:00Z")
        old = self.plan(["61"], ["rush"], cycles={"61": "2026-09-26T07:00:00Z"},
                        now="2026-09-26T12:30:06Z")
        self.assertIn("61:464", {task["task_id"] for task in old["completed_tasks"]})
        current = self.plan(["61"], ["rush"], cycles={"61": "2026-09-27T07:00:00Z"})
        play = next(block for block in current["match_blocks"] if any(t["task_id"] == "61:464" for t in block["tasks"]))
        self.assertEqual(play["qualifying_matches"], 1)
        self.assertEqual(play["mode_option"]["mode"], "rush")
        future = self.plan(["61"], ["rush"], cycles={"61": "2026-09-28T07:00:00Z"})
        self.assertFalse(future["match_blocks"])
        self.assertIn("cycle_starts_in_future", future["unscheduled_tasks"][0]["reasons"])

    def test_stale_view_is_rejected_and_completed_task_is_not_scheduled(self):
        users.select(self.state, SOURCE, "94", NOW)
        users.record_progress(self.state, SOURCE, "94:1696", count=15, completed=True, updated_at=NOW)
        result = self.plan(["94"], ["squad_battles"])
        self.assertEqual(result["completed_tasks"][0]["task_id"], "94:1696")
        self.assertEqual(result["match_blocks"][0]["qualifying_matches"], 12)
        view = users.selected_view(self.state, SOURCE, NOW)
        view["source_fetched_at"] = "other"
        with self.assertRaisesRegex(ValueError, "different fetches"):
            planner.build_plan(SOURCE, view, {"squad_battles"})


if __name__ == "__main__":
    unittest.main()
