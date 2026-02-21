#!/usr/bin/env python3
"""Test script for LinuxGroove adapters"""

import sys
from datetime import datetime
from src.adapters.steam_adapter import SteamAdapter
from src.adapters.statcounter_adapter import StatCounterAdapter
from src.adapters.dap_adapter import DAPAdapter


def test_adapters():
    """Test each adapter with date range support"""

    # Test date ranges
    test_ranges = [
        (None, None),  # No date range (current data)
        ("2025-06-01", "2025-06-30"),  # Specific month
        ("2025-01-01", "2025-12-31"),  # Full year
    ]

    adapters = [SteamAdapter(), StatCounterAdapter(), DAPAdapter()]

    for adapter in adapters:
        print(f" Testing {adapter.name} adapter:")

        for start_date, end_date in test_ranges:
            if start_date:
                print(f"  Date range: {start_date} to {end_date}")
            else:
                print(f"  Date range: All available data")

            try:
                data = adapter.fetch_data(start_date, end_date)
                print(f"    Retrieved {len(data)} data points")

                if data:
                    print(f"    First data point: {data[0]}")
            except Exception as e:
                print(f"    Error: {str(e)}")


if __name__ == "__main__":
    test_adapters()
