#!/usr/bin/env python3
"""
Linux Groove Market Trends
"""

import sys
import argparse
from datetime import datetime
from src.core.engine import MarketTrendsEngine


def main():
    parser = argparse.ArgumentParser(
        description="Linux Groove Market Trends",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect current data from all sources
  python3 -m src.main

  # Collect data for a specific month
  python3 -m src.main --month 2025-06

  # Collect a historical date range (StatCounter supports this)
  python3 -m src.main --source statcounter --range-from 2019-01-01 --range-to 2026-02-01

  # Collect from a single source
  python3 -m src.main --source steam

  # Rebuild manifest.json and combined.json from existing stored data
  python3 -m src.main --rebuild-index
        """,
    )

    parser.add_argument("--range-from", "-f", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--range-to", "-t", help="End date (YYYY-MM-DD)")
    parser.add_argument("--month", "-m", help="Collect a single month (YYYY-MM)")
    parser.add_argument(
        "--source", "-s",
        choices=["steam", "statcounter", "dap"],
        help="Only collect from this source",
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Rebuild manifest.json and combined.json from stored data (no network requests)",
    )

    args = parser.parse_args()

    engine = MarketTrendsEngine()

    if args.rebuild_index:
        engine.rebuild_index()
        return

    # Determine date range
    start_date = None
    end_date = None

    if args.month:
        try:
            year, month = map(int, args.month.split("-"))
            start_date = f"{year:04d}-{month:02d}-01"
            end_date = (
                f"{year + 1:04d}-01-01"
                if month == 12
                else f"{year:04d}-{month + 1:02d}-01"
            )
            print(f"Month: {args.month} ({start_date} to {end_date})")
        except ValueError:
            print(f"Invalid month format: {args.month!r}. Expected YYYY-MM")
            sys.exit(1)

    if args.range_from:
        start_date = args.range_from
    if args.range_to:
        end_date = args.range_to

    if start_date and end_date:
        try:
            s = datetime.strptime(start_date, "%Y-%m-%d")
            e = datetime.strptime(end_date, "%Y-%m-%d")
            if s > e:
                print("Error: start date must be before end date")
                sys.exit(1)
        except ValueError as ex:
            print(f"Invalid date: {ex}")
            sys.exit(1)

    engine.collect_data(start_date, end_date, args.source)


if __name__ == "__main__":
    main()
