"""Regression checks for the page fields the daily export depends on."""

import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import fetch_futgg_objectives as fetcher


LISTING = '''
<h1>EA SPORTS FC 27 Objectives</h1>
<a href="/objectives/seasonal/94-squad-battles/"><h3>Squad Battles</h3><p>Play matches.</p></a>
<script>eaId:94,slug:"94-squad-battles",name:"Squad Battles",categoryEaId:3,
description:"Play matches.",startTime:"2026-09-27T07:00:00Z",endTime:"2026-10-04T06:59:59Z"</script>
'''

DETAIL = '''
<h1>Squad Battles - EA SPORTS FC 27 Objectives</h1>
<div class="group/sbc"><h3>Squad Battles</h3><p>Play matches.</p>
<span class="font-bold text-center text-gray-300">100 Points</span>
<span class="font-bold text-gray-300">10 SP</span></div>
<div class="group/sbc"><h4>Win 3</h4><p>Win 3 matches in Squad Battles.</p>
<span class="font-bold text-center text-gray-300">50 Points</span></div>
<script>eaId:94,slug:"94-squad-battles",name:"Squad Battles",categoryEaId:3,
description:"Play matches.",startTime:"2026-09-27T07:00:00Z",endTime:"2026-10-04T06:59:59Z",
groupEaId:94,eaId:1696,name:"Win 3"</script>
'''


class FetcherTests(unittest.TestCase):
    def test_dates_and_stable_task_id(self):
        group = fetcher.parse_listing(LISTING)[0]
        fetcher.parse_detail(DETAIL, group)
        self.assertEqual(group["expires_at"], "2026-10-04T06:59:59Z")
        self.assertEqual(group["tasks"][0]["id"], "94:1696")
        self.assertEqual(group["tasks"][0]["rewards"], ["50 Points"])
        self.assertEqual(group["completion_rewards"], ["100 Points", "10 SP"])

    def test_missing_dates_fail_instead_of_silent_null(self):
        with self.assertRaisesRegex(ValueError, "Missing start/end times"):
            fetcher.parse_listing(LISTING.replace('endTime:"2026-10-04T06:59:59Z"', ""))

    def test_no_published_expiry_is_null(self):
        listing = LISTING.replace('endTime:"2026-10-04T06:59:59Z"', "endTime:null")
        self.assertIsNone(fetcher.parse_listing(listing)[0]["expires_at"])

    def test_task_identity_mismatch_fails(self):
        group = fetcher.parse_listing(LISTING)[0]
        with self.assertRaisesRegex(ValueError, "Task titles disagree"):
            fetcher.parse_detail(DETAIL.replace('name:"Win 3"', 'name:"Win 5"'), group)

    def test_failed_refresh_keeps_previous_export(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "objectives.json"
            output.write_text('{"groups": [{"id": "old"}]}', encoding="utf-8")
            with patch.object(sys, "argv", ["fetcher", "--output", str(output)]), patch.object(
                fetcher, "fetch_html", side_effect=[LISTING, DETAIL.replace('name:"Win 3"', 'name:"Win 5"')]
            ), patch.object(fetcher.time, "sleep"), redirect_stderr(StringIO()):
                self.assertEqual(fetcher.main(), 1)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["groups"][0]["id"], "old")

    def test_suspicious_group_drop_keeps_previous_export(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "objectives.json"
            original = {"groups": [{"id": str(index)} for index in range(3)]}
            output.write_text(json.dumps(original), encoding="utf-8")
            with patch.object(sys, "argv", ["fetcher", "--output", str(output)]), patch.object(
                fetcher, "fetch_html", return_value=LISTING
            ) as fetch_html, redirect_stderr(StringIO()):
                self.assertEqual(fetcher.main(), 1)
            fetch_html.assert_called_once_with(fetcher.LIST_URL)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), original)

    def test_removed_groups_keep_last_known_deadline(self):
        previous = {
            "fetched_at": "2026-09-26T00:00:00Z",
            "groups": [
                {"id": "94", "title": "Squad Battles", "expires_at": "2099-01-01T00:00:00Z"},
                {"id": "77", "title": "Expired objective", "expires_at": "2020-01-01T00:00:00Z"},
                {"id": "78", "title": "Removed early", "expires_at": "2099-01-01T00:00:00Z"},
            ],
        }
        removed = fetcher.removed_groups(previous, [{"id": "94"}], "2026-09-27T00:00:00Z")
        self.assertEqual([(x["id"], x["availability"]) for x in removed], [("77", "expired"), ("78", "unlisted")])
        self.assertEqual(removed[0]["last_seen_at"], "2026-09-26T00:00:00Z")
        self.assertEqual(removed[0]["expires_at"], "2020-01-01T00:00:00Z")
        later = fetcher.removed_groups(
            {"fetched_at": "2026-09-27T00:00:00Z", "groups": [{"id": "94"}], "removed_groups": removed},
            [{"id": "94"}],
            "2026-09-28T00:00:00Z",
        )
        self.assertEqual(later[0]["first_missing_at"], "2026-09-27T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
