#!/usr/bin/env python3
"""Export public EA SPORTS FC 27 objective pages from FUT.GG to JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


BASE_URL = "https://www.fut.gg"
LIST_URL = f"{BASE_URL}/objectives/"
OBJECTIVE_PATH = re.compile(r"^/objectives/([^/]+)/([0-9]+)-[^/]+/$")
GROUP_TIMES = re.compile(
    r'eaId:(\d+),\s*slug:"(\d+)-[^\"]+",\s*name:"(?:\\.|[^"\\])*",\s*'
    r'categoryEaId:\d+,\s*description:"(?:\\.|[^"\\])*",\s*'
    r'startTime:(null|"[^"]+"),\s*endTime:(null|"[^"]+")'
)
TASK_IDENTITY = re.compile(r'groupEaId:(\d+),eaId:(\d+),name:"((?:\\.|[^"\\])*)"')
USER_AGENT = "FC27ObjectiveExporter/1.0 (public objective pages; contact: local user)"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def clean_text(value: str) -> str:
    return " ".join(value.split())


def parse_timestamp(value: str) -> str | None:
    if value == "null":
        return None
    parsed = datetime.fromisoformat(json.loads(value).replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError(f"Timestamp lacks timezone: {value}")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def group_times(html: str) -> dict[str, dict]:
    """Read the start/end times embedded in FUT.GG's public page data."""
    result = {}
    for group_id, slug_id, start, end in GROUP_TIMES.findall(html):
        if group_id != slug_id:
            raise ValueError(f"Conflicting group IDs in page data: {group_id}, {slug_id}")
        value = {"starts_at": parse_timestamp(start), "expires_at": parse_timestamp(end)}
        if group_id in result and result[group_id] != value:
            raise ValueError(f"Conflicting dates for group {group_id}")
        result[group_id] = value
    return result


def task_identities(html: str, group_id: str) -> list[tuple[str, str]]:
    result = []
    for owner_id, task_id, encoded_name in TASK_IDENTITY.findall(html):
        if owner_id == group_id:
            result.append((task_id, clean_text(json.loads('"' + encoded_name + '"'))))
    if len({task_id for task_id, _ in result}) != len(result):
        raise ValueError(f"Duplicate task IDs in group {group_id}")
    return result


def removed_groups(previous: dict | None, active_groups: list[dict], fetched_at: str) -> list[dict]:
    """Keep last-known metadata for groups missing from a successful refresh."""
    if previous is None:
        return []
    active_ids = {group["id"] for group in active_groups}
    last_seen_at = previous["fetched_at"]
    retained = {group["id"]: group.copy() for group in previous.get("removed_groups", [])}
    for group in previous["groups"]:
        if group["id"] in active_ids:
            continue
        retained[group["id"]] = {
            key: group.get(key)
            for key in ("id", "title", "category", "url", "starts_at", "expires_at")
        } | {"last_seen_at": last_seen_at, "first_missing_at": fetched_at}

    now = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
    result = []
    for group_id, group in retained.items():
        if group_id in active_ids:
            continue
        expiry = group.get("expires_at")
        group["availability"] = (
            "expired"
            if expiry and datetime.fromisoformat(expiry.replace("Z", "+00:00")) <= now
            else "unlisted"
        )
        result.append(group)
    return sorted(result, key=lambda group: group["id"])


def fetch_html(url: str, retries: int = 3) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=25) as response:
                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type:
                    raise ValueError(f"Unexpected content type for {url}: {content_type}")
                return response.read().decode("utf-8")
        except HTTPError as exc:
            if exc.code not in RETRYABLE_STATUS or attempt == retries:
                raise
            retry_after = exc.headers.get("Retry-After", "")
            delay = int(retry_after) if retry_after.isdigit() else 2 ** attempt
            time.sleep(min(delay, 30))
        except (URLError, TimeoutError):
            if attempt == retries:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Could not fetch {url}")


def reward_labels(card) -> list[str]:
    """Extract reward captions from a group or task card, not page navigation."""
    labels = []
    for span in card.select("span"):
        classes = set(span.get("class", []))
        if "text-gray-300" in classes and "font-bold" in classes:
            label = clean_text(span.get_text(" ", strip=True))
            if label and label not in labels:
                labels.append(label)
    return labels


