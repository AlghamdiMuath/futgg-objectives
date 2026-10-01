"""Build a reward-ranked daily itinerary from active, reviewed match objectives."""

from __future__ import annotations

import re
from copy import deepcopy
from functools import cmp_to_key

from plan_objectives import build_plan
from optimize_matches import _player_roles, _squad_requirements
from interpret_objectives import eligible_mode_options
from user_objectives import select, selected_view

PRIORITIES = {"balanced", "packs", "coins", "season_points"}
SKIP_CATEGORIES = {"milestones", "mastery"}
ALL_MODES = {"squad_battles", "rivals", "champions", "rush", "live_events",
             "pve_live_events", "pvp_live_events", "draft", "co_op", "fc_pro_open_ladder"}
REVIEWED_RULES = {"25:140": {"source_text": "Score 20 goals in any Live Events match (or Rivals/Squad Battles).",
                              "target": {"unit": "goals", "count": 20, "scope": "cumulative"},
                              "mode_options": [{"mode": "live_events", "event": None, "minimum_difficulty": None},
                                               {"mode": "rivals", "event": None, "minimum_difficulty": None},
                                               {"mode": "squad_battles", "event": None, "minimum_difficulty": None}]}}


def _with_reviewed_rules(interpreted: dict, reviewed_rules: dict) -> dict:
    result = deepcopy(interpreted)
    for group in result["groups"]:
        for task in group["tasks"]:
            rule = reviewed_rules.get(task["id"])
            if rule and rule.get("source_text") == task["source_text"]:
                task["target"] = deepcopy(rule["target"])
                task["mode_options"] = deepcopy(rule["mode_options"])
                task["status"] = "parsed"
                task["review_reasons"] = []
                task["reviewed_rule"] = True
    return result


def _has_reward(group: dict, reward: str) -> bool:
    labels = list(group.get("completion_rewards", []))
    labels.extend(label for task in group.get("tasks", []) for label in task.get("rewards", []))
    if reward == "balanced":
        return bool(labels)
    if reward == "season_points":
        # Generic "Points" can mean Champions qualification points.
        return any(re.search(r"\b(?:SP|Season Points)\b", label, re.I) for label in labels)
    return any(_reward(label)["kind"] == ("pack" if reward == "packs" else "coins")
               for label in labels)


def _active_view(interpreted: dict, state: dict, now: str, excluded_modes: set[str],
                 reward: str = "balanced") -> dict:
    """Use the existing progress resolver while including every eligible group."""
    temporary = deepcopy(state)
    groups = {group["id"]: group for group in interpreted["groups"]}
    for group_id, group in groups.items():
        category = str(group.get("category", "")).casefold().replace("_", " ")
        if category in SKIP_CATEGORIES:
            continue
        if not _has_reward(group, reward):
            continue
        if group.get("starts_at") and group["starts_at"] > now:
            continue
        if group.get("expires_at") and group["expires_at"] <= now:
            continue
        select(temporary, interpreted, group_id, now)
    view = selected_view(temporary, interpreted, now)
    view["selected_groups"] = [group for group in view["selected_groups"]
                               if group.get("availability") == "active"
                               and str(groups.get(group["group_id"], {}).get("category", ""))
                               .casefold().replace("_", " ") not in SKIP_CATEGORIES
                               and _has_reward(groups.get(group["group_id"], {}), reward)]
    return view


