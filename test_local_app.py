"""Local UI API integration tests using isolated private files."""

import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from local_app import App, make_handler


SOURCE = Path(__file__).parent / "fc27_interpreted.json"


class LocalAppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.source = root / "fc27_interpreted.json"
        self.source.write_bytes(SOURCE.read_bytes())
        self.app = App(self.source, root / "private" / "state.json", root / "private" / "settings.json")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.app))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def request(self, path, data=None, origin=True):
        headers = {}
        if data is not None:
            headers["Content-Type"] = "application/json"
            if origin:
                headers["Origin"] = self.origin
        req = Request(self.origin + path, json.dumps(data).encode() if data is not None else None, headers)
        try:
            with urlopen(req) as response:
                return response.status, json.loads(response.read()) if path.startswith("/api/") else response.read()
        except HTTPError as exc:
            return exc.code, json.loads(exc.read()) if exc.headers.get("Content-Type", "").startswith("application/json") else {}

    def test_selection_progress_cycles_and_exports_stay_separate(self):
        original = self.source.read_bytes()
        status, data = self.request("/api/select", {"group_id": "61", "selected": True})
        self.assertEqual(status, 200)
        self.assertEqual(data["view"]["selected_groups"][0]["availability"], "active")
        status, data = self.request("/api/progress", {"task_id": "61:464", "count": 1, "completed": True})
        self.assertEqual(status, 400)
        self.assertIn("cycle start", data["error"])
        cycle = "2026-09-27T07:00:00Z"
        status, data = self.request("/api/settings", {"available_modes": ["rush"], "excluded_modes": [], "cycles": {"61": cycle}})
        self.assertEqual(status, 200)
        status, data = self.request("/api/progress", {"task_id": "61:464", "count": 1, "completed": True})
        self.assertEqual(status, 200)
        self.assertEqual(data["view"]["selected_groups"][0]["tasks"][0]["progress_key"], "61:464@" + cycle)
        self.assertTrue(any(t["task_id"] == "61:464" for t in data["plan"]["completed_tasks"]))
        self.assertEqual(self.source.read_bytes(), original)
        self.assertTrue(self.app.state.exists())
        self.assertTrue(self.app.settings.exists())
        self.assertEqual(self.app.state.stat().st_mode & 0o777, 0o600)

    def test_match_checkin_saves_multiple_task_updates_in_one_request(self):
        self.request("/api/select", {"group_id": "94", "selected": True})
        status, data = self.request("/api/progress_batch", {"entries": [
            {"task_id": "94:1696", "count": 1, "completed": False},
            {"task_id": "94:1695", "count": 1, "completed": False}]})
        self.assertEqual(status, 200)
        progress = {task["id"]: task["progress"]["count"] for task in
                    data["view"]["selected_groups"][0]["tasks"] if task["progress"]}
        self.assertEqual(progress, {"94:1696": 1, "94:1695": 1})

        saved_state = self.app.state.read_bytes()
        status, _ = self.request("/api/progress_batch", {"entries": [
            {"task_id": "94:1696", "count": 2, "completed": False},
            {"task_id": "94:1695", "count": -1, "completed": False}]})
        self.assertEqual(status, 400)
        self.assertEqual(self.app.state.read_bytes(), saved_state)

    def test_deadline_conflicts_and_source_changes_are_visible(self):
        self.request("/api/select", {"group_id": "25", "selected": True})
        status, data = self.request("/api/deadline", {"group_id": "25", "expires_at": "2026-10-02T17:00:00Z", "source": "fc27_in_game"})
        self.assertEqual(status, 200)
        self.assertEqual(data["view"]["selected_groups"][0]["effective_expires_at"], "2026-10-02T17:00:00Z")
        status, data = self.request("/api/deadline", {"group_id": "25", "expires_at": "2026-10-03T17:00:00Z", "source": "fc27_in_game"})
        self.assertEqual(status, 200)
        self.assertIn("conflicting_user_deadlines", data["view"]["selected_groups"][0]["review_flags"])
        self.assertIsNone(data["view"]["selected_groups"][0]["effective_expires_at"])
        interpreted = json.loads(self.source.read_text())
        group = next(g for g in interpreted["groups"] if g["id"] == "25")
        group["source_fingerprint"] = "changed"
        interpreted["changes"] = [{"group_id": "25", "change": "updated", "fields": ["description"], "task_ids": []}]
        self.source.write_text(json.dumps(interpreted))
        _, data = self.request("/api/snapshot")
        self.assertIn("source_group_changed", data["view"]["selected_groups"][0]["review_flags"])
        self.assertEqual(data["source_changes"][0]["group_id"], "25")

    def test_rejects_unconfirmed_deadline_and_cross_origin_write(self):
        status, _ = self.request("/api/deadline", {"group_id": "25", "expires_at": "2026-10-02T17:00:00Z"})
        self.assertEqual(status, 400)
        status, _ = self.request("/api/select", {"group_id": "25", "selected": True}, origin=False)
        self.assertEqual(status, 403)
        self.assertFalse(self.app.state.exists())

    def test_snapshot_includes_label_only_prizes(self):
        status, data = self.request("/api/snapshot")
        self.assertEqual(status, 200)
        groups = {group["id"]: group for group in data["groups"]}
        self.assertEqual(groups["113"]["prize"]["main"]["label"], "Shunsuke Mito")
        self.assertIsNone(groups["113"]["prize"]["rating"])
        self.assertEqual(groups["113"]["prize"]["pack_quality"], {"minimum_rating": 83, "player_count": 4})
        self.assertEqual(groups["87"]["prize"]["coins"], 16000)
        self.assertEqual(groups["81"]["prize"]["other_players"], ["Jesús Corona"])
        self.assertEqual(groups["72"]["prize"]["pack_quality"]["minimum_rating"], 84)

    def test_arabic_catalog_is_served_without_changing_source(self):
        original = self.source.read_bytes()
        status, body = self.request("/ar.json")
        self.assertEqual(status, 200)
        catalog = json.loads(body)
        self.assertIn("Daily Objectives", catalog)
        self.assertEqual(self.source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
