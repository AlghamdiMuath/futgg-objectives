# FUT.GG FC 27 objective export

## Phone site

Open **https://alghamdimuath.github.io/futgg-objectives/** on your phone.

The hosted version is built by `python3 build_site.py` and published from `dist/` through GitHub Pages. It runs the Python interpretation and planning modules in the browser using Pyodide, so reward preferences, excluded modes, reviewed rules, selections, deadline observations, and progress stay in that browser's local storage. They are not shared with the loopback app or another phone. In **My list → Your data**, download a backup before changing phones or clearing browser storage; import that backup on the new device.

The GitHub Actions workflow in `.github/workflows/publish.yml` fetches FUT.GG every day at **21:30 Asia/Riyadh** (18:30 UTC), interprets the data, updates Arabic translations when the translation service is available, verifies the project, and republishes the site. It also runs on pushes to `main` and can be run manually. A failed FUT.GG fetch leaves the previous published site in place. The exact release time for new objectives is not guaranteed, so the scheduled time is a daily check rather than a reset boundary for in-game progress.

## Run the local app

From this directory in WSL or Linux, install and start the app:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python local_app.py
```

Open **http://127.0.0.1:8765/** on the same laptop. Stop the server with Ctrl+C. The server binds only to loopback. By default, selections and any older private data live in `~/.local/share/futgg-objectives/state.json`. You can override the private paths with `--state /private/path/state.json --settings /private/path/settings.json`; `--port` changes the local port.

The default **Today** screen shows one match to play next, with its route, starting squad, and key actions. Choose a **Reward** to include only challenges that award that reward, or keep **Any reward**; exclude modes you cannot play. Either choice updates the plan automatically. The planner suggests only the matches currently needed, up to a maximum of ten at a time. Cumulative goals and assists without a reliable match count get one suggestion, then the route is recalculated from recorded progress. After meeting the listed conditions, **I completed this match as planned** records progress for that one match and generates the next recommendation. Wins and event access remain conditional. The planner excludes Milestones and Mastery; **Browse** and **My list** contain the full challenge catalog and source rules. A unique replacement for a selected repeat challenge is selected automatically when FUT.GG publishes it.

The **Language** control switches the app between English and Arabic and remembers the choice in this browser. Arabic uses right-to-left layout, and search accepts text in either language. FUT.GG currently publishes the objective pages used here in English. `web/ar.json` is a separate, machine-translated Arabic display catalog with reviewed corrections for current challenge names and key rules; it is not an original FUT.GG Arabic feed. The English source instruction remains visible beneath translated tasks. English text is always used for rule interpretation, source-change detection, and saved progress. A newly published or changed English string appears in English until its Arabic translation is added.

The main card prize comes from the published group completion rewards. Coin and pack highlights and sorting use the largest **single** prize of each type in the group completion and available reward labels. They are not totals or guaranteed earnings. Pack sorting uses the printed minimum player rating first, then the printed players per pack; packs without a minimum rating sort after comparable packs. Player names in the current export have no ratings, so the cards say **Rating unknown** and player-rating sorting leaves those challenges unranked. Unknown or disputed deadlines are labeled **Unknown** or **Review** and sort after known expiries. These labels never infer ratings, pack contents, or reset dates.

Daily and weekly objectives need no date entry. Recorded private progress affects the next recommendation batch. If FUT.GG republishes identical tasks and start time across an in-game reset, the app cannot detect that reset.

The UI displays published listing deadlines but has no date entry. The underlying CLI and API retain previously saved deadline evidence for compatibility; the daily planner uses the current published objectives.

Refresh the public export and interpretation from this directory, then click **Reload exports** in the app:

```bash
cp fc27_objectives.json /tmp/fc27-objectives-before-refresh.json
.venv/bin/python fetch_futgg_objectives.py --output fc27_objectives.json
.venv/bin/python interpret_objectives.py --input fc27_objectives.json --output fc27_interpreted.json --previous /tmp/fc27-objectives-before-refresh.json
.venv/bin/python translate_objectives.py --input fc27_interpreted.json --output web/ar.json
```

The translator sends only public source strings to Google Translate, reuses existing catalog entries, and writes the catalog atomically after each batch. Review new Arabic task wording before relying on it, especially quantities, "per match" conditions, player traits, and difficulty. The interpreter's `changes` report records added, removed, and changed source records. If the raw and interpreted exports have different fetch times, the app shows a warning until interpretation is rerun. Refresh reconciles private repeat selections and progress against changed published objectives. The public pages do not confirm every task rule or reset boundary; review flagged tasks.

Run all tests and syntax checks:

```bash
.venv/bin/python -m unittest discover -s . -p 'test_*.py'
.venv/bin/python -m py_compile local_app.py prize_summary.py user_objectives.py plan_objectives.py optimize_matches.py daily_game_planner.py interpret_objectives.py fetch_futgg_objectives.py translate_objectives.py browser_api.py build_site.py
node --check web/app.js
node --test test_plan_ui.js
```

The Node.js commands check browser JavaScript syntax and the Plan presentation rules; the app itself does not need Node.js.

Fetches the public [FUT.GG objective listing](https://www.fut.gg/objectives/) and each linked objective group. The output contains group IDs, categories, descriptions, exact UTC start and expiry times, completion rewards, all listed rewards, total Season Points when shown, and each task's text and rewards. Task progress is personal data and is not available from these public pages.

```bash
python3 -m pip install -r requirements.txt
python3 fetch_futgg_objectives.py --output fc27_objectives.json
```

For a quick live check, use `--limit 2 --output /tmp/fc27-smoke.json` with a new output path. The script waits 0.5 seconds between detail pages by default. It fetches public HTML pages only, makes no authenticated requests, and fails without replacing an existing output file if a page cannot be parsed. It also rejects a listing that drops below half the previous group count; `--allow-large-drop` overrides this after checking that a major expiry was real.

`expires_at` is an ISO 8601 UTC timestamp or `null` when FUT.GG publishes no end time. Filter any group with `expires_at <= now` at read time, even between daily runs. `fetched_at` lets the app detect an overdue refresh. Task IDs combine the group ID with FUT.GG's source task ID, so rearranging cards does not reset user progress.

`groups` contains objectives currently listed by FUT.GG. `removed_groups` retains last-known metadata after a successful refresh stops listing a group. Each record has `last_seen_at`, `first_missing_at`, and `availability`: `expired` when the published deadline has passed, or `unlisted` when it has not. A selected `unlisted` group is shown as unavailable without claiming it expired. Restored groups leave `removed_groups` automatically. The app keeps user selections and task progress in its own private state, keyed by these IDs.

Run the command once a day from a scheduler and alert on a nonzero exit status or an old `fetched_at`. The script is a one-shot job; it does not install a scheduler. Its JSON output is replaced atomically only after every detail page passes validation. Repeated runs produce the same IDs and field structure, with a new `fetched_at`.

This is the raw source layer. The interpreter derives task mode, squad, event, difficulty, and match count restrictions before the planner honors exclusions such as “no Rivals” or combines tasks. The source pages provide these mostly as prose, so uncertain interpretations remain flagged for review. Daily and weekly groups may reuse the same IDs across resets, so progress storage needs an explicit completion period; the source pages do not provide a reliable reset schedule for every group.

## Interpreted requirements

Generate the separate, derived layer after a successful fetch:

```bash
python3 interpret_objectives.py --input fc27_objectives.json --output fc27_interpreted.json
```

The output is a disposable cache, not user storage. Its `schema_version` is `1`; `source_schema_version` and `source_fetched_at` identify the raw export. `groups` retains the source ID, title, description, URL, UTC dates, group completion rewards, available rewards, and total Season Points. `removed_groups` carries the fetcher's last-known availability records through unchanged. Group and task `source_fingerprint` values change when relevant source content changes. No selection or personal progress belongs in either export.

Each task retains its ID, title, exact `source_text`, and reward labels. `kind` is `match`, `checklist`, or `dependency`. `status` is `parsed` or `review`, with machine-readable `review_reasons`. Consumers must show the original text and must not schedule a `review` task as if its uncertain fields were confirmed. Checklist `action` is the original instruction; when a safe numeric target is found, `target` adds `unit`, `count`, and `scope` for display or manual progress. A checklist can always be checked off manually.

For match tasks, `target.scope` is `separate_matches` or `cumulative`. A separate-match target counts distinct games, and conditions such as `{type: "goals", minimum_per_match: 2}` must hold within each counted game. A cumulative goal or assist target totals events across eligible games. `conditions` also holds win results, scoring-player traits, starting-squad traits, goal style/location, team credit, and assist source. There is no match formation restriction in this export; changing club formation is a checklist action. Event names are preserved in `mode_options[].event` rather than inferred from the event title's implied difficulty.

`mode_options` is an OR list. `minimum_difficulty` applies only to its own option. `any_fut` is a wildcard: expand it against the application's actual mode catalog and apply exclusions before proposing games. `eligible_mode_options(options, excluded, available_modes)` performs that filtering; an empty result means no permitted route is known. This preserves Rivals, Champions, Live Events, and Rush alternatives when Squad Battles is excluded. The catalog must come from the app, since FUT.GG does not enumerate every mode covered by “any FUT game mode.”

Dependencies use `dependency.group_id`, `completions`, and `distinct_periods`. A completionist target of four weekly completions requires four distinct weekly instances, not four checks of one instance. `prerequisites` records confirmed access qualifications only when the rule has been verified; otherwise it retains `status: review`.

### Reset periods and changes

`repeat.cadence` is `daily`, `weekly`, or `null`; it is a label derived from the group title. The group `starts_at` and `expires_at` values span publication/availability and are not reset boundaries. Repeat progress is keyed by task ID and a published objective identity built from group ID, start time, and task IDs and wording. Nonrepeat progress remains keyed by task ID. Changed repeat identities discard old progress; unchanged listings retain it.

Call `changes(previous_raw_export, current_raw_export)` after a successful refresh, or pass `--previous old_raw.json` to include a change report in the interpreted output. The report identifies added/removed groups and changed group fields or task IDs. Refresh affected plans when text, deadlines, rewards, or availability change. Recheck expiry against the current UTC time at read time, as the fetcher README notes. A changed task fingerprint can trigger review of stored progress semantics while leaving the user's stored selection and progress untouched.

The remaining task-rule review case is whether “Score 20 goals in any Live Events match (or Rivals/Squad Battles)” (`25:140`) means one match or a cumulative total. The public pages do not give reliable reset times for repeat groups, so unchanged listings cannot trigger a progress reset.

```bash
python3 -m unittest discover -s . -p 'test_*.py'
```

## Private selections and progress

`user_objectives.py` reads the interpreted export and writes a **separate private JSON file**. Keep that file outside the exported data and out of any published repository. The fetcher and interpreter never read or write it. For example:

```bash
python3 user_objectives.py --state ~/fc27-user-state.json select 25
python3 user_objectives.py --state ~/fc27-user-state.json deadline 25 2026-10-02T17:00:00Z
python3 user_objectives.py --state ~/fc27-user-state.json progress 25:141 1 --completed
python3 user_objectives.py --state ~/fc27-user-state.json view
```

A deadline entered with `deadline` is an **FC 27 in-game expiry correction** for the objective group, never a personal target date. The command requires an explicit UTC timestamp (`Z` or `+00:00`). Each observation is stored under `deadline_corrections[group_id]` with `expires_at`, `source: "fc27_in_game"`, and `recorded_at`. Previous observations remain intact. The view returns the raw `source_expires_at`, every correction, and `effective_expires_at`. A published FUT.GG deadline takes precedence when present; a different correction raises `source_deadline_conflict`. If FUT.GG has no deadline and user observations disagree, the effective deadline is `null`, availability is `needs_review`, and `conflicting_user_deadlines` is raised. A matching later FUT.GG deadline resolves the source conflict without deleting the observation.

Private storage schema version 1 has three maps: `selections[group_id]` stores the selection and repeat source identity; `deadline_corrections[group_id]` stores expiry observations; and `progress[progress_key]` stores manual count, completion, update time, and original task text. Repeat progress keys include the published objective identity. Writes replace the private state atomically.

`view` produces JSON with `schema_version`, `as_of`, `source_fetched_at`, and `selected_groups`. Each group has `availability` (`active`, `upcoming`, `expired`, `unlisted`, `missing`, or `needs_review`), the two deadline values and correction list, `review_flags`, `tasks`, and `unmatched_progress`. `expired` is evaluated against `as_of` on every read, including for unlisted groups. `unlisted` means FUT.GG removed a group before its effective expiry. `missing` means no active or retained source record exists. `source_group_changed`, `source_task_changed`, and `stored_task_unlisted` flag source changes without resetting private data. Task entries give the current `source_text`, the applicable `progress_key`, progress for that key only, and review flags. `unmatched_progress` exposes saved records whose task ID no longer appears in an active selected group. The returned view is derived output; do not save it over either source export.

For repeat objectives, record progress without a date. For example:

```bash
python3 user_objectives.py --state ~/fc27-user-state.json progress 61:464 1 --completed
python3 user_objectives.py --state ~/fc27-user-state.json view
```

When a newly published repeat objective changes identity, the app removes the old progress and automatically selects a unique replacement with the same title and cadence. Manual count is a user-entered quantity; this layer does not verify match eligibility or derive a reset schedule.

Verification: `python3 -m unittest discover -s . -p 'test_*.py'` covers deadline evidence, repeat source changes, replacement selection, match planning, and private-state round trips.

## Daily Game Planner

The **Today** screen builds a route from active objective groups matching the chosen reward, current progress, and excluded modes. It shows the next match and its concise conditions. Recording a completed match advances only the first recommended match and refreshes the route. The recommendation logic uses the match eligibility and compatibility helpers in `plan_objectives.py` and `optimize_matches.py`; those modules are internal and no longer provide a separate Plan screen or command-line planner.