def _reward(label: str) -> dict:
    coin = re.fullmatch(r"([\d,]+) Coins", label, re.I)
    if coin:
        return {"kind": "coins", "label": label, "amount": int(coin[1].replace(",", ""))}
    if "pack" in label.casefold():
        rating = re.search(r"(?<!\d)(\d{2})\+", label)
        normalized = re.sub(r"^\d+\s+x\s+", "", label, flags=re.I)
        count = re.match(r"(\d+)\s*x\s*", normalized, re.I)
        players = int(count[1]) if count and "player" in label.casefold() else (
            1 if re.search(r"\bPlayer Pack\b", label, re.I) else None)
        return {"kind": "pack", "label": label, "rating": int(rating[1]) if rating else None,
                "players": players}
    generic = ("point", "sp", "token", "badge", "award", "consumable", "manager", "trophy",
               "boost", "unlock", "access", "pick", "tifo", "theme", "ball")
    if any(word in label.casefold() for word in generic):
        points = re.search(r"([\d,]+)\s*(?:SP|Season Points)\b", label, re.I)
        return {"kind": "season_points" if points else "other", "label": label,
                "amount": int(points[1].replace(",", "")) if points else 0}
    rated = re.fullmatch(r"(.+?)\s*\((\d{2})\)", label)
    return {"kind": "player", "label": label, "rating": int(rated[2]) if rated else None}


def _task_map(interpreted: dict) -> tuple[dict, dict]:
    groups = {group["id"]: group for group in interpreted["groups"]}
    tasks = {task["id"]: (group, task) for group in interpreted["groups"] for task in group["tasks"]}
    return groups, tasks


def _task_progress(view: dict) -> dict:
    return {task["id"]: task["progress"] for group in view["selected_groups"] for task in group["tasks"]}


def _difficulty_value(value: str | None) -> int:
    levels = ("Beginner", "Amateur", "Semi-Pro", "Professional", "World Class", "Legendary", "Ultimate")
    return levels.index(value) if value in levels else -1


def _progress_increment(task: dict) -> int:
    target = task.get("target") or {}
    if target.get("unit") == "matches":
        return 1
    if target.get("scope") == "cumulative" and target.get("unit") in ("goals", "assists"):
        return max((condition.get("minimum_per_match", 1) for condition in task.get("conditions", [])
                    if condition.get("type") in ("goals", "assists")), default=1)
    return 0


def _advance_progress(task_ids: list[str], tasks: dict, progress: dict) -> None:
    for task_id in task_ids:
        task = tasks[task_id][1]
        amount = _progress_increment(task)
        if not amount:
            continue
        current = progress.get(task_id) or {"count": 0, "completed": False}
        count = current.get("count", 0) + amount
        target = task.get("target") or {}
        progress[task_id] = {**current, "count": count,
                             "completed": bool(current.get("completed") or
                                               (target.get("count") and count >= target["count"]))}


