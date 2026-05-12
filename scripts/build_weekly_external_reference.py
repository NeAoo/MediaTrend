#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from formatters.weekly_external_reference import (  # noqa: E402
    WeeklyExternalReferenceBuilder,
    validate_package,
)


def _parse_day(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _default_last_week(today: date | None = None) -> tuple[date, date]:
    current = today or date.today()
    this_monday = current - timedelta(days=current.weekday())
    start = this_monday - timedelta(days=7)
    return start, start + timedelta(days=6)


def parse_args() -> argparse.Namespace:
    start, end = _default_last_week()
    parser = argparse.ArgumentParser(description="Build weekly longxia external_reference package.")
    parser.add_argument("--scored-dir", default=str(PROJECT_DIR / "scored_data"))
    parser.add_argument("--output-root", default=str(PROJECT_DIR / "output" / "longxia_weekly_external_reference"))
    parser.add_argument("--week-start", default=start.isoformat())
    parser.add_argument("--week-end", default=end.isoformat())
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--content-max-chars", type=int, default=5000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    week_start = _parse_day(args.week_start)
    week_end = _parse_day(args.week_end)
    if week_start > week_end:
        print(f"error: week-start must be <= week-end: {week_start} > {week_end}", file=sys.stderr)
        return 2
    if (week_end - week_start).days > 6:
        print("error: weekly package range must be at most 7 days", file=sys.stderr)
        return 2

    builder = WeeklyExternalReferenceBuilder(
        scored_dir=Path(args.scored_dir),
        output_root=Path(args.output_root),
        timezone_name=args.timezone,
        content_max_chars=args.content_max_chars,
    )
    package_dir = builder.build(week_start, week_end)
    errors = validate_package(package_dir, week_start, week_end)
    if errors:
        print("error: package validation failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Package: {package_dir}")
    print(f"Week: {week_start.isoformat()}_to_{week_end.isoformat()}")
    print("Status: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
