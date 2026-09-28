# FUT.GG FC 27 objective export

## Phone site

Open **https://alghamdimuath.github.io/futgg-objectives/** on your phone.

The hosted version is built by `python3 build_site.py` and published from `dist/` through GitHub Pages. It runs the existing Python interpretation and planning modules in the browser using Pyodide, so selections, settings, deadline observations, and progress stay in that browser's local storage. They are not shared with the loopback app or another phone. In **Settings → Your data**, download a backup before changing phones or clearing browser storage; import that backup on the new device.

The GitHub Actions workflow in `.github/workflows/publish.yml` fetches FUT.GG every day at **21:30 Asia/Riyadh** (18:30 UTC), interprets the data, updates Arabic translations when the translation service is available, verifies the project, and republishes the site. It also runs on pushes to `main` and can be run manually. A failed FUT.GG fetch leaves the previous published site in place. The exact release time for new objectives is not guaranteed, so the scheduled time is a daily check rather than a reset boundary for in-game progress.

## Run the local app

From this directory in WSL or Linux, install and start the app:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python local_app.py
```

Open **http://127.0.0.1:8765/** on the same laptop. Stop the server with Ctrl+C. The server binds only to loopback. By default, private selections and progress live in `~/.local/share/futgg-objectives/state.json`; mode choices and explicitly entered cycle starts live in `~/.local/share/futgg-objectives/settings.json`. These files are separate from both exports. You can override them with `--state /private/path/state.json --settings /private/path/settings.json`; `--port` changes the local port.

The phone-first **Browse** screen has search, category and availability filters, reward-type chips (**All**, **Players**, **Coins**, **Packs**), and sorting by soonest expiry, highest player rating, most coins, or best pack quality. **Reward leaders** shows the largest listed coin prize and highest rated pack among the current search and category results; tap one to see that reward type first. Cards show the challenge name, days left, completion prize, and other listed player, coin, or rated pack rewards. A player appearing only in available rewards is named on the card. Open **Tasks & details** for source text, deadline evidence, and task controls; **+ Add to list** puts a challenge in **My list**, where progress remains easy to reach. **Plan** puts a suggested next run first, with its route, match count, starting lineup, and short task checklist. Expand a task for original wording and interpreted conditions, or open the lower sections for cumulative targets, tasks needing review, and completed work. When the planner finds multiple compatible routes for a run, choose one in the run card; that choice stays in this browser while it remains compatible. **Record progress** opens the relevant challenge in **My list**. **Settings** holds available modes, exclusions, and current cycle starts. Use **Refresh** after updating the exports.

The **Language** control switches the app between English and Arabic and remembers the choice in this browser. Arabic uses right-to-left layout, and search accepts text in either language. FUT.GG currently publishes the objective pages used here in English. `web/ar.json` is a separate, machine-translated Arabic display catalog with reviewed corrections for current challenge names and key rules; it is not an original FUT.GG Arabic feed. The English source instruction remains visible beneath translated tasks. English text is always used for rule interpretation, source-change detection, and saved progress. A newly published or changed English string appears in English until its Arabic translation is added.

The main card prize comes from the published group completion rewards. Coin and pack highlights and sorting use the largest **single** prize of each type in the group completion and available reward labels. They are not totals or guaranteed earnings. Pack sorting uses the printed minimum player rating first, then the printed players per pack; packs without a minimum rating sort after comparable packs. Player names in the current export have no ratings, so the cards say **Rating unknown** and player-rating sorting leaves those challenges unranked. Unknown or disputed deadlines are labeled **Unknown** or **Review** and sort after known expiries. These labels never infer ratings, pack contents, or reset dates.

For daily or weekly objectives, enter the current cycle start in **Settings** as an explicitly known UTC time such as `YYYY-MM-DDTHH:MM:SSZ` before saving progress. The app never derives it from publication or expiry timestamps. A later cycle has separate progress, and old records remain in private storage. Set available modes and optional exclusions there too; the plan starts with no assumed available modes.

To correct a deadline, expand an objective and enter only an expiry you observed **in FC 27**, in UTC. The app retains every observation. A published FUT.GG expiry takes precedence; a disagreement appears as a conflict and holds affected tasks out of match blocks. When no published expiry exists and observations disagree, no effective deadline is chosen. The selected view also displays changed source groups, changed task text, and removed tasks without discarding prior progress. The plan shows qualifying match blocks, completed tasks, unavailable groups, and unscheduled tasks with their reasons. Match counts are conditional qualifying outcomes, not predicted attempts or time.

Refresh the public export and interpretation from this directory, then click **Reload exports** in the app:

```bash
cp fc27_objectives.json /tmp/fc27-objectives-before-refresh.json
.venv/bin/python fetch_futgg_objectives.py --output fc27_objectives.json
.venv/bin/python interpret_objectives.py --input fc27_objectives.json --output fc27_interpreted.json --previous /tmp/fc27-objectives-before-refresh.json
.venv/bin/python translate_objectives.py --input fc27_interpreted.json --output web/ar.json
```

The translator sends only public source strings to Google Translate, reuses existing catalog entries, and writes the catalog atomically after each batch. Review new Arabic task wording before relying on it, especially quantities, "per match" conditions, player traits, and difficulty. The interpreter's `changes` report records added, removed, and changed source records. If the raw and interpreted exports have different fetch times, the app shows a warning until interpretation is rerun. Refresh does not modify private files. The public pages do not confirm every task rule or reset boundary; review flagged tasks and supply cycle starts only when known.

Run all tests and syntax checks:

```bash
.venv/bin/python -m unittest discover -s . -p 'test_*.py'
.venv/bin/python -m py_compile local_app.py prize_summary.py user_objectives.py plan_objectives.py optimize_matches.py interpret_objectives.py fetch_futgg_objectives.py translate_objectives.py
node --check web/app.js
```

`node --check` needs Node.js and only checks browser JavaScript syntax; the app itself does not need Node.js.

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

Dependencies use `dependency.group_id`, `completions`, and `distinct_periods`. A completionist target of four weekly completions requires four distinct weekly instances, not four checks of one instance. `prerequisites` records a possible access qualification only with `status: review` where the source wording does not prove a strict task dependency.

### Reset periods and changes

`repeat.cadence` is `daily`, `weekly`, or `null`; it is a label derived from the group title. `repeat.reset_schedule` remains `null` until an authoritative reset schedule is supplied. The group `starts_at` and `expires_at` values span publication/availability and **must not** be used as daily or weekly reset boundaries. Store private progress under `(task_id, cycle_start_utc)` for repeat tasks, and under `task_id` for nonrepeat tasks. `progress_key()` refuses to make a repeat key without an explicit cycle start. Keep completed old cycles for completionist dependencies, but never read their progress into a new cycle. The same rule applies to a future repeated group whose IDs are reused; set its cadence and schedule before recording progress.

Call `changes(previous_raw_export, current_raw_export)` after a successful refresh, or pass `--previous old_raw.json` to include a change report in the interpreted output. The report identifies added/removed groups and changed group fields or task IDs. Refresh affected plans when text, deadlines, rewards, or availability change. Recheck expiry against the current UTC time at read time, as the fetcher README notes. A changed task fingerprint can trigger review of stored progress semantics while leaving the user's stored selection and progress untouched.

Current review cases include one task with no stated mode (`113:1758`), a cumulative-versus-single-match wording ambiguity (`25:140`), and whether a Rivals qualification task strictly gates FC Pro Ladder play (`108:1734`). The public pages also do not give reliable reset times for Daily Objectives, Weekly Objectives, Weekly Rush Points, or Weekly Play. These require source review or a separately configured schedule before automatic planning or cycle-scoped progress.

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

Private storage schema version 1 has three maps: `selections[group_id]` stores `selected_at` and the group source fingerprint at selection; `deadline_corrections[group_id]` stores the observation list; and `progress[progress_key]` stores `task_id`, `cycle_start_utc`, manual `count`, manual `completed`, `updated_at`, and the source task fingerprint and text from the first record. Updating progress preserves that original text and fingerprint so a changed instruction remains reviewable. `unselect` removes only the selection; evidence and progress stay in the private file. Writes replace the state file atomically. The CLI does not merge concurrent writers, so serialize updates to one state file.

`view` produces JSON with `schema_version`, `as_of`, `source_fetched_at`, and `selected_groups`. Each group has `availability` (`active`, `upcoming`, `expired`, `unlisted`, `missing`, or `needs_review`), the two deadline values and correction list, `review_flags`, `tasks`, and `unmatched_progress`. `expired` is evaluated against `as_of` on every read, including for unlisted groups. `unlisted` means FUT.GG removed a group before its effective expiry. `missing` means no active or retained source record exists. `source_group_changed`, `source_task_changed`, and `stored_task_unlisted` flag source changes without resetting private data. Task entries give the current `source_text`, the applicable `progress_key`, progress for that key only, and review flags. `unmatched_progress` exposes saved records whose task ID no longer appears in an active selected group. The returned view is derived output; do not save it over either source export.

For repeat objectives, supply an authoritative cycle start in UTC when recording progress and when reading the current cycle. For example:

```bash
python3 user_objectives.py --state ~/fc27-user-state.json progress 61:464 1 --completed --cycle-start-utc 2026-09-27T07:00:00Z
python3 user_objectives.py --state ~/fc27-user-state.json view --cycle 61=2026-09-27T07:00:00Z
```

That example timestamp is illustrative, **not a verified reset schedule**. `view` reports `cycle_start_required` and no current progress if a repeat selection has no supplied cycle. Old daily and weekly records stay in storage but are never read into a new cycle. Nonrepeat tasks reject cycle starts. Manual count is a user-entered quantity; this layer does not verify match eligibility, derive a reset schedule, or plan matches.

Verification: `python3 -m unittest discover -s . -p 'test_*.py'` covers a real null-deadline objective (`25`), a published deadline (`94`), daily (`61`) and weekly (`80`) cycles, unlisting, text changes, conflicting evidence, and private-state round trips. Remaining cases for later work: obtaining trustworthy reset boundaries, deciding whether a reviewed user correction should supersede a conflicting FUT.GG deadline, and reconciling changed or removed task semantics with past manual progress.

## Match planning core

`plan_objectives.py` consumes the interpreted export and the **derived selected view** from `user_objectives.selected_view()`. It does not read or alter the raw export or private state when called as a function. The CLI generates a fresh view from private state, then prints a plan as JSON:

```bash
python3 plan_objectives.py --state ~/fc27-user-state.json \
  --mode squad_battles --mode rivals --mode rush --exclude rivals \
  --cycle 65=2026-09-24T07:00:00Z