def _run_recipes(plan: dict, tasks: dict, groups: dict, progress: dict,
                 excluded_modes: set[str]) -> list[dict]:
    recipes = []
    progress_state = deepcopy(progress)
    run_number = 0
    for run in plan["combined_plan"]["runs"]:
        run_id = run_number
        run_number += 1
        route = run["mode_option"]
        for offset in range(run["qualifying_matches"]):
            advances = []
            for item in run["match_tasks"]:
                if offset >= item["remaining_qualifying_matches"]:
                    continue
                advances.append(item["task_id"])
            for item in run["cumulative_targets"]:
                advances.append(item["task_id"])
            if not advances:
                continue
            unique = list(dict.fromkeys(advances))
            levels = []
            for task_id in unique:
                task_options = tasks[task_id][1].get("mode_options", [])
                applicable = [option.get("minimum_difficulty") for option in task_options
                              if option["mode"] == route["mode"]
                              and (option.get("event") is None or option.get("event") == route.get("event"))
                              and option.get("minimum_difficulty")]
                if applicable:
                    levels.append(min(applicable, key=_difficulty_value))
            recipe_route = {**route, "minimum_difficulty": max(levels, key=_difficulty_value) if levels else None}
            active_tasks = [{"conditions": tasks[task_id][1].get("conditions", [])} for task_id in unique]
            setup = {"squad_requirements": _squad_requirements(active_tasks),
                     "player_roles": _player_roles(active_tasks)}
            required = []
            for task_id in unique:
                group, task = tasks[task_id]
                conditions = task.get("conditions", [])
                deliberate = any(condition.get("type") not in ("result",) for condition in conditions)
                target = task.get("target") or {}
                before = (progress_state.get(task_id) or {}).get("count", 0)
                increment = 1 if target.get("unit") == "matches" else 0
                if target.get("scope") == "cumulative" and target.get("unit") in ("goals", "assists"):
                    increment = max((condition.get("minimum_per_match", 1) for condition in conditions
                                     if condition.get("type") in ("goals", "assists")), default=1)
                reward_steps = (list(task.get("rewards", []))
                                if target.get("count") and before < target["count"] <= before + increment
                                else [])
                required.append({"task_id": task_id, "group_id": group["id"],
                                 "group_title": group["title"], "source_text": task["source_text"],
                                 "conditions": conditions, "target": target, "deliberate": deliberate,
                                 "reviewed_rule": task.get("reviewed_rule", False),
                                 "reward_steps": reward_steps})
            # Natural match counters may also progress, but only list conditions
            # from the recipe as claimed progress.
            recipes.append({"route": recipe_route, "setup": setup, "objectives": required,
                            "task_ids": unique, "expires_at": None,
                            "score": _score_recipe(unique, tasks, groups, progress_state),
                            "run_order": len(recipes), "run_id": run_id})
            _advance_progress(unique, tasks, progress_state)
    included = {task_id for recipe in recipes for task_id in recipe["task_ids"]}
    for task_id in plan["combined_plan"].get("cumulative_without_run", []):
        if task_id in included or task_id not in tasks:
            continue
        group, task = tasks[task_id]
        target = task.get("target") or {}
        current = progress_state.get(task_id) or {}
        remaining = max(0, target.get("count", 0) - current.get("count", 0))
        options = eligible_mode_options(task.get("mode_options", []), excluded_modes, ALL_MODES)
        if not remaining or not options:
            continue
        route = options[0]
        run_id = run_number
        run_number += 1
        conditions = task.get("conditions", [])
        setup = {"squad_requirements": _squad_requirements([{"conditions": conditions}]),
                 "player_roles": _player_roles([{"conditions": conditions}])}
        # A cumulative goal or assist target has no reliable match count.
        # Suggest one useful game, then recalculate from recorded progress.
        current = progress_state.get(task_id) or {"count": 0, "completed": False}
        before = current.get("count", 0)
        increment = _progress_increment(task)
        reward_steps = (list(task.get("rewards", []))
                        if target.get("count") and before < target["count"] <= before + increment
                        else [])
        objective = {"task_id": task_id, "group_id": group["id"],
                     "group_title": group["title"], "source_text": task["source_text"],
                     "conditions": conditions, "target": target,
                     "deliberate": any(condition.get("type") != "result" for condition in conditions),
                     "reviewed_rule": task.get("reviewed_rule", False), "reward_steps": reward_steps}
        recipes.append({"route": route, "setup": setup, "objectives": [objective],
                        "task_ids": [task_id], "expires_at": group.get("expires_at"),
                        "score": _score_recipe([task_id], tasks, groups, progress_state),
                        "run_order": len(recipes), "run_id": run_id})
        _advance_progress([task_id], tasks, progress_state)
    return recipes


