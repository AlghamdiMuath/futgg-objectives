"""Combine compatible objective tasks into shared, conditional match runs."""

from __future__ import annotations

from collections import defaultdict

DIFFICULTY = {name: index for index, name in enumerate(
    ("Beginner", "Amateur", "Semi-Pro", "Professional", "World Class", "Legendary", "Ultimate"))}
SEARCH_LIMIT = 200_000


def _route_key(option: dict) -> tuple[str, str | None]:
    return option["mode"], option["event"]


def _fits(task: dict, route: tuple[str, str | None]) -> bool:
    return any(option["mode"] == route[0] and
               (option["event"] is None or option["event"] == route[1])
               for option in task["options"])


def _difficulty(task: dict, route: tuple[str, str | None]) -> str | None:
    names = [option["minimum_difficulty"] for option in task["options"]
             if _route_key(option) == route or
             (option["mode"] == route[0] and option["event"] is None)]
    names = [name for name in names if name]
    return min(names, key=lambda name: DIFFICULTY.get(name, 100)) if names else None


def _squad_requirements(tasks: list[dict]) -> list[dict]:
    requirements = {}
    for task in tasks:
        for condition in task["conditions"]:
            if condition["type"] != "squad":
                continue
            key = (condition["slot"], condition["trait"])
            minimum = condition["minimum"]
            previous = requirements.get(key, 0)
            requirements[key] = "all" if minimum == "all" or previous == "all" else max(previous, minimum)
    return [{"slot": slot, "trait": trait, "minimum": count}
            for (slot, trait), count in sorted(requirements.items())]


def _player_roles(tasks: list[dict]) -> list[dict]:
    roles = {(condition["type"], condition["trait"])
             for task in tasks for condition in task["conditions"]
             if condition["type"] in ("scoring_player", "assisting_player")}
    return [{"role": role, "trait": trait} for role, trait in sorted(roles)]


def _trait_key(trait: str) -> str:
    return trait.lower().removesuffix(" players").removesuffix(" player").strip()


def _can_share(tasks: list[dict]) -> bool:
    # Treat different traits as distinct players. This conservative limit can
    # reject an overlap that a dual-eligible card would make possible.
    squad = [item for item in _squad_requirements(tasks)
             if item["slot"] == "starting_11" and isinstance(item["minimum"], int)]
    covered = {_trait_key(item["trait"]) for item in squad}
    extra_roles = {_trait_key(role["trait"]) for role in _player_roles(tasks)} - covered
    return sum(item["minimum"] for item in squad) + len(extra_roles) <= 11


def _candidate_routes(tasks: list[dict]) -> list[tuple[str, str | None]]:
    return sorted({_route_key(option) for task in tasks for option in task["options"]},
                  key=lambda key: (key[0], key[1] or ""))


