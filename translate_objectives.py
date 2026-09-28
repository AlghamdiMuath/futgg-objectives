#!/usr/bin/env python3
"""Update the Arabic display catalog for public objective text.

Translations are machine-generated and should be reviewed for game-rule accuracy.
The English source export remains authoritative for parsing and progress.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def source_strings(export: dict) -> set[str]:
    values: set[str] = set()
    for group in export["groups"]:
        values.update((group["title"], group["description"]))
        values.update(group.get("completion_rewards", []))
        values.update(group.get("available_rewards", []))
        for task in group["tasks"]:
            values.update((task["title"], task["source_text"]))
            values.update(task.get("rewards", []))
    return {value for value in values if value.strip()}


def translate_batch(values: list[str]) -> list[str]:
    # Numeric markers survive translation and let one request cover several labels.
    source = "\n".join(f"###T{i:03d}###\n{value}" for i, value in enumerate(values))
    query = urlencode({"client": "gtx", "sl": "en", "tl": "ar", "dt": "t", "q": source})
    request = Request(
        "https://translate.googleapis.com/translate_a/single?" + query,
        headers={"User-Agent": "FC27ObjectiveArabicCatalog/1.0"},
    )
    with urlopen(request, timeout=30) as response:
        data = json.load(response)
    translated = "".join(part[0] for part in data[0])
    parts = re.split(r"###T(\d{3})###\s*", translated)
    if len(parts) != 1 + len(values) * 2 or parts[0].strip():
        raise ValueError("Translation service changed or omitted batch markers")
    result = []
    for index, value in enumerate(values):
        if int(parts[1 + index * 2]) != index:
            raise ValueError("Translation service reordered batch markers")
        arabic = parts[2 + index * 2].strip()
        if not arabic:
            raise ValueError(f"Empty translation for {value!r}")
        result.append(arabic)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("fc27_interpreted.json"))
    parser.add_argument("--output", type=Path, default=Path("web/ar.json"))
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--delay", type=float, default=0.3)
    args = parser.parse_args()
    if args.batch_size < 1 or args.batch_size > 20 or args.delay < 0:
        parser.error("--batch-size must be 1–20 and --delay must be nonnegative")
    export = json.loads(args.input.read_text(encoding="utf-8"))
    existing = json.loads(args.output.read_text(encoding="utf-8")) if args.output.exists() else {}
    if not isinstance(existing, dict):
        raise ValueError("Arabic catalog must be a JSON object")
    missing = sorted(source_strings(export) - existing.keys())
    print(f"{len(missing)} new strings; {len(existing)} cached translations")
    for start in range(0, len(missing), args.batch_size):
        batch = missing[start:start + args.batch_size]
        for attempt in range(3):
            try:
                translations = translate_batch(batch)
                break
            except (OSError, ValueError, IndexError, KeyError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        existing.update(zip(batch, translations))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(args.output)
        print(f"Translated {min(start + len(batch), len(missing))}/{len(missing)}")
        if start + len(batch) < len(missing):
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