def _select_batch(recipes: list[dict], tasks: dict, groups: dict, progress: dict,
                  priority: str) -> list[dict]:
    """Choose the highest-scoring compatible run prefixes without promising future thresholds."""
    run_map: dict[int, list[dict]] = {}
    for recipe in recipes:
        run_map.setdefault(recipe["run_id"], []).append(recipe)
    for sequence in run_map.values():
        sequence.sort(key=lambda recipe: recipe["run_order"])
    current = deepcopy(progress)
    selected = []
    while run_map and len(selected) < 10:
        slots = 10 - len(selected)
        options = []
        for run_id, sequence in run_map.items():
            simulation = deepcopy(current)
            simulated_recipes = []
            total = {"direct_84_players": 0, "direct_84_rating_sum": 0,
                     "packs": [], "season_points": 0, "below_84_players": 0,
                     "below_84_rating_sum": 0, "coins": 0, "completion_rewards": []}
            for recipe in sequence[:slots]:
                for objective in recipe["objectives"]:
                    task = tasks[objective["task_id"]][1]
                    target = task.get("target") or {}
                    before = (simulation.get(objective["task_id"]) or {}).get("count", 0)
                    increment = _progress_increment(task)
                    objective["reward_steps"] = (list(task.get("rewards", []))
                        if target.get("count") and before < target["count"] <= before + increment else [])
                score = _score_recipe(recipe["task_ids"], tasks, groups, simulation)
                recipe_copy = {**recipe, "score": score}
                simulated_recipes.append(recipe_copy)
                for key in ("direct_84_players", "direct_84_rating_sum", "season_points",
                            "below_84_players", "below_84_rating_sum", "coins"):
                    total[key] += score[key]
                total["packs"].extend(score["packs"])
                total["completion_rewards"].extend(score["completion_rewards"])
                _advance_progress(recipe["task_ids"], tasks, simulation)
            options.append((run_id, simulated_recipes, simulation, total))
        winner = options[0]
        for candidate in options[1:]:
            comparison = _compare_scores(candidate[3], winner[3], priority)
            if comparison > 0 or (comparison == 0 and candidate[0] < winner[0]):
                winner = candidate
        run_id, chosen, current, _ = winner
        selected.extend(chosen)
        del run_map[run_id]
    return selected


def _score_recipe(task_ids: list[str], tasks: dict, groups: dict, progress: dict) -> dict:
    direct84 = lower_players = direct84_rating = lower_rating = coins = sp = 0
    packs = []
    completion_reward_labels = []
    completion_groups = set()
    for task_id in task_ids:
        group, task = tasks[task_id]
        current = progress.get(task_id) or {}
        before = current.get("count", 0)
        target = task.get("target") or {}
        increment = 1 if target.get("unit") == "matches" else 0
        if target.get("scope") == "cumulative" and target.get("unit") in ("goals", "assists"):
            increment = max((condition.get("minimum_per_match", 1)
                             for condition in task.get("conditions", [])
                             if condition.get("type") in ("goals", "assists")), default=1)
        after = before + increment
        completed_before = bool(current.get("completed"))
        completed_after = bool(target.get("count") and after >= target["count"])
        rewards = list(task.get("rewards", []))
        if target.get("count") and after < target["count"]:
            rewards = []
        if completed_before:
            rewards = []
        for label in rewards:
            item = _reward(label)
            if item["kind"] == "player":
                if item.get("rating") is not None and item["rating"] >= 84:
                    direct84 += 1
                    direct84_rating += item["rating"]
                else:
                    lower_players += 1
                    lower_rating += item.get("rating") or 0
            elif item["kind"] == "pack":
                packs.append(item)
            elif item["kind"] == "coins":
                coins += item["amount"]
            elif item["kind"] == "season_points":
                sp += item["amount"]
        if target.get("count") and completed_after:
            completion_groups.add(group["id"])
    # A group reward is marginal only when this recipe completes every listed
    # group task. Count each completion reward once even if several tasks cross.
    for group_id in completion_groups:
        group = groups[group_id]
        def projected_done(task: dict) -> bool:
            current = progress.get(task["id"]) or {}
            if current.get("completed"):
                return True
            target = task.get("target") or {}
            if not target.get("count"):
                return False
            increment = 0
            if task["id"] in task_ids:
                if target.get("unit") == "matches":
                    increment = 1
                elif target.get("scope") == "cumulative" and target.get("unit") in ("goals", "assists"):
                    increment = max((condition.get("minimum_per_match", 1)
                                     for condition in task.get("conditions", [])
                                     if condition.get("type") in ("goals", "assists")), default=1)
            return current.get("count", 0) + increment >= target["count"]

        complete = all(projected_done(task) for task in group.get("tasks", []))
        if complete:
            for label in group.get("completion_rewards", []):
                completion_reward_labels.append(label)
                item = _reward(label)
                if item["kind"] == "player":
                    if item.get("rating") is not None and item["rating"] >= 84:
                        direct84 += 1
                        direct84_rating += item["rating"]
                    else:
                        lower_players += 1
                        lower_rating += item.get("rating") or 0
                elif item["kind"] == "pack":
                    packs.append(item)
                elif item["kind"] == "coins":
                    coins += item["amount"]
                elif item["kind"] == "season_points":
                    sp += item["amount"]
    return {"direct_84_players": direct84, "direct_84_rating_sum": direct84_rating, "packs": packs,
            "season_points": sp, "below_84_players": lower_players,
            "below_84_rating_sum": lower_rating, "coins": coins,
            "completion_rewards": completion_reward_labels}


