import os
import calendar
import requests
from datetime import datetime
from src.adapters.base_adapter import BaseAdapter


class CloudflareAdapter(BaseAdapter):
    """Adapter for Cloudflare Radar HTTP OS share data.

    Fetches OS distribution from Cloudflare Radar's public API.
    Covers all HTTP traffic (desktop + mobile) worldwide.

    Requires a free Cloudflare Radar API token:
      https://developers.cloudflare.com/radar/get-started/first-request/
    Set via: export CLOUDFLARE_RADAR_API_KEY=your_token
    """

    SOURCE_INFO = {
        "name": "Cloudflare Radar",
        "description": "OS share across all HTTP traffic observed by Cloudflare (all devices, worldwide)",
        "url": "https://radar.cloudflare.com/",
        "methodology": "Aggregated from Cloudflare's global network traffic",
    }

    _API_URL = "https://api.cloudflare.com/client/v4/radar/http/summary/OS"

    def __init__(self):
        super().__init__("Cloudflare")
        self.supported_date_ranges = True

    def fetch_data(self, start_date=None, end_date=None):
        """Fetch OS share from Cloudflare Radar.

        If start_date and end_date span multiple months, fetches each month
        individually and skips months already stored in data/cloudflare/.

        Args:
            start_date: Start date (YYYY-MM-DD). Defaults to current month.
            end_date: End date (YYYY-MM-DD). Defaults to current month.

        Returns:
            List of monthly data points with linux_share, windows_share,
            mac_share, and other_share.
        """
        api_token = os.environ.get("CLOUDFLARE_RADAR_API_KEY", "")
        if not api_token:
            print("  WARNING: CLOUDFLARE_RADAR_API_KEY not set — Cloudflare fetch will fail.")
            print("  Get a free token at https://developers.cloudflare.com/radar/get-started/first-request/")
            return []

        now = datetime.utcnow()
        from_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime(now.year, now.month, 1)
        to_dt   = datetime.strptime(end_date,   "%Y-%m-%d") if end_date   else datetime(now.year, now.month, 1)

        # Single-month fetch
        if from_dt.year == to_dt.year and from_dt.month == to_dt.month:
            point = self._fetch_one_month(from_dt.year, from_dt.month, api_token)
            return self.format_data([point]) if point else []

        # Multi-month historical fetch
        return self._fetch_historical(from_dt, to_dt, api_token)

    def _fetch_historical(self, from_dt, to_dt, api_token):
        """Fetch multiple months, skipping ones already stored."""
        results = []
        year, month = from_dt.year, from_dt.month
        end_year, end_month = to_dt.year, to_dt.month

        while (year, month) <= (end_year, end_month):
            ym = f"{year:04d}-{month:02d}"
            existing = f"data/cloudflare/{ym}.json"
            if os.path.exists(existing):
                print(f"  Skipping {ym} (already stored)")
            else:
                print(f"  Fetching Cloudflare {ym}...")
                point = self._fetch_one_month(year, month, api_token)
                if point:
                    results.extend(self.format_data([point]))
                    print(f"    Linux: {point['linux_share']:.2f}%")

            month += 1
            if month > 12:
                month = 1
                year += 1

        return results

    def _fetch_one_month(self, year, month, api_token):
        """Fetch OS share for a single month from the Cloudflare Radar API."""
        last_day = calendar.monthrange(year, month)[1]
        date_start = f"{year:04d}-{month:02d}-01T00:00:00Z"
        date_end   = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59Z"

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        params = {
            "dateStart": date_start,
            "dateEnd": date_end,
            "format": "JSON",
        }

        try:
            resp = requests.get(self._API_URL, headers=headers, params=params, timeout=30)
            if resp.status_code == 400:
                # Cloudflare Radar has limited historical data (available from ~2022-09).
                # A 400 for older dates is expected — skip silently.
                print(f"    No data available for {year:04d}-{month:02d} (outside Cloudflare Radar history)")
                return None
            if resp.status_code != 200:
                print(f"    HTTP {resp.status_code}: {resp.text[:200]}")
                return None
            return self._parse_response(resp.json(), year, month)
        except Exception as exc:
            print(f"    Error fetching {year:04d}-{month:02d}: {exc}")
            return None

    def _parse_response(self, resp_json, year, month):
        """Parse the Cloudflare API response into a data point dict."""
        summary = resp_json.get("result", {}).get("summary_0", {})
        if not summary:
            return None

        def pct(key):
            try:
                return float(summary.get(key, 0) or 0)
            except (ValueError, TypeError):
                return 0.0

        linux   = pct("LINUX")
        windows = pct("WINDOWS")
        mac     = pct("MACOS")
        android = pct("ANDROID")
        ios     = pct("IOS")
        other   = pct("OTHER")

        # Group mobile OSes into other_share (Cloudflare covers all devices)
        other_total = round(android + ios + other, 2)

        date_str = f"{year:04d}-{month:02d}-01"
        return {
            "date":          date_str,
            "linux_share":   round(linux,   2),
            "windows_share": round(windows, 2),
            "mac_share":     round(mac,     2),
            "other_share":   other_total,
            "details": {
                "Linux":   round(linux,   2),
                "Windows": round(windows, 2),
                "macOS":   round(mac,     2),
                "Android": round(android, 2),
                "iOS":     round(ios,     2),
                "Other":   round(other,   2),
            },
        }
