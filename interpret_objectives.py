#!/usr/bin/env python3
"""Conservatively interpret the public FUT.GG objective export."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


VERSION = 1
MODE_NAMES = {
    "Squad Battles": "squad_battles", "Rivals": "rivals", "Champions": "champions",
    "Live Events": "live_events", "Rush": "rush", "Draft": "draft",
    "Co-Op": "co_op", "PVE Live Events": "pve_live_events",
    "PVP Live Events": "pvp_live_events",
}
DIFFICULTIES = ("Semi-Pro", "Professional", "World Class", "Legendary", "Ultimate")

# Verified in-game behavior supplied by a domain expert: when a parsed match
# task omits a mode, it can be completed in any FUT game mode.


def fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def source_fingerprint(group: dict) -> str:
    """Only planning/reward fields; fetched_at and listing order do not cause churn."""
    fields = {key: group.get(key) for key in (
        "title", "description", "starts_at", "expires_at", "completion_rewards",
        "available_rewards", "total_season_points",
    )}
    fields["tasks"] = sorted(group["tasks"], key=lambda task: task["id"])
    return fingerprint(fields)


def changes(previous: dict, current: dict) -> list[dict]:
    old = {g["id"]: g for g in previous["groups"]}
    new = {g["id"]: g for g in current["groups"]}
    result = []
    for group_id in sorted(old.keys() | new.keys()):
        if group_id not in old or group_id not in new:
            result.append({"group_id": group_id, "change": "added" if group_id in new else "removed"})
            continue
        before, after = old[group_id], new[group_id]
        fields = [key for key in ("title", "description", "starts_at", "expires_at", "completion_rewards", "available_rewards", "total_season_points") if before.get(key) != after.get(key)]
        old_tasks = {t["id"]: t for t in before["tasks"]}
        new_tasks = {t["id"]: t for t in after["tasks"]}
        task_ids = sorted(tid for tid in old_tasks.keys() | new_tasks.keys() if old_tasks.get(tid) != new_tasks.get(tid))
        if fields or task_ids:
            result.append({"group_id": group_id, "change": "updated", "fields": fields, "task_ids": task_ids})
    return result


def _mode_option(label: str, difficulty: str | None = None, event: str | None = None) -> dict:
    return {"mode": MODE_NAMES.get(label, label), "event": event, "minimum_difficulty": difficulty}


def parse_modes(text: str) -> tuple[list[dict], str]:
    """Return OR options. A difficulty belongs only to its own option."""
    if re.search(r"\bany (?:FUT|Football Ultimate Team) game mode\b", text, re.I):
        return [_mode_option("any_fut")], "explicit"
    # Take the last "in ... Event/Challenge/Exhibition" clause. Earlier clauses
    # often describe a match count or starting XI, not the event name.
    event = re.search(r".*\bin (?:the )?(.+?) (?:Live Event|Challenge|Exhibition)\b", text, re.I)
    if event:
        name = event.group(1) + " " + ("Live Event" if "Live Event" in event.group(0) else "Challenge" if "Challenge" in event.group(0) else "Exhibition")
        return [_mode_option("live_events", event=name)], "explicit"
    if "FC Pro Open Ladder" in text and re.match(r"Play ", text):
        return [_mode_option("fc_pro_open_ladder")], "explicit"
    # Parenthesized alternatives are separate routes, never extra requirements.
    alt = re.search(r"\(or ([^)]+)\)", text)
    primary = text[:alt.start()] if alt else text
    options = []
    for label in sorted(MODE_NAMES, key=len, reverse=True):
        if re.search(r"\b" + re.escape(label) + r"\b", primary, re.I):
            diff = re.search(r"(?:min\. |minimum )(" + "|".join(DIFFICULTIES) + r") difficulty", primary, re.I)
            options.append(_mode_option(label, diff.group(1) if diff else None))
            break
    if alt:
        for name in alt.group(1).split("/"):
            label = name.strip().rstrip(". ")
            canonical = next((k for k in MODE_NAMES if k.lower() == label.lower()), None)
            if canonical:
                options.append(_mode_option(canonical))
            else:
                return options, "review"
    return options, "explicit" if options else "unspecified"


def _quantity(text: str) -> int:
    return int(text.replace(",", ""))


def parse_match_target(text: str) -> tuple[dict, list[dict]] | None:
    """The target distinguishes cumulative events from separate-match conditions."""
    match = re.match(r"^(Play|Win) (\d[\d,]*|a|any) (?:[\w-]+ ){0,3}match(?:es)?\b", text, re.I)
    if match:
        return ({"unit": "matches", "count": 1 if match.group(2).lower() in ("a", "any") else _quantity(match.group(2)), "scope": "separate_matches"}, [{"type": "result", "value": "win"}] if match.group(1).lower() == "win" else [])
    match = re.match(r"^(Score|Assist)(?: at least)? (\d[\d,]*|two) (?:([\w ]+?) )?goals? in (\d+) separate matches\b", text, re.I)
    if match:
        event = "goals" if match.group(1).lower() == "score" else "assists"
        count = 2 if match.group(2).lower() == "two" else _quantity(match.group(2))
        conditions = [{"type": event, "minimum_per_match": count}]
        if match.group(3): conditions.append({"type": "goal_style", "value": match.group(3).strip()})
        return {"unit": "matches", "count": _quantity(match.group(4)), "scope": "separate_matches"}, conditions
    match = re.match(r"^(Score|Assist) in (\d+) separate matches\b", text, re.I)
    if match:
        return {"unit": "matches", "count": _quantity(match.group(2)), "scope": "separate_matches"}, [{"type": "goals" if match.group(1).lower() == "score" else "assists", "minimum_per_match": 1}]
    match = re.match(r"^(Score|Assist) (\d[\d,]*|two) (?:([\w ]+?) )?goals? in (\d+) match\b", text, re.I)
    if match:
        event = "goals" if match.group(1).lower() == "score" else "assists"
        count = 2 if match.group(2).lower() == "two" else _quantity(match.group(2))
        return {"unit": "matches", "count": _quantity(match.group(4)), "scope": "separate_matches"}, [{"type": event, "minimum_per_match": count}]
    match = re.match(r"^(Score|Assist) (\d[\d,]*|two) (.*?)\b(?:goals?|times|direct Free Kicks)\b", text, re.I)
    if match:
        event = "goals" if match.group(1).lower() == "score" else "assists"
        count = 2 if match.group(2).lower() == "two" else _quantity(match.group(2))
        return {"unit": event, "count": count, "scope": "cumulative"}, []
    if re.match(r"^(Score|Assist)(?: with| in| from| while|\.)", text, re.I):
        event = "goals" if text.lower().startswith("score") else "assists"
        return {"unit": event, "count": 1, "scope": "cumulative"}, []
    return None


def parse_conditions(text: str) -> list[dict]:
    result = []
    squad = re.search(r"(?:while having|with) (.+?) in your starting (11|XI|squad)", text, re.I)
    if squad:
        for clause in re.split(r"\s+and\s+(?=\d+ |(?:min\.|at least) \d+ )", squad.group(1)):
            part = re.fullmatch(r"(?:(?:min\.|at least) )?(\d+) (.+)", clause.strip(), re.I)
            if part:
                result.append({"type": "squad", "minimum": int(part.group(1)), "trait": part.group(2), "slot": "starting_11" if squad.group(2).lower() != "squad" else "starting_squad"})
    if "starting squad of First Owned players" in text:
        result.append({"type": "squad", "minimum": "all", "trait": "First Owned players", "slot": "starting_squad"})
    role = "assisting_player" if text.lower().startswith("assist") else "scoring_player"
    for trait in re.findall(r"using (?:a|an) (.+?) player", text, re.I):
        if trait == "player with a Preferred Position of": continue
        result.append({"type": role, "trait": trait.strip(), "must_start": True})
    for trait in re.findall(r"(?:Score|Assist) (?:\d+ )?(?:goals? )?with (?:a|an) (.+?) player", text, re.I):
        result.append({"type": role, "trait": trait.strip(), "must_start": True})
    actor = re.search(r"^(Score|Assist) (?:\d+[\d,]* )?(?:goals? |times )?by (?:a|an) (.+?)(?: player)?(?: in |\.|$)", text, re.I)
    if actor:
        result.append({"type": "scoring_player" if actor.group(1).lower() == "score" else "assisting_player",
                       "trait": actor.group(2).strip(), "must_start": True})
    position = re.search(r"using a player with a Preferred Position of ([A-Z]+)", text)
    if position:
        result.append({"type": role, "trait": f"Preferred Position: {position.group(1)}", "must_start": True})
    if "outside the box" in text: result.append({"type": "goal_location", "value": "outside_the_box"})
    if "Low Driven goals" in text: result.append({"type": "goal_style", "value": "Low Driven"})
    if "direct Free Kicks" in text: result.append({"type": "goal_style", "value": "direct Free Kicks"})
    if "from a cross" in text: result.append({"type": "assist_source", "value": "cross"})
    if "as a team" in text: result.append({"type": "credited_to", "value": "team"})
    return result


def checklist_target(text: str) -> dict | None:
    patterns = (
        (r"^(?:Earn|reach) ([\d,]+) points\b", "points"),
        (r"^Complete ([\d,]+) (?:Rush bonuses|Sets|Squad Building Challenge groups)\b", "actions"),
        (r"^(?:Buy|List) ([\d,]+) (?:players|Player Items|player items)\b", "items"),
        (r"^Watch .+? for at least ([\d,]+) minutes\b", "minutes"),
        (r"^Reach Gallery Level ([\d,]+)\b", "level"),
        (r"^Reach Division ([\d,]+)\b", "division"),
    )
    for pattern, unit in patterns:
        match = re.search(pattern, text, re.I)
        if match: return {"unit": unit, "count": _quantity(match.group(1)), "scope": "cumulative"}
    return None


def interpret_task(task: dict, group: dict, titles: dict[str, str]) -> dict:
    text = task["description"]
    reasons = []
    dependency = None
    dep = re.match(r"^(?:Fully )?Complete (?:the )?['\"]?(.+?)['\"]? (?:Objectives Group|objective)(?: (\d+) times?| (\d+) times?)?\.$", text, re.I)
    if dep:
        name = dep.group(1).strip("'\" ")
        matches = [gid for gid, title in titles.items() if title.lower() == name.lower()]
        dependency = {"group_id": matches[0] if len(matches) == 1 else None, "group_title": name, "completions": int(dep.group(2) or dep.group(3) or 1), "distinct_periods": bool(dep.group(2) or dep.group(3))}
        if len(matches) != 1: reasons.append("unresolved_dependency")
    if dependency:
        kind, target, conditions, modes = "dependency", {"unit": "group_completions", "count": dependency["completions"], "scope": "distinct_periods" if dependency["distinct_periods"] else "once"}, [], []
    else:
        modes, mode_status = parse_modes(text)
        parsed = parse_match_target(text)
        if parsed:
            kind, (target, conditions) = "match", parsed
            conditions += parse_conditions(text)
            if mode_status != "explicit": reasons.append("mode_" + mode_status)
            if mode_status == "unspecified":
                modes = [_mode_option("any_fut")]
                reasons = [reason for reason in reasons if reason != "mode_unspecified"]
            if re.search(r"\b(?:goals?|assists?) in any [\w ]+ match\b", text, re.I):
                reasons.append("cumulative_vs_single_match_unclear")
        else:
            kind, target, conditions = "checklist", checklist_target(text), []
            if re.match(r"^(?:Play|Win|Score|Assist)\b", text, re.I): reasons.append("unparsed_match_rule")
            modes = []
    # A checklist preserves its full instruction; quantities are only hints and never scheduling rules.
    checklist = {"action": text} if kind == "checklist" else None
    return {
        "id": task["id"], "title": task["title"], "source_text": text,
        "rewards": task.get("rewards", []), "kind": kind,
        "status": "review" if reasons else "parsed", "review_reasons": reasons,
        "mode_options": modes, "target": target, "conditions": conditions,
        "checklist": checklist, "dependency": dependency,
        "prerequisites": [],
        "source_fingerprint": fingerprint({"title": task["title"], "description": text, "rewards": task.get("rewards", [])}),
    }


def repeat_info(group: dict) -> dict:
    title = group["title"].lower()
    cadence = "daily" if "daily" in title else "weekly" if "weekly" in title else None
    return {"cadence": cadence, "reset_schedule": None, "cycle_key_required": cadence is not None}


def progress_key(task_id: str, cycle_start: str | None, repeat: dict) -> str:
    """Build an identity for private progress only after a reset boundary is known."""
    if repeat["cycle_key_required"]:
        if not cycle_start:
            raise ValueError("Repeat objective requires an authoritative cycle start")
        parsed = datetime.fromisoformat(cycle_start.replace("Z", "+00:00"))
        if parsed.utcoffset() is None:
            raise ValueError("Cycle start must include a timezone")
        cycle_start = parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return f"{task_id}@{cycle_start}"
    return task_id


def eligible_mode_options(options: list[dict], excluded: set[str], available_modes: set[str]) -> list[dict]:
    """Resolve an any-FUT option against a caller's mode catalog and exclusions."""
    def allowed(mode: str) -> bool:
        parent = "live_events" if mode in ("pve_live_events", "pvp_live_events") else mode
        return mode not in excluded and parent not in excluded and mode in available_modes

    result = []
    for option in options:
        if option["mode"] == "any_fut":
            result.extend(_mode_option(mode) for mode in sorted(available_modes) if allowed(mode))
        elif allowed(option["mode"]):
            result.append(option)
    return result