def _compare_pack(left: dict, right: dict) -> int:
    """Return positive when left is the better published pack label."""
    lr, rr = left.get("rating"), right.get("rating")
    lc, rc = left.get("players"), right.get("players")
    rating_gap = abs(lr - rr) if lr is not None and rr is not None else 0
    if lr is not None and rr is None:
        return 1
    if rr is not None and lr is None:
        return -1
    if rating_gap >= 2:
        return (lr > rr) - (lr < rr)
    if lc is not None and rc is None:
        return 1
    if rc is not None and lc is None:
        return -1
    if lc is not None and rc is not None and abs(lc - rc) >= 2:
        return (lc > rc) - (lc < rc)
    if lr is not None and rr is not None and lr != rr:
        return (lr > rr) - (lr < rr)
    if lc is not None and rc is not None:
        return (lc > rc) - (lc < rc)
    return 0


def _compare_pack_lists(left: list[dict], right: list[dict]) -> int:
    a = sorted(left, key=cmp_to_key(_compare_pack), reverse=True)
    b = sorted(right, key=cmp_to_key(_compare_pack), reverse=True)
    for one, two in zip(a, b):
        result = _compare_pack(one, two)
        if result:
            return result
    return (len(a) > len(b)) - (len(a) < len(b))


def _compare_scores(left: dict, right: dict, priority: str) -> int:
    fields = ["direct_84", "packs", "season_points", "below_84", "coins"]
    if priority == "packs":
        fields = ["packs", "direct_84", "season_points", "below_84", "coins"]
    elif priority == "coins":
        fields = ["coins", "direct_84", "packs", "season_points", "below_84"]
    elif priority == "season_points":
        fields = ["season_points", "direct_84", "packs", "below_84", "coins"]
    for field in fields:
        if field == "packs":
            result = _compare_pack_lists(left[field], right[field])
        elif field == "direct_84":
            result = ((left["direct_84_players"], left["direct_84_rating_sum"])
                      > (right["direct_84_players"], right["direct_84_rating_sum"])) - (
                      (left["direct_84_players"], left["direct_84_rating_sum"])
                      < (right["direct_84_players"], right["direct_84_rating_sum"]))
        elif field == "below_84":
            result = ((left["below_84_players"], left["below_84_rating_sum"])
                      > (right["below_84_players"], right["below_84_rating_sum"])) - (
                      (left["below_84_players"], left["below_84_rating_sum"])
                      < (right["below_84_players"], right["below_84_rating_sum"]))
        else:
            result = (left[field] > right[field]) - (left[field] < right[field])
        if result:
            return result
    return 0


