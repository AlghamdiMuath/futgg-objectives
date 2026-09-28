#!/usr/bin/env python3
"""Private selections, deadline evidence, and manual progress for interpreted objectives."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from interpret_objectives import progress_key

SCHEMA_VERSION = 1


def utc(value: str) -> str:
    """Require an explicit UTC offset and return a canonical UTC timestamp."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() != timezone.utc.utcoffset(None):
        raise ValueError("Timestamp must be explicitly UTC (Z or +00:00)")
    return parsed.isoformat().replace("+00:00", "Z")


def new_state() -> dict:
    return {"schema_version": SCHEMA_VERSION, "selections": {}, "deadline_corrections": {}, "progress": {}}


def load_state(path: Path) -> dict:
    state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else new_state()
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported user-state schema version")
    for field in ("selections", "deadline_corrections", "progress"):
        if not isinstance(state.get(field), dict):
            raise ValueError(f"Invalid user-state {field}")
    return state


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        file.write(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def groups_by_id(interpreted: dict) -> dict[str, dict]:
    if interpreted.get("schema_version") != 1:
        raise ValueError("Expected interpreted export schema version 1")
    return {group["id"]: group for group in interpreted["groups"]}


def select(state: dict, interpreted: dict, group_id: str, selected_at: str) -> None:
    group = groups_by_id(interpreted).get(group_id)
    if group is None:
        raise ValueError(f"Group {group_id} is not currently listed")
    state["selections"].setdefault(group_id, {
        "selected_at": utc(selected_at), "source_fingerprint": group["source_fingerprint"]
    })


def unselect(state: dict, group_id: str) -> None:
    # Historical progress and deadline evidence survive deselection.
    state["selections"].pop(group_id, None)


def correct_deadline(state: dict, interpreted: dict, group_id: str, expires_at: str, recorded_at: str) -> None:
    groups = groups_by_id(interpreted)
    group = groups.get(group_id)
    if group is None and not any(g["id"] == group_id for g in interpreted.get("removed_groups", [])):
        raise ValueError(f"Unknown group {group_id}")
    evidence = {"expires_at": utc(expires_at), "source": "fc27_in_game", "recorded_at": utc(recorded_at)}
    entries = state["deadline_corrections"].setdefault(group_id, [])
    if evidence not in entries:
        entries.append(evidence)


def record_progress(state: dict, interpreted: dict, task_id: str, *, count: int,
                    completed: bool, updated_at: str, cycle_start_utc: str | None = None) -> None:
    if isinstance(count, bool) or not isinstance(count, int) or count < 0 or not isinstance(completed, bool):
        raise ValueError("Progress requires a nonnegative integer count and boolean completed")
    group = next((g for g in groups_by_id(interpreted).values() if any(t["id"] == task_id for t in g["tasks"])), None)
    if group is None:
        raise ValueError(f"Unknown active task {task_id}")
    repeat = group["repeat"]
    if not repeat["cycle_key_required"] and cycle_start_utc is not None:
        raise ValueError("Nonrepeat progress cannot have a cycle start")
    cycle = utc(cycle_start_utc) if cycle_start_utc is not None else None
    key = progress_key(task_id, cycle, repeat)
    task = next(t for t in group["tasks"] if t["id"] == task_id)
    original = state["progress"].get(key)
    state["progress"][key] = {
        "task_id": task_id, "cycle_start_utc": cycle, "count": count, "completed": completed,
        "updated_at": utc(updated_at),
        "source_fingerprint": original["source_fingerprint"] if original else task["source_fingerprint"],
        "source_text": original["source_text"] if original else task["source_text"],
    }


def cumulative_threshold_family(task: dict) -> tuple[str, str] | None:
    """Identify same-group checklist ladders such as weekly Rush points.

    A number is deliberately removed only from otherwise identical public
    instructions. This prevents unrelated cumulative counters, such as market
    buys and listings, from sharing progress.
    """
    target = task.get("target") or {}
    checklist = task.get("checklist") or {}
    action = checklist.get("action")
    if (task.get("kind") != "checklist" or target.get("scope") != "cumulative"
            or not target.get("unit") or not isinstance(action, str)):
        return None
    return target["unit"], re.sub(r"\d[\d,]*", "#", action.casefold())


def selected_view(state: dict, interpreted: dict, now: str,
                  cycles: dict[str, str] | None = None) -> dict:
    """Resolve availability at read time; never copy private data into an export."""
    current = utc(now)
    groups = groups_by_id(interpreted)
    removed = {g["id"]: g for g in interpreted.get("removed_groups", [])}
    cycles = {gid: utc(start) for gid, start in (cycles or {}).items()}
    result = []
    for group_id, selection in state["selections"].items():
        group = groups.get(group_id) or removed.get(group_id)
        raw_expiry = group.get("expires_at") if group else None
        evidence = state["deadline_corrections"].get(group_id, [])
        user_values = {entry["expires_at"] for entry in evidence}
        flags = []
        if group_id in groups and selection["source_fingerprint"] != group["source_fingerprint"]:
            flags.append("source_group_changed")
        if len(user_values) > 1:
            flags.append("conflicting_user_deadlines")
        if raw_expiry is not None and any(value != raw_expiry for value in user_values):
            flags.append("source_deadline_conflict")
        # FUT.GG's published value wins when present. Conflicting manual evidence
        # without a published value cannot safely choose an effective deadline.
        effective = raw_expiry if raw_expiry is not None else next(iter(user_values)) if len(user_values) == 1 else None
        if group is None:
            availability = "missing"
            flags.append("missing_source_group")
        elif effective is not None and effective <= current:
            availability = "expired"
        elif group_id in removed:
            availability = "unlisted"
        elif len(user_values) > 1 and raw_expiry is None:
            availability = "needs_review"
        elif group.get("starts_at") and group["starts_at"] > current:
            availability = "upcoming"
        else:
            availability = "active"
        if group_id in removed:
            flags.append("unlisted_source_group")
        tasks = []
        unmatched_progress = []
        if group_id in groups:
            repeat = group["repeat"]
            cycle = cycles.get(group_id) if repeat["cycle_key_required"] else None
            if repeat["cycle_key_required"] and cycle is None:
                flags.append("cycle_start_required")
            progress_by_task = {}
            threshold_progress = {}
            for task in group["tasks"]:
                key = progress_key(task["id"], cycle, repeat) if not repeat["cycle_key_required"] or cycle else None
                progress = state["progress"].get(key) if key else None
                progress_by_task[task["id"]] = (key, progress)
                family = cumulative_threshold_family(task)
                if progress and family:
                    previous = threshold_progress.get(family)
                    if previous is None or progress["count"] > previous["count"]:
                        threshold_progress[family] = progress
            for task in group["tasks"]:
                key, progress = progress_by_task[task["id"]]
                family = cumulative_threshold_family(task)
                aggregate = threshold_progress.get(family) if family else None
                if aggregate and (progress is None or aggregate["count"] > progress["count"]):
                    progress = {"task_id": task["id"], "cycle_start_utc": cycle,
                                "count": aggregate["count"],
                                "completed": aggregate["count"] >= task["target"]["count"],
                                "updated_at": aggregate["updated_at"],
                                "source_fingerprint": task["source_fingerprint"],
                                "source_text": task["source_text"]}
                task_flags = []
                if progress and progress["source_fingerprint"] != task["source_fingerprint"]:
                    task_flags.append("source_task_changed")
                tasks.append({"id": task["id"], "source_text": task["source_text"],
                              "progress_key": key, "progress": progress, "review_flags": task_flags})
            current_ids = {task["id"] for task in group["tasks"]}
            unmatched_progress = [entry for entry in state["progress"].values()
                                  if entry["task_id"].split(":", 1)[0] == group_id
                                  and entry["task_id"] not in current_ids]
            if unmatched_progress:
                flags.append("stored_task_unlisted")
        result.append({"group_id": group_id, "title": group.get("title") if group else None,
                       "selection": selection, "availability": availability,
                       "source_expires_at": raw_expiry, "deadline_corrections": evidence,
                       "effective_expires_at": effective, "review_flags": flags,
                       "tasks": tasks, "unmatched_progress": unmatched_progress})
    return {"schema_version": 1, "as_of": current, "source_fetched_at": interpreted["source_fetched_at"],
            "selected_groups": result}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("fc27_interpreted.json"))
    parser.add_argument("--state", type=Path, required=True, help="Private user-state JSON path")
    commands = parser.add_subparsers(dest="command", required=True)
    selection = commands.add_parser("select")
    selection.add_argument("group_id")
    commands.add_parser("unselect").add_argument("group_id")
    deadline = commands.add_parser("deadline")
    deadline.add_argument("group_id")
    deadline.add_argument("expires_at", help="Expiry visible in FC 27, as UTC")
    progress = commands.add_parser("progress")
    progress.add_argument("task_id")
    progress.add_argument("count", type=int)
    progress.add_argument("--completed", action="store_true")
    progress.add_argument("--cycle-start-utc")
    view = commands.add_parser("view")
    view.add_argument("--cycle", action="append", default=[], metavar="GROUP_ID=UTC_START")
    args = parser.parse_args()
    interpreted = json.loads(args.source.read_text(encoding="utf-8"))
    state = load_state(args.state)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if args.command == "select":
        select(state, interpreted, args.group_id, now)
    elif args.command == "unselect":
        unselect(state, args.group_id)
    elif args.command == "deadline":
        correct_deadline(state, interpreted, args.group_id, args.expires_at, now)
    elif args.command == "progress":
        record_progress(state, interpreted, args.task_id, count=args.count, completed=args.completed,
                        updated_at=now, cycle_start_utc=args.cycle_start_utc)
    else:
        cycles = dict(item.split("=", 1) for item in args.cycle)
        print(json.dumps(selected_view(state, interpreted, now, cycles), ensure_ascii=False, indent=2))
        return
    save_state(args.state, state)


if __name__ == "__main__":
    main()
