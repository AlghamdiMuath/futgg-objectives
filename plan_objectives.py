#!/usr/bin/env python3
"""Build a conditional match plan from interpreted objectives and a selected view."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from interpret_objectives import eligible_mode_options
from optimize_matches import combine_tasks
from user_objectives import load_state, selected_view, utc


def build_plan(interpreted: dict, view: dict, available_modes: set[str],
               excluded_modes: set[str] | None = None) -> dict:
    """Return finite qualifying-match blocks, unscheduled tasks, and completed tasks.

    Counts are qualifying outcomes, not a prediction of attempts or elapsed time.
    Only tasks in the same group with identical chosen route and conditions share
    a block. Cumulative targets have no known finite match count.
    """
    if interpreted.get("schema_version") != 1 or view.get("schema_version") != 1:
        raise ValueError("Expected interpreted export and selected view schema version 1")
    if view["source_fetched_at"] != interpreted["source_fetched_at"]:
        raise ValueError("Selected view and interpreted export come from different fetches")
    excluded = set(excluded_modes or ())
    modes = set(available_modes)
    if not all(isinstance(mode, str) and mode for mode in modes | excluded):
        raise ValueError("Mode names must be nonempty strings")
    as_of = utc(view["as_of"])
    groups = {group["id"]: group for group in interpreted["groups"]}
    blocks: dict[str, dict] = {}
    unscheduled = []
    completed = []
    unavailable_groups = []
    separate_tasks = []
    cumulative_tasks = []

    for selected in view["selected_groups"]:
        group_id = selected["group_id"]
        group = groups.get(group_id)
        group_flags = selected["review_flags"]
        state_tasks = {item["id"]: item for item in selected["tasks"]}
        if group is None:
            unavailable_groups.append({"group_id": group_id, "title": selected["title"],
                                       "availability": selected["availability"],
                                       "review_flags": group_flags})
        for state_task in selected["tasks"]:
            task_id = state_task["id"]
            task = next((item for item in group["tasks"] if item["id"] == task_id), None) if group else None
            if task is None:
                unscheduled.append(_unscheduled(selected, state_task, None, ["source_task_missing"]))
                continue
            progress = state_task["progress"]
            reasons = []
            for prerequisite in task.get("prerequisites", []):
                if prerequisite.get("status") != "confirmed":
                    continue
                prerequisite_progress = state_tasks.get(prerequisite["task_id"], {}).get("progress")
                if not prerequisite_progress or not prerequisite_progress["completed"]:
                    reasons.append("prerequisite_incomplete:" + prerequisite["task_id"])
            if (progress and progress["completed"] and task["status"] == "parsed"
                    and not state_task["review_flags"] and not group_flags and not reasons):
                completed.append({"group_id": group_id, "task_id": task_id,
                                  "progress_key": state_task["progress_key"]})
                continue
            if selected["availability"] != "active":
                reasons.append("availability_" + selected["availability"])
            if selected["effective_expires_at"] and selected["effective_expires_at"] <= as_of:
                reasons.append("effective_deadline_passed")
            if group_flags:
                reasons.extend("group_" + flag for flag in group_flags)
            reasons.extend(state_task["review_flags"])
            if task["status"] != "parsed":
                reasons.extend(task["review_reasons"] or ["task_needs_review"])
            if task["kind"] != "match":
                reasons.append("not_match_task")
            if state_task["progress_key"] is None:
                reasons.append("progress_cycle_unknown")
            cycle = _cycle_from_key(state_task["progress_key"]) if state_task["progress_key"] else None
            if cycle and cycle > as_of:
                reasons.append("cycle_starts_in_future")
            target = task["target"]
            if task["kind"] == "match" and (not target or target.get("scope") != "separate_matches"
                                                   or target.get("unit") != "matches"):
                reasons.append("match_count_not_bounded")
            count = progress["count"] if progress else 0
            if target and target.get("scope") == "separate_matches" and count >= target["count"]:
                reasons.append("completion_needs_confirmation")
            options = eligible_mode_options(task["mode_options"], excluded, modes) if task["kind"] == "match" else []
            if task["kind"] == "match" and not options:
                reasons.append("no_permitted_mode")
            if reasons:
                if reasons == ["match_count_not_bounded"] and target and target.get("scope") == "cumulative":
                    cumulative_tasks.append({"group_id": group_id, "task_id": task_id,
                                             "source_text": task["source_text"], "target": target,
                                             "remaining": max(0, target["count"] - count),
                                             "conditions": task["conditions"], "options": options})
                unscheduled.append(_unscheduled(selected, state_task, task, list(dict.fromkeys(reasons))))
                continue

            separate_tasks.append({"group_id": group_id, "task_id": task_id,
                                   "source_text": task["source_text"],
                                   "remaining": target["count"] - count,
                                   "conditions": task["conditions"], "options": options})

            # First source-listed permitted route is a choice, not a claim of optimality.
            option = options[0]
            # The group/cycle identity protects against assuming cross-group or
            # cross-cycle credit for a single game.
            signature = json.dumps([group_id, cycle, option, task["conditions"]], sort_keys=True)
            block = blocks.setdefault(signature, {
                "group_id": group_id, "group_title": selected["title"],
                "effective_expires_at": selected["effective_expires_at"],
                "cycle_start_utc": cycle, "mode_option": option,
                "conditions": task["conditions"], "qualifying_matches": 0, "tasks": [],
            })
            remaining = target["count"] - count
            block["qualifying_matches"] = max(block["qualifying_matches"], remaining)
            block["tasks"].append({"task_id": task_id, "source_text": task["source_text"],
                                   "progress_key": state_task["progress_key"],
                                   "remaining_qualifying_matches": remaining})

        # Removed source tasks retain progress but no interpreted rule to plan.
        for old in selected["unmatched_progress"]:
            unscheduled.append({"group_id": group_id, "task_id": old["task_id"],
                                "source_text": old["source_text"], "reasons": ["stored_task_unlisted"],
                                "target": None, "progress_key": None})

    plan = list(blocks.values())
    plan.sort(key=lambda block: (block["effective_expires_at"] is None,
                                 block["effective_expires_at"] or "", block["group_id"],
                                 block["mode_option"]["mode"],
                                 block["mode_option"]["event"] or ""))
    return {"schema_version": 1, "as_of": as_of,
            "source_fetched_at": interpreted["source_fetched_at"],
            "available_modes": sorted(modes), "excluded_modes": sorted(excluded),
            "match_blocks": plan, "unscheduled_tasks": unscheduled,
            "unavailable_groups": unavailable_groups,
            "completed_tasks": completed,
            "combined_plan": combine_tasks(separate_tasks, cumulative_tasks)}


def _cycle_from_key(key: str) -> str | None:
    return key.split("@", 1)[1] if "@" in key else None


def _unscheduled(selected: dict, state_task: dict, task: dict | None, reasons: list[str]) -> dict:
    return {"group_id": selected["group_id"], "task_id": state_task["id"],
            "source_text": state_task["source_text"], "reasons": reasons,
            "target": task["target"] if task else None,
            "progress_key": state_task["progress_key"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("fc27_interpreted.json"))
    parser.add_argument("--state", type=Path, required=True, help="Private user-state JSON path")
    parser.add_argument("--mode", action="append", required=True, help="Available mode; repeat for a catalog")
    parser.add_argument("--exclude", action="append", default=[], help="Excluded mode; repeat as needed")
    parser.add_argument("--cycle", action="append", default=[], metavar="GROUP_ID=UTC_START")
    parser.add_argument("--as-of", help="Explicit UTC time; defaults to current UTC")
    args = parser.parse_args()
    cycles = dict(item.split("=", 1) for item in args.cycle)
    interpreted = json.loads(args.source.read_text(encoding="utf-8"))
    now = args.as_of or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    view = selected_view(load_state(args.state), interpreted, now, cycles)
    result = build_plan(interpreted, view, set(args.mode), set(args.exclude))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
