#!/usr/bin/env python3
"""Loopback-only UI for the existing FUT.GG interpretation and planning layers."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from urllib.parse import urlparse

from prize_summary import summarize
from daily_game_planner import PRIORITIES, REVIEWED_RULES, build_daily_plan, complete_daily_batch
from user_objectives import (correct_deadline, load_state, record_progress, save_state,
                             select, selected_view, unselect, utc, reconcile_repeats)

HERE = Path(__file__).resolve().parent
MODES = ("squad_battles", "rivals", "champions", "rush", "live_events",
         "pve_live_events", "pvp_live_events", "draft", "co_op", "fc_pro_open_ladder")
DEFAULT_PRIVATE = Path.home() / ".local" / "share" / "futgg-objectives"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def check_private_path(path: Path, source: Path) -> None:
    if path.resolve() in {source.resolve(), (source.parent / "fc27_objectives.json").resolve()}:
        raise ValueError("Private files cannot replace source exports")


def load_settings(path: Path) -> dict:
    settings = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
        "schema_version": 1, "available_modes": [], "excluded_modes": [],
        "reward_priority": "balanced", "reviewed_rules": REVIEWED_RULES, "cycles": {}}
    validate_settings(settings)
    return settings


def validate_settings(settings: dict) -> None:
    if not isinstance(settings, dict) or settings.get("schema_version") != 1:
        raise ValueError("Invalid private settings schema")
    settings.setdefault("reward_priority", "balanced")
    if settings["reward_priority"] not in PRIORITIES:
        raise ValueError("Invalid reward priority")
    settings.setdefault("reviewed_rules", REVIEWED_RULES)
    if not isinstance(settings["reviewed_rules"], dict):
        raise ValueError("Invalid reviewed rules")
    for key in ("available_modes", "excluded_modes"):
        values = settings.get(key)
        if not isinstance(values, list) or any(not isinstance(v, str) or v not in MODES for v in values):
            raise ValueError(f"Invalid {key}")
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate {key}")
    cycles = settings.get("cycles")
    if not isinstance(cycles, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in cycles.items()):
        raise ValueError("Invalid cycles")
    for start in cycles.values():
        utc(start)


class App:
    def __init__(self, source: Path, state: Path, settings: Path):
        self.source, self.state, self.settings = source, state, settings
        if state.resolve() == settings.resolve():
            raise ValueError("State and settings must have different paths")
        for path in (state, settings):
            check_private_path(path, source)
        self.lock = RLock()

    def snapshot(self) -> dict:
        with self.lock:
            return self._snapshot()

    def _snapshot(self) -> dict:
        interpreted = json.loads(self.source.read_text(encoding="utf-8"))
        state = load_state(self.state)
        settings = load_settings(self.settings)
        if reconcile_repeats(state, interpreted, settings["cycles"]):
            save_state(self.state, state)
        if settings["cycles"]:
            settings["cycles"] = {}
            save_state(self.settings, settings)
        view = selected_view(state, interpreted, now_utc())
        daily = build_daily_plan(interpreted, state, set(settings["excluded_modes"]),
                                 settings["reward_priority"], view["as_of"], settings["reviewed_rules"])
        raw_path = self.source.parent / "fc27_objectives.json"
        raw_mismatch = False
        if raw_path.exists():
            raw_mismatch = json.loads(raw_path.read_text(encoding="utf-8")).get("fetched_at") != interpreted["source_fetched_at"]
        return {"groups": [{**group, "prize": summarize(group)} for group in interpreted["groups"]],
                "removed_groups": interpreted.get("removed_groups", []),
                "view": view, "daily_plan": daily, "settings": settings, "mode_catalog": MODES,
                "source_mismatch": raw_mismatch, "source_changes": interpreted.get("changes")}

    def update(self, action: str, data: dict) -> dict:
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        with self.lock:
            interpreted = json.loads(self.source.read_text(encoding="utf-8"))
            state = load_state(self.state)
            settings = load_settings(self.settings)
            if reconcile_repeats(state, interpreted, settings["cycles"]):
                save_state(self.state, state)
            if settings["cycles"]:
                settings["cycles"] = {}
                save_state(self.settings, settings)
            timestamp = now_utc()
            if action == "select":
                group_id = str(data["group_id"])
                if type(data.get("selected")) is not bool:
                    raise ValueError("selected must be boolean")
                if data["selected"]:
                    select(state, interpreted, group_id, timestamp)
                else:
                    unselect(state, group_id)
                save_state(self.state, state)
            elif action == "progress":
                task_id = str(data["task_id"])
                group_id = task_id.split(":", 1)[0]
                if group_id not in state["selections"]:
                    raise ValueError("Select the group before recording progress")
                group = next((g for g in interpreted["groups"] if g["id"] == group_id), None)
                if group is None:
                    raise ValueError("Task is no longer listed")
                record_progress(state, interpreted, task_id, count=data["count"],
                                completed=data["completed"], updated_at=timestamp)
                save_state(self.state, state)
            elif action == "progress_batch":
                entries = data.get("entries")
                if not isinstance(entries, list) or not entries:
                    raise ValueError("A match check-in needs at least one progress update")
                candidate = deepcopy(state)
                for entry in entries:
                    if not isinstance(entry, dict):
                        raise ValueError("Invalid match check-in entry")
                    task_id = str(entry["task_id"])
                    group_id = task_id.split(":", 1)[0]
                    if group_id not in candidate["selections"]:
                        raise ValueError("Select each challenge before recording progress")
                    group = next((g for g in interpreted["groups"] if g["id"] == group_id), None)
                    if group is None:
                        raise ValueError("Task is no longer listed")
                    record_progress(candidate, interpreted, task_id, count=entry["count"],
                                    completed=entry["completed"], updated_at=timestamp)
                state = candidate
                save_state(self.state, state)
            elif action == "deadline":
                if data.get("source") != "fc27_in_game":
                    raise ValueError("Confirm that this expiry was observed in FC 27")
                correct_deadline(state, interpreted, str(data["group_id"]), data["expires_at"], timestamp)
                save_state(self.state, state)
            elif action == "settings":
                candidate = {"schema_version": 1, "available_modes": data["available_modes"],
                             "excluded_modes": data["excluded_modes"],
                             "reward_priority": data.get("reward_priority", settings["reward_priority"]),
                             "reviewed_rules": settings["reviewed_rules"],
                             "cycles": {}}
                validate_settings(candidate)
                save_state(self.settings, candidate)
            elif action == "daily_done":
                complete_daily_batch(interpreted, state, set(settings["excluded_modes"]),
                                     settings["reward_priority"], timestamp, settings["reviewed_rules"])
                save_state(self.state, state)
            else:
                raise ValueError("Unknown action")
            return self.snapshot()


def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, status: int, value: dict) -> None:
            body = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _allowed(self) -> bool:
            host = self.headers.get("Host", "")
            return host in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

        def do_GET(self) -> None:
            if not self._allowed():
                self.send_error(403)
                return
            path = urlparse(self.path).path
            if path == "/":
                asset, mime = "index.html", "text/html; charset=utf-8"
            elif path == "/app.js":
                asset, mime = "app.js", "text/javascript; charset=utf-8"
            elif path == "/style.css":
                asset, mime = "style.css", "text/css; charset=utf-8"
            elif path == "/ar.json":
                asset, mime = "ar.json", "application/json; charset=utf-8"
            elif path == "/api/snapshot":
                try:
                    self._json(200, app.snapshot())
                except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
                    self._json(500, {"error": str(exc)})
                return
            else:
                self.send_error(404)
                return
            body = (HERE / "web" / asset).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            if not self._allowed() or self.headers.get("Origin") not in {
                f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}:
                self.send_error(403)
                return
            action = urlparse(self.path).path.removeprefix("/api/")
            if action not in {"select", "progress", "progress_batch", "deadline", "settings", "daily_done"}:
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > 65536 or self.headers.get("Content-Type", "").split(";", 1)[0] != "application/json":
                    raise ValueError("Expected JSON body up to 64 KiB")
                data = json.loads(self.rfile.read(length))
                self._json(200, app.update(action, data))
            except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
                self._json(400, {"error": str(exc)})

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=HERE / "fc27_interpreted.json")
    parser.add_argument("--state", type=Path, default=DEFAULT_PRIVATE / "state.json")
    parser.add_argument("--settings", type=Path, default=DEFAULT_PRIVATE / "settings.json")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    app = App(args.source, args.state, args.settings)
    app.snapshot()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(app))
    print(f"FUT.GG objectives: http://127.0.0.1:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
