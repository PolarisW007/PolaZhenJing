#!/usr/bin/env python3
"""Utilities for PolaZhenJing content production v2 artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from content_production_v2 import (  # noqa: E402
    CAPABILITY_MAP,
    capability_map_markdown,
    dump_json,
    normalize_signal_summary,
    render_review_markdown,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PolaZhenJing content production v2 helpers")
    sub = parser.add_subparsers(dest="command", required=True)

    capability = sub.add_parser("capability-map", help="Render the upstream capability map")
    capability.add_argument("--format", choices=("markdown", "json"), default="markdown")
    capability.add_argument("--output", help="Write to file instead of stdout")

    review = sub.add_parser("review", help="Generate a de-AI review report from article markdown")
    review.add_argument("--topic", required=True)
    review.add_argument("--article", required=True, help="Path to article markdown")
    review.add_argument("--signals", help="Path to signal-summary JSON")
    review.add_argument("--output", help="Write report to file instead of stdout")

    signals = sub.add_parser("signal-summary", help="Normalize source summaries into a signal pack")
    signals.add_argument("--topic", required=True)
    signals.add_argument("--input", required=True, help="Path to JSON list of source objects")
    signals.add_argument("--output", help="Write normalized JSON to file instead of stdout")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "capability-map":
        payload = capability_map_markdown() if args.format == "markdown" else dump_json(CAPABILITY_MAP)
        return _write_output(payload, args.output)

    if args.command == "signal-summary":
        source_payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        normalized = normalize_signal_summary(args.topic, source_payload)
        return _write_output(dump_json(normalized), args.output)

    article = Path(args.article).read_text(encoding="utf-8")
    signal_summary = None
    if args.signals:
        signal_summary = json.loads(Path(args.signals).read_text(encoding="utf-8"))
    report = render_review_markdown(args.topic, article, signal_summary=signal_summary)
    return _write_output(report, args.output)


def _write_output(payload: str, output: str | None) -> int:
    if output:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