def parse_listing(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find("h1")
    if not heading or "FC 27 Objectives" not in heading.get_text(" ", strip=True):
        raise ValueError("FUT.GG listing did not contain the FC 27 objectives heading")

    times = group_times(html)
    groups = []
    seen = set()
    for link in soup.select('a[href^="/objectives/"]'):
        path = urlparse(link["href"]).path
        match = OBJECTIVE_PATH.fullmatch(path)
        if not match or match.group(2) in seen:
            continue
        # FUT.GG also uses a full-card overlay link beside the visible content.
        card = link.parent if "absolute" in link.get("class", []) else link
        title = card.find("h3")
        if not title:
            continue
        seen.add(match.group(2))
        if match.group(2) not in times:
            raise ValueError(f"Missing start/end times for objective group {match.group(2)}")
        description = card.find("p")
        groups.append({
            "id": match.group(2),
            "category": match.group(1),
            "title": clean_text(title.get_text(" ", strip=True)),
            "description": clean_text(description.get_text(" ", strip=True)) if description else "",
            "url": urljoin(BASE_URL, path),
            **times[match.group(2)],
        })
    if not groups:
        raise ValueError("No objective groups found in FUT.GG listing")
    return groups


def parse_detail(html: str, group: dict) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find("h1")
    if not heading or group["title"] not in heading.get_text(" ", strip=True):
        raise ValueError(f"Detail page did not match {group['title']!r}")

    group_heading = next(
        (h for h in soup.find_all("h3") if clean_text(h.get_text(" ", strip=True)) == group["title"]),
        None,
    )
    if group_heading is None:
        raise ValueError(f"Group card missing for {group['url']}")
    group_card = group_heading.find_parent(class_=lambda value: value and "group/sbc" in value)
    if group_card is None:
        raise ValueError(f"Group card structure changed for {group['url']}")
    detail_times = group_times(html).get(group["id"])
    if detail_times != {key: group[key] for key in ("starts_at", "expires_at")}:
        raise ValueError(f"Dates disagree between listing and detail page for {group['url']}")

    description = group_card.find("p")
    group["description"] = clean_text(description.get_text(" ", strip=True)) if description else group["description"]
    group["completion_rewards"] = reward_labels(group_card)

    rewards_label = soup.find(string=lambda value: value and value.strip() == "Rewards")
    if rewards_label:
        rewards_panel = rewards_label.parent.parent.parent
        rewards_list = rewards_panel.select_one("div.flex.flex-col.gap-2")
        if rewards_list:
            group["available_rewards"] = []
            for row in rewards_list.find_all("div", recursive=False):
                label = clean_text(row.get_text(" ", strip=True))
                if not label:
                    image = row.find("img", alt=True)
                    label = clean_text(image["alt"]) if image else ""
                if label:
                    group["available_rewards"].append(label)

    total_sp = group_card.find(string=re.compile(r"\btotal\b", re.I))
    if total_sp:
        match = re.search(r"([\d,]+)\s*total", clean_text(total_sp.parent.get_text(" ", strip=True)), re.I)
        if match:
            group["total_season_points"] = int(match.group(1).replace(",", ""))

    tasks = []
    for task_heading in soup.find_all("h4"):
        card = task_heading.find_parent(class_=lambda value: value and "group/sbc" in value)
        if card is None:
            continue
        title = clean_text(task_heading.get_text(" ", strip=True))
        task_description = card.find("p")
        if not task_description:
            raise ValueError(f"Task {title!r} has no description on {group['url']}")
        tasks.append({
            "id": f"{group['id']}:{len(tasks) + 1}",
            "title": title,
            "description": clean_text(task_description.get_text(" ", strip=True)),
            "rewards": reward_labels(card),
        })
    if not tasks:
        raise ValueError(f"No tasks found for {group['url']}")
    identities = task_identities(html, group["id"])
    if len(identities) != len(tasks):
        raise ValueError(f"Task ID count disagrees with visible tasks for {group['url']}")
    for task, (task_id, source_title) in zip(tasks, identities):
        if task["title"] != source_title:
            raise ValueError(f"Task titles disagree for {group['url']}: {task['title']!r} vs {source_title!r}")
        task["id"] = f"{group['id']}:{task_id}"
    group["tasks"] = tasks
    return group


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("fc27_objectives.json"))
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between detail requests (default: 0.5)")
    parser.add_argument("--limit", type=int, help="Fetch only the first N groups for a quick check")
    parser.add_argument(
        "--allow-large-drop",
        action="store_true",
        help="Accept a listing with fewer than half as many groups as the previous export",
    )
    args = parser.parse_args()
    if args.delay < 0 or args.limit is not None and args.limit < 1:
        parser.error("--delay must be nonnegative and --limit must be positive")

    try:
        groups = parse_listing(fetch_html(LIST_URL))
        if args.limit:
            groups = groups[: args.limit]
        previous = None
        if args.output.exists():
            if args.limit:
                raise ValueError("--limit cannot replace an existing output file; choose a new --output path")
            previous = json.loads(args.output.read_text(encoding="utf-8"))
            if not args.allow_large_drop:
                previous_count = len(previous["groups"])
                if previous_count and len(groups) * 2 < previous_count:
                    raise ValueError(
                        f"Group count fell from {previous_count} to {len(groups)}; "
                        "keeping previous export. Use --allow-large-drop if this is expected."
                    )
        for index, group in enumerate(groups):
            if index:
                time.sleep(args.delay)
            parse_detail(fetch_html(group["url"]), group)
            print(f"[{index + 1}/{len(groups)}] {group['title']}: {len(group['tasks'])} tasks", file=sys.stderr)

        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        result = {
            "schema_version": 3,
            "game": "EA SPORTS FC 27",
            "source": LIST_URL,
            "fetched_at": fetched_at,
            "groups": groups,
            "removed_groups": removed_groups(previous, groups, fetched_at),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_name(args.output.name + ".tmp")
        temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(args.output)
        print(f"Wrote {len(groups)} groups and {sum(len(g['tasks']) for g in groups)} tasks to {args.output}")
        return 0
    except (HTTPError, URLError, TimeoutError, ValueError, OSError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