```

`--mode` supplies the application's actual available mode catalog; repeat it for each mode. `--exclude` removes a mode. Excluding `live_events` also removes its PVE and PVP variants. `--cycle` is required for each selected daily or weekly group whose progress should be planned; supply an **authoritatively known current cycle start**, never a time inferred from the group start or expiry. `--as-of` can fix the UTC read time for a reproducible result. The output is private because it reflects selections and progress; keep redirected files outside published exports.

Programmatic contract: `build_plan(interpreted, selected_view, available_modes: set[str], excluded_modes: set[str] | None = None)` returns schema version 1 JSON-compatible data. The view and export must have matching `source_fetched_at`. `as_of`, `available_modes`, and `excluded_modes` describe the evaluation. `match_blocks` contains one chosen `mode_option`, `conditions`, `effective_expires_at`, optional `cycle_start_utc`, and `qualifying_matches` for each block. Each block lists the exact task IDs, source instructions, progress keys, and remaining qualifying matches it covers. Blocks are sorted by known expiry, then group and route. `completed_tasks` lists manually completed tasks with no active review flags. `unscheduled_tasks` retains source instructions, target, progress key, and machine-readable reasons. `unavailable_groups` reports selected groups without active interpreted tasks, including unlisted and missing groups.

`combined_plan` groups compatible separate-match tasks across selected groups into shared runs and minimizes the sum of qualifying matches over permitted routes. A specific Live Event match can also count toward a generic Live Events or any-FUT task. A higher difficulty can satisfy a lower minimum in the same mode. Each run shows its separate-match tasks, starting-squad requirements, required scorer/assister traits, and cumulative targets that can progress in those matches; a cumulative target may appear in several compatible runs because its progress can span them. The search is exact under these compatibility rules unless it reaches its node limit; then `optimization` is `search_limited`. The match count is a **conditional minimum for separate-match tasks**, not a guaranteed full-completion count: cumulative goals and assists have no stated per-match cap, match outcomes can fail, event access and available players are not verified, and unparsed or review tasks stay unscheduled. Different squad traits are conservatively treated as different players when checking the eleven-slot limit; one dual-eligible player may permit more overlap than the planner recognizes.

Only active, parsed, separate-match tasks with a permitted catalog route and no review flags enter blocks. A manually recorded count reduces the target within the supplied current cycle. Tasks in the **same group and cycle** share a block only when their chosen mode option and all conditions match exactly; the block uses the largest remaining count. For example, the three Squad Battles win tiers in group `94` produce one block of 15 qualifying World Class wins when progress is empty. Wins, scoring conditions, and assists are **conditional outcomes**; `qualifying_matches` is not a prediction of attempts, time, or guaranteed completion. Alternative modes use the first permitted option in source order; this is a deterministic route choice, not an optimization across tasks.

The planner reports cumulative goal or assist targets as `match_count_not_bounded` because their match count cannot be calculated from the export, even when they appear as opportunities in shared runs. It also reports checklist and dependency tasks, unconfirmed task rules, source or deadline conflicts, unavailable groups, missing cycle starts, and routes removed by the mode catalog or exclusions. It does not derive reset times, schedule calendar slots, verify that a user has a required squad or event access, or prove that a win or goal will happen.
