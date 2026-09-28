"""Planner behavior against the checked-in FC 27 interpreted export."""

import copy
import json
import unittest
from pathlib import Path

import plan_objectives as planner
from optimize_matches import combine_tasks
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

    def test_verified_implicit_mode_is_planned_and_other_reviews_are_reported(self):
        result = self.plan(["25", "113", "58"], ["live_events", "rivals", "squad_battles"])
        reasons = {task["task_id"]: task["reasons"] for task in result["unscheduled_tasks"]}
        self.assertIn("cumulative_vs_single_match_unclear", reasons["25:140"])
        self.assertNotIn("113:1758", reasons)
        self.assertIn("113:1758", {task["task_id"] for run in result["combined_plan"]["runs"]
                                    for task in run["match_tasks"]})
        self.assertIn("match_count_not_bounded", reasons["58:270"])
        self.assertEqual(next(t for t in result["unscheduled_tasks"] if t["task_id"] == "58:270")["target"]["count"], 500)

    def test_fc_pro_ladder_waits_for_confirmed_division_five_gate(self):
        blocked = self.plan(["108"], ["fc_pro_open_ladder"])
        ladder = next(task for task in blocked["unscheduled_tasks"] if task["task_id"] == "108:1734")
        self.assertIn("prerequisite_incomplete:108:1733", ladder["reasons"])
        users.record_progress(self.state, SOURCE, "108:1733", count=5, completed=True, updated_at=NOW)
        ready = self.plan(["108"], ["fc_pro_open_ladder"])
        block = next(block for block in ready["match_blocks"] if block["tasks"][0]["task_id"] == "108:1734")
        self.assertEqual(block["qualifying_matches"], 5)

    def test_rush_point_ladder_shares_the_highest_recorded_weekly_count(self):
        users.select(self.state, SOURCE, "72", NOW)
        cycle = "2026-09-24T07:00:00Z"
        users.record_progress(self.state, SOURCE, "72:510", count=35000, completed=True,
                              updated_at=NOW, cycle_start_utc=cycle)
        view = users.selected_view(self.state, SOURCE, NOW, {"72": cycle})
        tasks = view["selected_groups"][0]["tasks"]
        self.assertTrue(all(task["progress"]["count"] == 35000 and task["progress"]["completed"]
                            for task in tasks))

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
        self.assertEqual(result["combined_plan"]["qualifying_match_count"], 7)
        self.assertEqual(len(result["combined_plan"]["runs"]), 1)
        self.assertEqual(len(result["combined_plan"]["runs"][0]["cumulative_targets"]), 2)

    def test_same_event_conditions_share_thirty_matches(self):
        result = self.plan(["88"], ["live_events"])
        combined = result["combined_plan"]
        self.assertEqual(combined["qualifying_match_count"], 30)
        self.assertEqual(len(combined["runs"]), 1)
        self.assertEqual(len(combined["runs"][0]["match_tasks"]), 7)

    def test_combined_runs_cover_every_playable_task_and_account_for_cumulative_targets(self):
        # The phone Plan uses combined runs as its sole task list. Every bounded
        # condition must still be reachable after removing the old detail cards.
        result = self.plan(["82", "83", "84", "85"], ["live_events"])
        bounded = {task["task_id"] for block in result["match_blocks"] for task in block["tasks"]}
        runs = result["combined_plan"]["runs"]
        displayed = [task["task_id"] for run in runs for task in run["match_tasks"]]
        self.assertEqual(set(displayed), bounded)
        self.assertEqual(len(displayed), len(bounded))
        cumulative = {task["task_id"] for task in result["unscheduled_tasks"]
                      if task["reasons"] == ["match_count_not_bounded"]}
        attached = {task["task_id"] for run in runs for task in run["cumulative_targets"]}
        unattached = set(result["combined_plan"]["cumulative_without_run"])
        self.assertEqual(attached | unattached, cumulative)
        self.assertEqual(result["combined_plan"]["qualifying_match_count"],
                         sum(run["qualifying_matches"] for run in runs))

    def test_selected_groups_share_mode_and_any_fut_targets(self):
        result = self.plan(["94", "65"], ["squad_battles"], cycles={"65": "2026-09-24T07:00:00Z"})
        runs = result["combined_plan"]["runs"]
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["qualifying_matches"], 15)
        self.assertEqual(set(runs[0]["group_ids"]), {"94", "65"})
        self.assertIn("65:475", {task["task_id"] for task in runs[0]["cumulative_targets"]})

    def test_first_owned_full_squad_requirement_remains_usable(self):
        result = self.plan(["59"], ["squad_battles"])
        run = result["combined_plan"]["runs"][0]
        self.assertEqual(run["qualifying_matches"], 100)
        self.assertEqual(run["squad_requirements"],
                         [{"slot": "starting_squad", "trait": "First Owned players", "minimum": "all"}])

    def test_two_challenge_example_has_one_ten_match_run_and_squad(self):
        route = {"mode": "squad_battles", "event": None, "minimum_difficulty": None}
        def task(group, identifier, remaining, conditions=(), cumulative=False):
            return {"group_id": group, "task_id": identifier, "source_text": identifier,
                    "target": {"unit": "goals", "scope": "cumulative", "count": remaining} if cumulative else None,
                    "remaining": remaining, "conditions": list(conditions), "options": [route]}
        separate = [task("a", "play ten", 10),
                    task("b", "play five with Spanish starters", 5,
                         [{"type": "squad", "minimum": 2, "trait": "Spanish players", "slot": "starting_11"}])]
        cumulative = [task("a", "score ten", 10, cumulative=True),
                      task("a", "assist ten", 10, cumulative=True),
                      task("b", "Spanish goals", 5, [{"type": "scoring_player", "trait": "Spanish"}], True),
                      task("b", "English winger goals", 5, [{"type": "scoring_player", "trait": "English winger"}], True),
                      task("b", "Argentinian assists", 10, [{"type": "assisting_player", "trait": "Argentinian"}], True)]
        result = combine_tasks(separate, cumulative)
        self.assertEqual(result["qualifying_match_count"], 10)
        self.assertEqual(len(result["runs"]), 1)
        self.assertEqual(len(result["runs"][0]["cumulative_targets"]), 5)
        self.assertEqual(result["runs"][0]["squad_requirements"],
                         [{"slot": "starting_11", "trait": "Spanish players", "minimum": 2}])
        self.assertEqual({role["trait"] for role in result["runs"][0]["player_roles"]},
                         {"Spanish", "English winger", "Argentinian"})
        self.assertEqual(result["runs"][0]["route_options"], [route])

    def test_unverified_card_overlap_is_planned_as_an_optional_lineup_optimization(self):
        route = {"mode": "squad_battles", "event": None, "minimum_difficulty": None}
        tasks = [
            {"group_id": "a", "task_id": "spanish eleven", "source_text": "spanish eleven",
             "remaining": 10, "conditions": [{"type": "squad", "minimum": 11,
                                                "trait": "Spanish players", "slot": "starting_11"}],
             "options": [route]},
            {"group_id": "b", "task_id": "english scorer", "source_text": "english scorer",
             "remaining": 5, "conditions": [{"type": "scoring_player", "trait": "English winger"}],
             "options": [route]},
        ]
        result = combine_tasks(tasks, [])
        self.assertEqual(result["qualifying_match_count"], 10)
        self.assertEqual([run["qualifying_matches"] for run in result["runs"]], [10])

    def test_equally_qualifying_routes_are_exposed_for_the_player_to_choose(self):
        squad = {"mode": "squad_battles", "event": None, "minimum_difficulty": "Semi-Pro"}
        rivals = {"mode": "rivals", "event": None, "minimum_difficulty": None}
        task = {"group_id": "a", "task_id": "choose a route", "source_text": "Win 3 matches",
                "remaining": 3, "conditions": [{"type": "result", "value": "win"}],
                "options": [squad, rivals]}
        result = combine_tasks([task], [])
        self.assertEqual(result["qualifying_match_count"], 3)
        self.assertEqual(result["runs"][0]["route_options"], [rivals, squad])

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
