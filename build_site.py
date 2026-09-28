#!/usr/bin/env python3
"""Assemble the static, phone-friendly GitHub Pages app in dist/."""

from pathlib import Path
from shutil import copyfile

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"
PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.js"


def main() -> None:
    DIST.mkdir(exist_ok=True)
    for name in ("app.js", "style.css", "ar.json", "static_api.js"):
        copyfile(HERE / "web" / name, DIST / name)
    for name in ("fc27_interpreted.json", "interpret_objectives.py", "user_objectives.py",
                 "plan_objectives.py", "prize_summary.py", "browser_api.py"):
        copyfile(HERE / name, DIST / name)
    html = (HERE / "web" / "index.html").read_text(encoding="utf-8")
    marker = '  <script src="./app.js" defer></script>'
    if html.count(marker) != 1:
        raise ValueError("App script tag changed")
    scripts = f'  <script src="{PYODIDE_URL}"></script>\n  <script src="./static_api.js"></script>\n{marker}'
    (DIST / "index.html").write_text(html.replace(marker, scripts), encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {DIST}")


if __name__ == "__main__":
    main()
