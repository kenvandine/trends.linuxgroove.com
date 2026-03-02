import requests
from datetime import datetime
from src.adapters.base_adapter import BaseAdapter


class FirefoxAdapter(BaseAdapter):
    """Adapter for Firefox Public Data Report hardware dashboard.

    Fetches weekly OS distribution from Mozilla's public dataset API.
    No authentication required.

    Data source: https://data.firefox.com/dashboard/hardware
    API:         https://data.firefox.com/datasets/desktop/hardware/default/osName/index.json
    """

    SOURCE_INFO = {
        "name": "Firefox Public Data Report",
        "description": "OS distribution among Firefox desktop release channel users (weekly)",
        "url": "https://data.firefox.com/dashboard/hardware",
        "methodology": "Weekly sample of Firefox telemetry from the desktop release channel",
    }

    _OS_URL = (
        "https://data.firefox.com/datasets/desktop/hardware"
        "/default/osName/index.json"
    )

    def __init__(self):
        super().__init__("Firefox")
        self.supported_date_ranges = True

    def fetch_data(self, start_date=None, end_date=None):
        """Fetch weekly OS distribution from the Firefox Public Data Report API.

        Args:
            start_date: Optional start date (YYYY-MM-DD). Only data on or after
                        this date is returned.
            end_date:   Optional end date   (YYYY-MM-DD). Only data on or before
                        this date is returned.

        Returns:
            List of weekly data points.
        """
        print("  Fetching Firefox Public Data Report OS data...")
        try:
            resp = requests.get(self._OS_URL, timeout=30)
            if resp.status_code != 200:
                print(f"  Firefox HTTP {resp.status_code}")
                return []
            payload = resp.json()
        except Exception as exc:
            print(f"  Firefox fetch error: {exc}")
            return []

        populations = payload.get("data", {}).get("populations", {})
        if not populations:
            print("  Firefox: no population data in response")
            return []

        # Collect all dates present in the dataset
        all_dates = set()
        for points in populations.values():
            for pt in points:
                all_dates.add(pt["x"])

        results = []
        for date_str in sorted(all_dates, reverse=True):
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue

            point = self._aggregate_date(populations, date_str)
            if point is not None:
                results.append(point)
                print(
                    f"  Firefox ({date_str}): "
                    f"Linux={point['linux_share']:.2f}%  "
                    f"Win={point['windows_share']:.2f}%  "
                    f"Mac={point['mac_share']:.2f}%"
                )

        return self.format_data(results)

    def _aggregate_date(self, populations, date_str):
        """Aggregate all OS population buckets for a single date.

        Population keys use human-readable labels like "Windows 10",
        "Windows 11", "macOS Big Sur", "Darwin-24.x", "Linux-6.x", etc.
        They are grouped into four buckets: windows, mac, linux, other.
        """
        windows = mac = linux = other = 0.0
        details = {}

        for key, points in populations.items():
            value = next((pt["y"] for pt in points if pt["x"] == date_str), None)
            if value is None:
                continue

            key_lower = key.lower()
            if key_lower.startswith("windows"):
                windows += value
            elif key_lower.startswith("macos") or key_lower.startswith("darwin"):
                mac += value
            elif key_lower.startswith("linux"):
                linux += value
                details[key] = round(value, 2)
            else:
                other += value

        if windows == 0 and linux == 0:
            return None

        return {
            "date":          date_str,
            "linux_share":   round(linux,   2),
            "windows_share": round(windows, 2),
            "mac_share":     round(mac,     2),
            "other_share":   round(other,   2),
            "details":       details,
        }
