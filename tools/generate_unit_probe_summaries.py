#!/usr/bin/env python3
"""Generate stable Markdown summaries from unit probe result JSON files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO = TOOLS_DIR.parent
DEFAULT_RESULTS_DIR = REPO / "evidence" / "unit-investigations" / "plans" / "results"

sys.path.insert(0, str(TOOLS_DIR))
from run_unit_probe_plan import render_summary_markdown  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Markdown summaries from unit probe result JSON files.")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--check", action="store_true", help="Fail if any generated summary is missing or stale.")
    return parser.parse_args()


def render_one(path: Path, check: bool) -> bool:
    summary = json.loads(path.read_text(encoding="utf-8"))
    rendered = render_summary_markdown(summary, path)
    out = path.with_suffix(".md")
    if check:
        if not out.is_file() or out.read_text(encoding="utf-8") != rendered:
            print(f"stale summary: {out}", file=sys.stderr)
            return False
        return True
    out.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"summary: {out}")
    return True


def main() -> int:
    args = parse_args()
    paths = sorted(args.results_dir.glob("*.json")) if args.results_dir.is_dir() else []
    ok = True
    for path in paths:
        ok = render_one(path, args.check) and ok
    if args.check and ok:
        print(f"unit-probe-summaries-ok files={len(paths)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
