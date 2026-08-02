import requests
import csv
import re
import io
import json
from datetime import datetime, timedelta
from src.adapters.base_adapter import BaseAdapter


class StatCounterAdapter(BaseAdapter):
    """Adapter for StatCounter desktop OS market share data.

    Fetches real monthly time-series data from StatCounter's FusionCharts XML
    endpoint, which supports region-specific data.  Worldwide data is the
    default; pass ``region_code`` to fetch a different region.

    Region codes:  ww (Worldwide), US, CA, GB, DE, IN, JP, BR, etc.
    See https://gs.statcounter.com/os-market-share/desktop for the full list.
    """

    SOURCE_INFO = {
        "name": "StatCounter Global Stats",
        "description": "Desktop web traffic OS market share (worldwide)",
        "url": "https://gs.statcounter.com/",
        "methodology": "Aggregated web traffic from millions of websites globally",
    }

    # Column-name prefixes/keywords that identify each OS group
    _WIN_PREFIXES  = ("win",)
    _MAC_COLUMNS   = frozenset(["os x", "macos", "mac os x", "osx"])
    _LINUX_COLUMNS = frozenset(["linux"])
    _CHROME_COLUMNS = frozenset(["chrome os"])

    # Region code -> (region_name_for_url, region_hidden_value)
    REGION_MAP = {
        "ww":            ("Worldwide",           "ww"),
        "US":            ("United States",       "US"),
        "CA":            ("Canada",              "CA"),
        "GB":            ("United Kingdom",      "GB"),
        "DE":            ("Germany",             "DE"),
        "IN":            ("India",               "IN"),
        "JP":            ("Japan",               "JP"),
        "BR":            ("Brazil",              "BR"),
        "na":            ("North America",       "NA"),
        "eu":            ("Europe",              "EU"),
        "as":            ("Asia",                "AS"),
        "sa":            ("South America",       "SA"),
        "af":            ("Africa",              "AF"),
        "oc":            ("Oceania",             "OC"),
    }

    def __init__(self, region_code="ww"):
        super().__init__("StatCounter")
        self.supported_date_ranges = True
        self.region_code = region_code
        region_name, region_hidden = self.REGION_MAP.get(
            region_code, (f"Region-{region_code}", region_code)
        )
        self.region_name = region_name
        self.region_hidden = region_hidden
        # Set the source name used in data points
        if region_code == "ww":
            self.name = "StatCounter"
        else:
            self.name = f"StatCounter ({region_name})"
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://gs.statcounter.com/",
        }

    def _build_url(self, from_dt, to_dt):
        """Build the StatCounter FusionCharts XML URL for the given region."""
        from_int = from_dt.strftime("%Y%m")
        to_int   = to_dt.strftime("%Y%m")
        return (
            f"https://gs.statcounter.com/chart.php"
            f"?os-{self.region_code}-monthly-{from_int}-{to_int}"
        )

    def fetch_data(self, start_date=None, end_date=None):
        """Fetch OS market share data from StatCounter.

        Args:
            start_date: Start date (YYYY-MM-DD). Defaults to current month.
            end_date: End date (YYYY-MM-DD). Defaults to current month.

        Returns:
            List of monthly data points with linux_share, windows_share,
            mac_share, chromeos_share, and other_share.
        """
        now = datetime.utcnow()
        if start_date:
            from_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            first_of_month = datetime(now.year, now.month, 1)
            from_dt = (first_of_month - timedelta(days=1)).replace(day=1)
        to_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else from_dt

        # The FusionCharts endpoint requires from != to. If single-month,
        # fetch the previous month too and filter later.
        fetch_from = from_dt
        fetch_to = to_dt
        single_month = (from_dt.strftime("%Y%m") == to_dt.strftime("%Y%m"))
        if single_month:
            # Fetch one extra month backwards to ensure we get data
            fetch_from = from_dt - timedelta(days=32)
            fetch_from = fetch_from.replace(day=1)

        url = self._build_url(fetch_from, fetch_to)
        print(f"  Fetching StatCounter data ({self.region_name}): "
              f"{fetch_from.strftime('%Y-%m')} to {fetch_to.strftime('%Y-%m')}")

        try:
            response = requests.get(url, headers=self._headers, timeout=30)
            if response.status_code == 200 and response.text.strip():
                points = self._parse_fusioncharts(response.text)
                if points:
                    # Filter to requested date range if single-month fetch
                    if single_month:
                        points = [p for p in points
                                  if p["date"].startswith(from_dt.strftime("%Y-%m"))]
                    print(f"  Parsed {len(points)} month(s) from StatCounter "
                          f"({self.region_name})")
                    return self.format_data(points)
                print(f"  StatCounter ({self.region_name}) returned no usable rows")
            else:
                print(f"  StatCounter HTTP {response.status_code} ({self.region_name})")
        except Exception as exc:
            print(f"  StatCounter error ({self.region_name}): {exc}")

        return []

    def _parse_fusioncharts(self, text):
        """Parse StatCounter FusionCharts XML (JS-wrapped) into monthly data points.

        The chart.php endpoint returns JavaScript like:
            var json = {"xml":"<chart ...><dataset seriesName='Linux' ...>...</dataset>...</chart>"};

        Each <dataset> corresponds to one OS.  Each <set> has a value and a
        toolText like 'Linux - 3.44% - Jan 2024'.
        """
        # Extract the JSON object from the JS wrapper
        json_match = re.search(r'var json = (\{.+?\});', text, re.DOTALL)
        if not json_match:
            return []

        try:
            data = json.loads(json_match.group(1))
        except json.JSONDecodeError:
            return []

        xml = data.get("xml", "")
        if not xml:
            return []

        # Extract categories (dates) — these are sparse (every other month shown)
        categories = re.findall(r'<category[^>]*label=[\'"]([^\'"]+)[\'"]', xml)

        # Extract datasets
        datasets = re.findall(
            r'<dataset seriesName=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</dataset>',
            xml, re.DOTALL
        )

        if not categories or not datasets:
            return []

        # Build a lookup: month_label -> {os_name: value}
        # Categories are sparse; we need to map values to ALL months
        # The <set> elements contain the full monthly data in toolText
        month_data = {}  # {month_label: {os_name: value}}

        for os_name, dataset_xml in datasets:
            sets = re.findall(
                r'<set value=[\'"]([^\'"]+)[\'"][^>]*toolText=[\'"]([^\'"]+)[\'"]',
                dataset_xml
            )
            for value_str, tool_text in sets:
                # toolText format: "Linux - 3.44% - Jan 2024"
                match = re.search(r'(\w+ \d{4})$', tool_text.strip())
                if match:
                    month_label = match.group(1)
                    val = self._parse_float(value_str)
                    if month_label not in month_data:
                        month_data[month_label] = {}
                    month_data[month_label][os_name.lower()] = val

        # Build data points — one per unique month
        data_points = []
        for month_label in sorted(month_data.keys()):
            os_values = month_data[month_label]
            date_str = self._parse_month_label(month_label)
            if not date_str:
                continue

            linux = win = mac = chrome = other = 0.0
            for col, val in os_values.items():
                if col in self._LINUX_COLUMNS:
                    linux += val
                elif col in self._MAC_COLUMNS:
                    mac += val
                elif col in self._CHROME_COLUMNS:
                    chrome += val
                elif any(col.startswith(p) for p in self._WIN_PREFIXES):
                    win += val
                else:
                    other += val

            if linux == 0 and win == 0:
                continue

            details = {}
            for col, val in os_values.items():
                # Capitalize the OS name for display
                display_name = col.replace("os x", "OS X").replace("chrome os", "Chrome OS")
                if display_name in ("os x", "chrome os"):
                    display_name = col.title()
                details[display_name] = round(val, 2)

            data_points.append({
                "date":           date_str,
                "linux_share":    round(linux,  2),
                "windows_share":  round(win,    2),
                "mac_share":      round(mac,    2),
                "chromeos_share": round(chrome, 2),
                "other_share":    round(other,  2),
                "details":        details,
            })

        return data_points

    def _parse_month_label(self, month_label):
        """Parse a month label like 'Jan 2024' to '2024-01-01'."""
        _MONTHS = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
                   "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
        parts = month_label.split()
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
