import requests
from datetime import datetime
from src.adapters.base_adapter import BaseAdapter


class DAPAdapter(BaseAdapter):
    """Adapter for the US Digital Analytics Program (DAP).

    Fetches OS distribution data from analytics.usa.gov, which tracks
    visits to US federal government websites. This represents a broad
    cross-section of US internet users across all devices.

    Note: DAP data includes mobile devices (Android, iOS), so Linux share
    here represents desktop Linux as a fraction of *all* government web
    traffic (mobile + desktop), which is lower than desktop-only metrics.
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

    def __init__(self):
        super().__init__("DAP")
        # os.json provides OS breakdown across all government website sessions
        self.url = "https://analytics.usa.gov/data/live/os.json"
        self.supported_date_ranges = False  # DAP only provides current/recent data
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
        }

    def fetch_data(self, start_date=None, end_date=None):
        """Fetch current OS distribution from analytics.usa.gov.

        Args:
            start_date: Ignored (DAP provides only current period data).
            end_date: Ignored.

        Returns:
            List with one data point for the current period.
        """
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
