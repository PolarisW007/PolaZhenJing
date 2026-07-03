#!/usr/bin/env python3
"""Backfill historical insight topics for missing calendar dates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import insight_topics  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Backfill missing PolaZhenJing daily insight topics for a date range.",
    )
    parser.add_argument("--start", required=True, help="Start date, YYYY-MM-DD.")
    parser.add_argument("--end", required=True, help="End date, YYYY-MM-DD.")
    parser.add_argument(
        "--topics-per-day",
        type=int,
        default=1,
        help="Number of deterministic topics to add for each missing date. Default: 1.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute the additions without writing data/insight_topics.json.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        result = insight_topics.backfill_topics_for_date_range(
            args.start,
            args.end,
            topics_per_day=args.topics_per_day,
            persist=not args.dry_run,
        )
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        action = "would add" if args.dry_run else "added"
        print(
            f"{action} {result['added_count']} topic(s), "
            f"covered {result['target_days'] - len(result['missing_days_after'])}/"
            f"{result['target_days']} day(s)."
        )
        if result["added_dates"]:
            print("added dates:", ", ".join(result["added_dates"]))
        if result["missing_days_after"]:
            print("still missing:", ", ".join(result["missing_days_after"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
