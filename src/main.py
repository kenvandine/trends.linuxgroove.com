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

  # Backfill StatCounter history (2018-present)
  python3 -m src.main --source statcounter --range-from 2018-01-01 --range-to 2026-02-01

  # Backfill Steam history via Wayback Machine (2014-present, ~2s per month)
  python3 -m src.main --source steam --range-from 2014-01-01 --range-to 2026-02-01

  # Backfill DAP history via GSA API (2018-present)
  # Requires: export DAP_API_KEY=your_key   (register free at https://api.data.gov/signup/)
  python3 -m src.main --source dap --range-from 2018-01-01 --range-to 2026-02-01

  # Backfill Cloudflare Radar history (monthly, all devices; data available from ~2022-09)
  # Requires: export CLOUDFLARE_RADAR_API_KEY=your_token  (free at https://developers.cloudflare.com/radar/get-started/first-request/)
  python3 -m src.main --source cloudflare --range-from 2022-09-01 --range-to 2026-02-01

  # Backfill Stack Overflow Developer Survey history (annual, 2017-present)
  python3 -m src.main --source stackoverflow --range-from 2017-01-01 --range-to 2026-01-01

  # Backfill JetBrains Developer Ecosystem Survey history (annual, 2019-present)
  python3 -m src.main --source jetbrains --range-from 2019-01-01 --range-to 2026-01-01

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
        choices=["steam", "statcounter", "dap", "cloudflare", "stackoverflow", "jetbrains"],
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