def combine_tasks(separate_tasks: list[dict], cumulative_tasks: list[dict]) -> dict:
    """Minimize shared qualifying matches for separate-match tasks.

    Every per-match condition is assumed achievable in a qualifying game. The
    search is exact within that model unless the node limit is reached.
    Cumulative targets are attached to matching runs but have no match bound.
    """
    routes = _candidate_routes(separate_tasks + cumulative_tasks)
    ordered = sorted(separate_tasks, key=lambda task: (
        sum(_fits(task, route) for route in routes), -task["remaining"], task["task_id"]))
    candidates = [[route for route in routes if _fits(task, route)] for task in ordered]

    def choices_for(task: dict, choices: list[tuple], bins: list[dict]) -> list[tuple[int | None, tuple, int]]:
        result = []
        for index, bin_ in enumerate(bins):
            if bin_["route"] in choices and _can_share(bin_["tasks"] + [task]):
                result.append((index, bin_["route"],
                               max(bin_["count"], task["remaining"]) - bin_["count"]))
        for route in choices:
            if _can_share([task]):
                result.append((None, route, task["remaining"]))
        return sorted(result, key=lambda item: (item[2], item[0] is None,
                                                 item[1][0], item[1][1] or ""))

    def greedy() -> list[dict]:
        bins = []
        for task, choices in zip(ordered, candidates):
            viable = choices_for(task, choices, bins)
            if not viable:
                raise ValueError("No feasible squad configuration for a task")
            index, route, _ = viable[0]
            if index is None:
                bins.append({"route": route, "count": task["remaining"], "tasks": [task]})
            else:
                bins[index]["tasks"].append(task)
                bins[index]["count"] = max(bins[index]["count"], task["remaining"])
        return bins

    best_bins = greedy()
    best_cost = sum(bin_["count"] for bin_ in best_bins)
    bins: list[dict] = []
    nodes = 0
    limited = False

    def search(index: int, cost: int) -> None:
        nonlocal best_bins, best_cost, nodes, limited
        nodes += 1
        if nodes > SEARCH_LIMIT:
            limited = True
            return
        if cost > best_cost:
            return
        if index == len(ordered):
            if cost < best_cost or (cost == best_cost and len(bins) < len(best_bins)):
                best_cost = cost
                best_bins = [{"route": bin_["route"], "count": bin_["count"],
                              "tasks": list(bin_["tasks"])} for bin_ in bins]
            return
        task = ordered[index]
        for bin_index, route, delta in choices_for(task, candidates[index], bins):
            if bin_index is None:
                bins.append({"route": route, "count": task["remaining"], "tasks": [task]})
                search(index + 1, cost + delta)
                bins.pop()
            else:
                bin_ = bins[bin_index]
                old = bin_["count"]
                bin_["count"] = max(old, task["remaining"])
                bin_["tasks"].append(task)
                search(index + 1, cost + delta)
                bin_["tasks"].pop()
                bin_["count"] = old
            if limited:
                return

    search(0, 0)
    remaining_cumulative = []
    bonuses: dict[int, list[dict]] = defaultdict(list)
    for task in cumulative_tasks:
        compatible = [index for index, bin_ in enumerate(best_bins)
                      if _fits(task, bin_["route"]) and
                      _can_share(bin_["tasks"] + bonuses[index] + [task])]
        if compatible:
            for index in compatible:
                bonuses[index].append(task)
        else:
            remaining_cumulative.append(task["task_id"])

    runs = []
    for index, bin_ in sorted(enumerate(best_bins), key=lambda pair: (pair[1]["route"][0],
                                                                 pair[1]["route"][1] or "", pair[0])):
        route = bin_["route"]
        tasks = bin_["tasks"]
        all_tasks = tasks + bonuses[index]
        levels = [_difficulty(task, route) for task in all_tasks]
        levels = [level for level in levels if level]
        runs.append({
            "mode_option": {"mode": route[0], "event": route[1],
                            "minimum_difficulty": max(levels, key=lambda n: DIFFICULTY.get(n, 100)) if levels else None},
            "qualifying_matches": bin_["count"],
            "group_ids": sorted({task["group_id"] for task in all_tasks}),
            "squad_requirements": _squad_requirements(all_tasks),
            "player_roles": _player_roles(all_tasks),
            "match_tasks": [{"group_id": task["group_id"], "task_id": task["task_id"],
                             "source_text": task["source_text"], "remaining_qualifying_matches": task["remaining"],
                             "conditions": task["conditions"]} for task in tasks],
            "cumulative_targets": [{"group_id": task["group_id"], "task_id": task["task_id"],
                                    "source_text": task["source_text"], "target": task["target"],
                                    "remaining": task["remaining"], "conditions": task["conditions"]}
                                   for task in bonuses[index]],
        })
    return {"runs": runs, "qualifying_match_count": best_cost,
            "optimization": "search_limited" if limited else "exact_for_separate_matches",
            "cumulative_without_run": remaining_cumulative}