def interpret_export(raw: dict) -> dict:
    if raw.get("schema_version") != 3:
        raise ValueError("Expected FUT.GG export schema version 3")
    titles = {g["id"]: g["title"] for g in raw["groups"]}
    groups = []
    for group in raw["groups"]:
        tasks = [interpret_task(task, group, titles) for task in group["tasks"]]
        # Verified FC 27 behavior: a task that says it qualifies a player for
        # a named mode is a strict access gate for that mode.
        for qualifier in tasks:
            match = re.search(r"to qualify for the (.+?)\.$", qualifier["source_text"])
            if match:
                for task in tasks:
                    if task["id"] != qualifier["id"] and f"in the {match.group(1)}" in task["source_text"]:
                        task["prerequisites"].append({"task_id": qualifier["id"], "relation": "access_qualification", "status": "confirmed"})
        groups.append({
            "id": group["id"], "title": group["title"], "category": group["category"],
            "description": group["description"], "url": group["url"],
            "starts_at": group["starts_at"], "expires_at": group["expires_at"],
            "completion_rewards": group.get("completion_rewards", []),
            "available_rewards": group.get("available_rewards", []),
            "total_season_points": group.get("total_season_points"),
            "repeat": repeat_info(group), "source_fingerprint": source_fingerprint(group),
            "tasks": tasks,
        })
    return {"schema_version": VERSION, "source_schema_version": raw["schema_version"],
            "source_fetched_at": raw["fetched_at"], "groups": groups,
            "removed_groups": raw.get("removed_groups", [])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("fc27_objectives.json"))
    parser.add_argument("--output", type=Path, default=Path("fc27_interpreted.json"))
    parser.add_argument("--previous", type=Path, help="previous raw export for change report")
    args = parser.parse_args()
    raw = json.loads(args.input.read_text(encoding="utf-8"))
    result = interpret_export(raw)
    if args.previous:
        result["changes"] = changes(json.loads(args.previous.read_text(encoding="utf-8")), raw)
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    tasks = [t for g in result["groups"] for t in g["tasks"]]
    print(f"Wrote {len(result['groups'])} groups, {len(tasks)} tasks; {sum(t['status'] == 'review' for t in tasks)} need review")


if __name__ == "__main__":
    main()
