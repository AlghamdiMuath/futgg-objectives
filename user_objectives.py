#!/usr/bin/env python3
"""Private selections, deadline evidence, and manual progress for interpreted objectives."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from interpret_objectives import fingerprint

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
        "selected_at": utc(selected_at), "source_fingerprint": group["source_fingerprint"],
        "repeat_identity": repeat_identity(group) if group["repeat"]["cadence"] else None,
        "title": group["title"], "cadence": group["repeat"]["cadence"],
    })


def repeat_identity(group: dict) -> str:
    """Identify a published repeat objective without using the fetch time or rewards."""
    return fingerprint({"group_id": group["id"], "starts_at": group.get("starts_at"),
                        "tasks": sorted((task["id"], task["source_text"]) for task in group["tasks"])})


def reconcile_repeats(state: dict, interpreted: dict, legacy_cycles: dict | None = None) -> bool:
    """Switch selected repeat objectives when the source replaces them."""
    groups = groups_by_id(interpreted)
    changed = False
    for old_id, selection in list(state["selections"].items()):
        old = groups.get(old_id)
        title = selection.get("title") or (old or {}).get("title") or next(
            (g["title"] for g in interpreted.get("removed_groups", []) if g["id"] == old_id), None)
        cadence = selection.get("cadence") or (old or {}).get("repeat", {}).get("cadence") or (
            "daily" if title and "daily" in title.casefold() else
            "weekly" if title and "weekly" in title.casefold() else None)
        if not cadence:
            continue
        candidates = [g for g in groups.values() if g["repeat"]["cadence"] == cadence
                      and g["title"].casefold() == (title or "").casefold()]
        current = old if old and old["repeat"]["cadence"] == cadence else None
        newer = [g for g in candidates if current and g["id"] != old_id
                 and (g.get("starts_at") or "") > (current.get("starts_at") or "")]
        replacement = newer[0] if len(newer) == 1 else current or (candidates[0] if len(candidates) == 1 else None)
        if replacement is None:
            if old is None:
                del state["selections"][old_id]
                state["progress"] = {k: v for k, v in state["progress"].items()
                                     if v["task_id"].split(":", 1)[0] != old_id}
                changed = True
            continue
        identity = repeat_identity(replacement)
        old_identity = selection.get("repeat_identity")
        reset_progress = old_identity != identity or old_id != replacement["id"]
        if old_identity is None:
            # Legacy progress belongs only to the cycle explicitly selected by its owner.
            legacy = (legacy_cycles or {}).get(old_id) if selection.get("source_fingerprint") == replacement["source_fingerprint"] else None
            for task in replacement["tasks"]:
                old_key = f'{task["id"]}@{legacy}' if legacy else None
                if old_key in state["progress"]:
                    state["progress"][f'{task["id"]}@{identity}'] = {
                        **state["progress"][old_key], "cycle_start_utc": None}
            changed = True
        elif old_identity != identity or old_id != replacement["id"]:
            changed = True
        if selection.get("source_fingerprint") != replacement["source_fingerprint"]:
            changed = True
        if reset_progress:
            state["progress"] = {k: v for k, v in state["progress"].items()
                                 if v["task_id"].split(":", 1)[0] != old_id
                                 or k.endswith("@" + identity)}
        if old_id != replacement["id"]:
            del state["selections"][old_id]
            if replacement["id"] in state["selections"]:
                continue
            state["selections"][replacement["id"]] = selection
        selection.update({"repeat_identity": identity, "source_fingerprint": replacement["source_fingerprint"],
                          "title": replacement["title"], "cadence": cadence})
    return changed


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
    if cycle_start_utc is not None:
        raise ValueError("Cycle dates are no longer used for progress")
    key = f'{task_id}@{repeat_identity(group)}' if group["repeat"]["cadence"] else task_id
    task = next(t for t in group["tasks"] if t["id"] == task_id)
    original = state["progress"].get(key)
    state["progress"][key] = {
        "task_id": task_id, "cycle_start_utc": None, "count": count, "completed": completed,
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


def selected_view(state: dict, interpreted: dict, now: str) -> dict:
    """Resolve availability at read time; never copy private data into an export."""
    current = utc(now)
    groups = groups_by_id(interpreted)
    removed = {g["id"]: g for g in interpreted.get("removed_groups", [])}
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
        progress_history = []
        if group_id in groups:
            repeat = group["repeat"]
            identity = repeat_identity(group) if repeat["cadence"] else None
            progress_by_task = {}
            threshold_progress = {}
            for task in group["tasks"]:
                key = f'{task["id"]}@{identity}' if identity else task["id"]
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
                    progress = {"task_id": task["id"], "cycle_start_utc": None,
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
            unmatched_progress = [entry for key, entry in state["progress"].items()
                                  if entry["task_id"].split(":", 1)[0] == group_id
                                  and (not identity or key.endswith("@" + identity))
                                  and entry["task_id"] not in current_ids]
            if unmatched_progress:
                flags.append("stored_task_unlisted")
        result.append({"group_id": group_id, "title": group.get("title") if group else None,
                       "selection": selection, "availability": availability,
                       "source_expires_at": raw_expiry, "deadline_corrections": evidence,
                       "effective_expires_at": effective, "review_flags": flags,
                       "tasks": tasks, "unmatched_progress": unmatched_progress,
                       "progress_history": progress_history})
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
    view = commands.add_parser("view")
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
        reconcile_repeats(state, interpreted)
        record_progress(state, interpreted, args.task_id, count=args.count, completed=args.completed,
                        updated_at=now)
    else:
        if reconcile_repeats(state, interpreted):
            save_state(args.state, state)
        print(json.dumps(selected_view(state, interpreted, now), ensure_ascii=False, indent=2))
        return
    save_state(args.state, state)


if __name__ == "__main__":
    main()
