"""Run the existing objective planner with private state held in the browser."""

from __future__ import annotations

import json

from plan_objectives import build_plan
from prize_summary import summarize
from user_objectives import (correct_deadline, new_state, record_progress, select,
                             selected_view, unselect, utc)

MODES = ("squad_battles", "rivals", "champions", "rush", "live_events",
         "pve_live_events", "pvp_live_events", "draft", "co_op", "fc_pro_open_ladder")
DEFAULT_SETTINGS = {"schema_version": 1, "available_modes": [], "excluded_modes": [], "cycles": {}}
SOURCE = None


def initialize(source_json: str) -> None:
    global SOURCE
    source = json.loads(source_json)
    if source.get("schema_version") != 1:
        raise ValueError("Unsupported objective export")
    SOURCE = source


def _state(value: str | None) -> dict:
    state = json.loads(value) if value else new_state()
    if state.get("schema_version") != 1 or any(not isinstance(state.get(k), dict)
                                                for k in ("selections", "deadline_corrections", "progress")):
        raise ValueError("Invalid saved progress")
    return state


def _settings(value: str | None) -> dict:
    settings = json.loads(value) if value else {**DEFAULT_SETTINGS, "cycles": {}}
    if settings.get("schema_version") != 1:
        raise ValueError("Invalid settings version")
    for key in ("available_modes", "excluded_modes"):
        values = settings.get(key)
        if not isinstance(values, list) or len(values) != len(set(values)) or any(v not in MODES for v in values):
            raise ValueError(f"Invalid {key}")
    cycles = settings.get("cycles")
    if not isinstance(cycles, dict):
        raise ValueError("Invalid cycles")
    for group_id, start in cycles.items():
        if not isinstance(group_id, str) or not isinstance(start, str):
            raise ValueError("Invalid cycle start")
        utc(start)
    return settings


def _snapshot(state: dict, settings: dict, now: str) -> dict:
    view = selected_view(state, SOURCE, now, settings["cycles"])
    plan = build_plan(SOURCE, view, set(settings["available_modes"]), set(settings["excluded_modes"]))
    return {"groups": [{**group, "prize": summarize(group)} for group in SOURCE["groups"]],
            "removed_groups": SOURCE.get("removed_groups", []),
            "view": view, "plan": plan, "settings": settings, "mode_catalog": MODES,
            "source_mismatch": False, "source_changes": SOURCE.get("changes")}


def snapshot_json(state_json: str | None, settings_json: str | None, now: str) -> str:
    return json.dumps(_snapshot(_state(state_json), _settings(settings_json), now), ensure_ascii=False)


def update_json(action: str, data_json: str, state_json: str | None,
                settings_json: str | None, now: str) -> str:
    state, settings, data = _state(state_json), _settings(settings_json), json.loads(data_json)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    if action == "select":
        group_id = str(data["group_id"])
        if type(data.get("selected")) is not bool:
            raise ValueError("selected must be boolean")
        if data["selected"]:
            select(state, SOURCE, group_id, now)
        else:
            unselect(state, group_id)
    elif action == "progress":
        task_id = str(data["task_id"])
        group_id = task_id.split(":", 1)[0]
        if group_id not in state["selections"]:
            raise ValueError("Select the group before recording progress")
        group = next((g for g in SOURCE["groups"] if g["id"] == group_id), None)
        if group is None:
            raise ValueError("Task is no longer listed")
        cycle = settings["cycles"].get(group_id) if group["repeat"]["cycle_key_required"] else None
        record_progress(state, SOURCE, task_id, count=data["count"],
                        completed=data["completed"], updated_at=now, cycle_start_utc=cycle)
    elif action == "deadline":
        if data.get("source") != "fc27_in_game":
            raise ValueError("Confirm that this expiry was observed in FC 27")
        correct_deadline(state, SOURCE, str(data["group_id"]), data["expires_at"], now)
    elif action == "settings":
        candidate = {"schema_version": 1, "available_modes": data["available_modes"],
                     "excluded_modes": data["excluded_modes"], "cycles": data["cycles"]}
        settings = _settings(json.dumps(candidate))
        valid_groups = {g["id"] for g in SOURCE["groups"] if g["repeat"]["cycle_key_required"]}
        if any(group_id not in valid_groups for group_id in settings["cycles"]):
            raise ValueError("Cycles must belong to a listed daily or weekly group")
    else:
        raise ValueError("Unknown action")
    return json.dumps({"state": state, "settings": settings,
                       "snapshot": _snapshot(state, settings, now)}, ensure_ascii=False)
