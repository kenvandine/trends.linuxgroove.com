import requests
import csv
import io
from datetime import datetime
from src.adapters.base_adapter import BaseAdapter


class StatCounterAdapter(BaseAdapter):
    """Adapter for StatCounter desktop OS market share data.

    Fetches real monthly time-series data from StatCounter's CSV export API.
    Windows versions (Win10, Win11, Win7…) are aggregated into windows_share.
    "OS X" and "macOS" columns are combined into mac_share.
    """

    SOURCE_INFO = {
        "name": "StatCounter Global Stats",
        "description": "Desktop web traffic OS market share (worldwide)",
        "url": "https://gs.statcounter.com/",
        "methodology": "Aggregated web traffic from millions of websites globally",
    }

    # Column-name prefixes/keywords that identify each OS group
    _WIN_PREFIXES  = ("win",)          # Win10, Win11, Win7, Win8, Win8.1, WinXP…
    _MAC_COLUMNS   = frozenset(["os x", "macos", "mac os x", "osx"])
    _LINUX_COLUMNS = frozenset(["linux"])
    _CHROME_COLUMNS = frozenset(["chrome os"])

    def __init__(self):
        super().__init__("StatCounter")
        self.supported_date_ranges = True
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://gs.statcounter.com/",
        }

    def _build_url(self, from_dt, to_dt):
        """Build the StatCounter monthly CSV export URL."""
        from_int = from_dt.strftime("%Y%m")      # e.g. "202501"
        to_int   = to_dt.strftime("%Y%m")
        from_ym  = from_dt.strftime("%Y-%m")     # e.g. "2025-01"
        to_ym    = to_dt.strftime("%Y-%m")
        return (
            "https://gs.statcounter.com/os-market-share/desktop/worldwide/chart.php"
            f"?period=monthly&statType_hidden=os&region_hidden=ww"
            f"&granularity=monthly&statType=Operating+System&region=Worldwide"
            f"&fromInt={from_int}&toInt={to_int}"
            f"&fromMonthYear={from_ym}&toMonthYear={to_ym}"
            f"&csv=1&chartWidth=600"
        )

    def fetch_data(self, start_date=None, end_date=None):
        """Fetch OS market share data from StatCounter CSV export.

        Args:
            start_date: Start date (YYYY-MM-DD). Defaults to current month.
            end_date: End date (YYYY-MM-DD). Defaults to current month.

        Returns:
            List of monthly data points with linux_share, windows_share,
            mac_share, chromeos_share, and other_share.
        """
        now = datetime.utcnow()
        from_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime(now.year, now.month, 1)
        to_dt   = datetime.strptime(end_date,   "%Y-%m-%d") if end_date   else datetime(now.year, now.month, 1)

        url = self._build_url(from_dt, to_dt)
        print(f"  Fetching StatCounter data: {from_dt.strftime('%Y-%m')} to {to_dt.strftime('%Y-%m')}")

        try:
            response = requests.get(url, headers=self._headers, timeout=30)
            if response.status_code == 200 and response.text.strip():
                points = self._parse_csv(response.text)
                if points:
                    print(f"  Parsed {len(points)} month(s) from StatCounter")
                    return self.format_data(points)
                print("  StatCounter CSV returned no usable rows")
            else:
                print(f"  StatCounter HTTP {response.status_code}")
        except Exception as exc:
            print(f"  StatCounter error: {exc}")

        return []

    def _parse_csv(self, csv_text):
        """Parse StatCounter CSV into monthly data points.

        StatCounter returns two different formats depending on the date range:

        Multi-month (time series) format — used when fromInt != toInt:
            "Date","Win11","Win10","OS X","macOS","Linux","Chrome OS","Unknown",...
            2025-01,26.36,43.38,15.02,0,3.72,1.92,...

        Single-month (aggregate) format — used when fromInt == toInt:
            "OS","Market Share Perc. (Jan 2026)"
            "Win11",45.24
            "Win10",21.57
            "Linux",3.59
            ...
        """
        stripped = csv_text.strip()
        reader = csv.reader(io.StringIO(stripped))
        rows = list(reader)

        if not rows:
            return []

        headers = [h.strip().strip('"') for h in rows[0]]

        # Detect format by first column header
        if headers[0].lower() == "date":
            return self._parse_timeseries(headers, rows[1:], date_from_header=False)
        elif headers[0].lower() == "os":
            # Single-month aggregate: extract period from column header "Market Share Perc. (Jan 2026)"
            period_date = self._extract_period_from_header(headers[1] if len(headers) > 1 else "")
            return self._parse_aggregate(rows[1:], period_date)
        else:
            return []

    def _parse_timeseries(self, headers, data_rows, date_from_header=False):
        """Parse multi-month time-series rows."""
        data_points = []
        for row in data_rows:
            if len(row) < 2:
                continue
            date_str = self._parse_date(row[0].strip().strip('"'))
            if not date_str:
                continue
            linux = win = mac = chrome = other = 0.0
            for col, raw in zip(headers[1:], row[1:]):
                col_l = col.lower()
                val = self._parse_float(raw)
                if col_l in self._LINUX_COLUMNS:
                    linux += val
                elif col_l in self._MAC_COLUMNS:
                    mac += val
                elif col_l in self._CHROME_COLUMNS:
                    chrome += val
                elif any(col_l.startswith(p) for p in self._WIN_PREFIXES):
                    win += val
                else:
                    other += val
            if linux == 0 and win == 0:
                continue
            data_points.append(self._make_point(date_str, linux, win, mac, chrome, other))
        return data_points

    def _parse_aggregate(self, data_rows, period_date):
        """Parse single-month aggregate rows (OS, share%) into one data point."""
        if not period_date:
            return []
        linux = win = mac = chrome = other = 0.0
        for row in data_rows:
            if len(row) < 2:
                continue
            col_l = row[0].strip().strip('"').lower()
            val = self._parse_float(row[1])
            if col_l in self._LINUX_COLUMNS:
                linux += val
            elif col_l in self._MAC_COLUMNS:
                mac += val
            elif col_l in self._CHROME_COLUMNS:
                chrome += val
            elif any(col_l.startswith(p) for p in self._WIN_PREFIXES):
                win += val
            else:
                other += val
        if linux == 0 and win == 0:
            return []
        return [self._make_point(period_date, linux, win, mac, chrome, other)]

    def _make_point(self, date_str, linux, win, mac, chrome, other):
        return {
            "date":           date_str,
            "linux_share":    round(linux,  2),
            "windows_share":  round(win,    2),
            "mac_share":      round(mac,    2),
            "chromeos_share": round(chrome, 2),
            "other_share":    round(other,  2),
            "details": {
                "Linux":    round(linux,  2),
                "Windows":  round(win,    2),
                "macOS":    round(mac,    2),
                "ChromeOS": round(chrome, 2),
                "Other":    round(other,  2),
            },
        }

    def _extract_period_from_header(self, header_text):
        """Extract YYYY-MM-01 from 'Market Share Perc. (Jan 2026)'."""
        import re
        m = re.search(r'\((\w+ \d{4})\)', header_text)
        if m:
            return self._parse_date(m.group(1))
        # Try "Feb 2026" directly
        return self._parse_date(header_text.strip())

    def _parse_date(self, date_str):
        """Parse StatCounter date to YYYY-MM-01.

        Handles:
          - "2025-01"  → "2025-01-01"
          - "Jan 25"   → "2025-01-01"
          - "Jan 2025" → "2025-01-01"
        """
        if not date_str:
            return None

        # ISO YYYY-MM
        try:
            dt = datetime.strptime(date_str, "%Y-%m")
            return dt.strftime("%Y-%m-01")
        except ValueError:
            pass

        # "Jan 25" or "Jan 2025"
        _MONTHS = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
                   "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
        parts = date_str.split()
        if len(parts) == 2:
            mon = parts[0].lower()[:3]
            yr_str = parts[1]
            if mon in _MONTHS:
                year = int(yr_str) if len(yr_str) == 4 else 2000 + int(yr_str)
                return f"{year:04d}-{_MONTHS[mon]:02d}-01"

        return None

    def _parse_float(self, value):
        try:
            return float(str(value).strip().replace("%", "")) if value else 0.0
        except (ValueError, TypeError):
            return 0.0