def build_daily_plan(interpreted: dict, state: dict, excluded_modes: set[str],
                     priority: str, now: str, reviewed_rules: dict | None = None) -> dict:
    if priority not in PRIORITIES:
        raise ValueError("Invalid reward priority")
    interpreted = _with_reviewed_rules(interpreted, reviewed_rules or REVIEWED_RULES)
    view = _active_view(interpreted, state, now, excluded_modes, priority)
    plan = build_plan(interpreted, view, ALL_MODES, excluded_modes)
    groups, tasks = _task_map(interpreted)
    progress = _task_progress(view)
    recipes = _run_recipes(plan, tasks, groups, progress, excluded_modes)
    # Recommendations are one itinerary. Each recipe already represents a
    # distinct game; expose only today's next ten and recompute after check-in.
    batch = _select_batch(recipes, tasks, groups, progress, priority)
    recipes_by_order = sorted(recipes, key=lambda item: item["run_order"])
    for index, recipe in enumerate(batch, 1):
        recipe["number"] = index
        recipe["expires_at"] = min((groups[o["group_id"]].get("expires_at") for o in recipe["objectives"]
                                    if groups[o["group_id"]].get("expires_at")), default=None)
        parts = []
        if recipe["score"]["direct_84_players"]:
            parts.append("84+ direct player reward")
        if recipe["score"]["packs"]:
            parts.append(f"{len(recipe['score']['packs'])} pack reward step(s)")
        if recipe["score"]["season_points"]:
            parts.append("Season Points")
        if not parts:
            parts.append(f"{len(recipe['objectives'])} objective step(s)")
        recipe["reason"] = "Advances " + ", ".join(parts)
    scheduled = {task_id for recipe in recipes_by_order for task_id in recipe["task_ids"]}
    unscheduled = [item for item in plan["unscheduled_tasks"] if item["task_id"] not in scheduled]
    modes = sorted({option["mode"] for recipe in batch for option in [recipe["route"]]})
    return {"as_of": now, "priority": priority, "recommendations": batch,
            "available_count": len(recipes), "has_more": len(recipes) > len(batch),
            "unscheduled_count": len(unscheduled), "excluded_modes": sorted(excluded_modes),
            "considered_modes": modes, "optimization": plan["combined_plan"]["optimization"],
            "batch_score": {key: sum(recipe["score"][key] if isinstance(recipe["score"][key], int) else 0
                                    for recipe in batch)
                            for key in ("direct_84_players", "direct_84_rating_sum", "season_points",
                                        "below_84_players", "below_84_rating_sum", "coins")}
            | {"pack_rewards": [pack["label"] for recipe in batch for pack in recipe["score"]["packs"]]},
            "note": "Results are conditional on completing each recipe; wins, access, and play time are not guaranteed."}


def complete_daily_batch(interpreted: dict, state: dict, excluded_modes: set[str],
                         priority: str, now: str, reviewed_rules: dict | None = None,
                         match_count: int = 1) -> dict:
    if not isinstance(match_count, int) or not 1 <= match_count <= 10:
        raise ValueError("Match count must be between 1 and 10")
    interpreted = _with_reviewed_rules(interpreted, reviewed_rules or REVIEWED_RULES)
    plan = build_daily_plan(interpreted, state, excluded_modes, priority, now, reviewed_rules)
    groups, tasks = _task_map(interpreted)
    view = _active_view(interpreted, state, now, excluded_modes, priority)
    progress = _task_progress(view)
    increments: dict[str, int] = {}
    for recipe in plan["recommendations"][:match_count]:
        for task_id in recipe["task_ids"]:
            group, task = tasks[task_id]
            target = task.get("target") or {}
            if target.get("unit") == "matches":
                increments[task_id] = increments.get(task_id, 0) + 1
            elif target.get("scope") == "cumulative" and target.get("unit") in ("goals", "assists"):
                per_match = max((condition.get("minimum_per_match", 1)
                                 for condition in task.get("conditions", [])
                                 if condition.get("type") in ("goals", "assists")), default=1)
                increments[task_id] = increments.get(task_id, 0) + per_match
    for task_id, amount in increments.items():
        group, task = tasks[task_id]
        before = progress.get(task_id) or {"count": 0, "completed": False}
        target = task.get("target") or {}
        count = before.get("count", 0) + amount
        done = bool(before.get("completed") or (target.get("count") and count >= target["count"]))
        from user_objectives import record_progress
        record_progress(state, interpreted, task_id, count=count, completed=done, updated_at=now)
    return state
