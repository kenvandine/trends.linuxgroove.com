import calendar
import os
import time
import requests
from datetime import date, datetime
from pathlib import Path
from src.adapters.base_adapter import BaseAdapter


class DAPAdapter(BaseAdapter):
    """Adapter for the US Digital Analytics Program (DAP).

    Fetches OS distribution data from analytics.usa.gov, which tracks
    visits to US federal government websites. This represents a broad
    cross-section of US internet users across all devices.

    Note: DAP data includes mobile devices (Android, iOS), so Linux share
    here represents desktop Linux as a fraction of *all* government web
    traffic (mobile + desktop), which is lower than desktop-only metrics.

    Historical data (2018-present) is available via the GSA Analytics API:
      - v1.1: January 2018 – July 2023  (api_key query param)
      - v2:   August 2023 – present     (x-api-key header)

    Set the DAP_API_KEY environment variable to your api.data.gov key.
    A DEMO_KEY is used as fallback but has strict rate limits.
    """

    SOURCE_INFO = {
        "name": "US Digital Analytics Program (DAP)",
        "description": "OS distribution across US federal government websites (all devices)",
        "url": "https://analytics.usa.gov/",
        "methodology": "Real-time and aggregated analytics from participating US agencies"
    }

    # Known mobile/tablet OSes to separate from desktop
    _MOBILE_KEYWORDS = frozenset(["android", "ios", "iphone", "ipad", "ipod", "blackberry", "windows phone"])
    _LINUX_KEYWORDS = frozenset(["linux"])
    _WIN_KEYWORDS = frozenset(["windows"])
    _MAC_KEYWORDS = frozenset(["macintosh", "mac os", "macos", "os x"])
    _CHROMEOS_KEYWORDS = frozenset(["chromeos", "chrome os", "cros"])

    # GSA API endpoints
    _API_V1 = "https://api.gsa.gov/analytics/dap/v1.1/reports/os/data"
    _API_V2 = "https://api.gsa.gov/analytics/dap/v2/reports/os/data"

    def __init__(self):
        super().__init__("DAP")
        # os.json provides OS breakdown across all government website sessions
        self.url = "https://analytics.usa.gov/data/live/os.json"
        self.supported_date_ranges = True
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
        }

    def fetch_data(self, start_date=None, end_date=None):
        """Fetch OS distribution from DAP.

        When start_date and end_date are both provided, fetches historical
        data month-by-month via the GSA Analytics API. Skips months that
        already have stored data files.

        When called without dates, fetches the current period from the
        live analytics.usa.gov endpoint.

        Args:
            start_date: Start date (YYYY-MM-DD). Requires end_date.
            end_date:   End date   (YYYY-MM-DD). Requires start_date.

        Returns:
            List of data points, one per month in the requested range.
        """
        if start_date and end_date:
            return self._fetch_historical(start_date, end_date)
        return self._fetch_current()

    # ------------------------------------------------------------------ #
    # Current data                                                         #
    # ------------------------------------------------------------------ #

    def _fetch_current(self):
        try:
            print("  Fetching DAP OS data from analytics.usa.gov...")
            response = requests.get(self.url, headers=self._headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                os_data = self._parse_dap_data(data)
                if os_data:
                    date_str = datetime.utcnow().strftime("%Y-%m-01")
                    point = {"date": date_str, **os_data}
                    print(
                        f"  DAP: Linux={os_data.get('linux_share', 0):.2f}% "
                        f"Win={os_data.get('windows_share', 0):.2f}% "
                        f"Mac={os_data.get('mac_share', 0):.2f}%"
                    )
                    return self.format_data([point])

            print(f"  DAP returned status {response.status_code}")
        except Exception as e:
            print(f"  Error fetching DAP data: {e}")

        return []

    # ------------------------------------------------------------------ #
    # Historical data via GSA Analytics API                               #
    # ------------------------------------------------------------------ #

    def _fetch_historical(self, start_date, end_date):
        """Fetch one data point per month via the GSA API."""
        api_key = os.environ.get("DAP_API_KEY", "DEMO_KEY")
        if api_key == "DEMO_KEY":
            print(
                "  WARNING: DAP_API_KEY not set; using DEMO_KEY which has strict "
                "rate limits. Register free at https://api.data.gov/signup/"
            )

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        results = []
        current = date(start.year, start.month, 1)
        end_month = date(end.year, end.month, 1)

        while current <= end_month:
            year, month = current.year, current.month
            year_month = f"{year}-{month:02d}"

            if self._month_file_exists(year_month):
                print(f"  DAP {year_month}: already stored, skipping")
            else:
                points = self._fetch_one_month(year, month, api_key)
                if points:
                    results.extend(points)
                time.sleep(0.5)

            # Advance one month
            current = (
                date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
            )

        return results

    def _fetch_one_month(self, year, month, api_key):
        """Fetch OS data for one calendar month from the GSA API."""
        last_day = calendar.monthrange(year, month)[1]
        after = f"{year}-{month:02d}-01"
        before = f"{year}-{month:02d}-{last_day:02d}"
        date_str = f"{year}-{month:02d}-01"

        # v2 for August 2023+, v1.1 for earlier months
        use_v2 = (year, month) >= (2023, 8)

        if use_v2:
            url = self._API_V2
            headers = {**self._headers, "x-api-key": api_key}
            params = {"after": after, "before": before, "limit": 10000}
        else:
            url = self._API_V1
            headers = self._headers
            params = {"api_key": api_key, "after": after, "before": before, "limit": 10000}

        api_ver = "v2" if use_v2 else "v1.1"
        print(f"  DAP {year}-{month:02d}: querying {api_ver} API...")

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=60)

            if resp.status_code == 429:
                print(f"  DAP {year}-{month:02d}: rate limited, waiting 30s...")
                time.sleep(30)
                resp = requests.get(url, headers=headers, params=params, timeout=60)

            if resp.status_code != 200:
                print(f"  DAP {year}-{month:02d}: HTTP {resp.status_code}, skipping")
                return []

            records = resp.json()
            if not isinstance(records, list) or not records:
                print(f"  DAP {year}-{month:02d}: empty or unexpected response")
                return []

            # Aggregate daily visit counts per OS across all records in the month
            by_os = {}
            for rec in records:
                os_name = rec.get("os", "")
                visits = rec.get("visits", 0) or 0
                if os_name and os_name not in ("(not set)", ""):
                    by_os[os_name] = by_os.get(os_name, 0) + visits

            total_users = sum(by_os.values())
            if not total_users:
                print(f"  DAP {year}-{month:02d}: no usable visit data")
                return []

            # Reuse the existing parser (expects same dict structure as live endpoint)
            os_data = self._parse_dap_data(
                {"totals": {"by_os": by_os, "totalUsers": total_users}}
            )
            if not os_data:
                return []

            print(
                f"  DAP {year}-{month:02d}: "
                f"Linux={os_data['linux_share']:.2f}%  "
                f"Win={os_data['windows_share']:.2f}%  "
                f"Mac={os_data['mac_share']:.2f}%"
            )
            return self.format_data([{"date": date_str, **os_data}])

        except Exception as exc:
            print(f"  DAP {year}-{month:02d}: error — {exc}")
            return []

    def _month_file_exists(self, year_month):
        """Return True if a non-empty data file already exists for this month."""
        path = Path("data") / "dap" / f"{year_month}.json"
        return path.exists() and path.stat().st_size > 20

    # ------------------------------------------------------------------ #
    # Parsing                                                              #
    # ------------------------------------------------------------------ #

    def _parse_dap_data(self, data):
        """Parse analytics.usa.gov OS JSON into OS share totals.

        The live API format (as of 2025-2026):
            {
                "totals": {
                    "totalUsers": 40177656,
                    "by_os": {
                        "Windows": 18674756,
                        "iOS": 8857927,
                        "Android": 5407394,
                        "Macintosh": 5120568,
                        "Linux": 1259082,
                        "Chrome OS": 846446,
                        ...
                    }
                }
            }

        Percentages are calculated from totalUsers (includes mobile traffic).
        """
        totals_section = data.get("totals", {})
        by_os = totals_section.get("by_os", {})
        total_users = totals_section.get("totalUsers", 0)

        if not by_os or not total_users:
            return None

        buckets = {
            "linux": 0.0,
            "windows": 0.0,
            "mac": 0.0,
            "chromeos": 0.0,
            "mobile": 0.0,
            "other": 0.0,
        }
        linux_details = {}

        for os_name, count in by_os.items():
            pct = round(count / total_users * 100, 2)
            lower = os_name.lower()

            if any(k in lower for k in self._MOBILE_KEYWORDS):
                buckets["mobile"] += pct
            elif any(k in lower for k in self._CHROMEOS_KEYWORDS):
                buckets["chromeos"] += pct
            elif any(k in lower for k in self._LINUX_KEYWORDS):
                buckets["linux"] += pct
                linux_details[os_name] = pct
            elif any(k in lower for k in self._WIN_KEYWORDS):
                buckets["windows"] += pct
            elif any(k in lower for k in self._MAC_KEYWORDS):
                buckets["mac"] += pct
            else:
                buckets["other"] += pct

        if buckets["linux"] == 0 and buckets["windows"] == 0:
            return None

        return {
            "linux_share":    round(buckets["linux"],   2),
            "windows_share":  round(buckets["windows"], 2),
            "mac_share":      round(buckets["mac"],     2),
            "chromeos_share": round(buckets["chromeos"], 2),
            "other_share":    round(buckets["mobile"] + buckets["other"], 2),
            "details": {
                "Linux":               round(buckets["linux"],   2),
                "Windows":             round(buckets["windows"], 2),
                "macOS":               round(buckets["mac"],     2),
                "ChromeOS":            round(buckets["chromeos"], 2),
                "Mobile (Android/iOS)":round(buckets["mobile"],  2),
                **linux_details,
            },
        }

    def _parse_float(self, value):
        """Safely parse a float, returning 0.0 on failure."""
        try:
            return float(str(value).strip().replace("%", "")) if value else 0.0
        except (ValueError, TypeError):
            return 0.0
