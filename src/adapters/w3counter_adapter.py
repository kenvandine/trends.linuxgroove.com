import calendar
import os
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

from src.adapters.base_adapter import BaseAdapter


class W3CounterAdapter(BaseAdapter):
    """Adapter for W3Counter global platform share.

    Source page publishes a "Top 10 Platforms" table per month.
    This is not a full platform census, so shares are derived from listed rows
    plus an "unlisted remainder" bucket in other_share.
    """

    SOURCE_INFO = {
        "name": "W3Counter",
        "description": "Global platform share from W3Counter monthly top platforms",
        "url": "https://www.w3counter.com/globalstats.php",
        "methodology": "Monthly top-10 platform table from W3Counter global stats",
    }

    _URL = "https://www.w3counter.com/globalstats.php?year={year}&month={month}"
    _USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    _LINUX_HINTS = ("linux", "ubuntu", "debian", "fedora", "mint", "arch")
    _WIN_HINTS = ("win", "windows")
    _MAC_HINTS = ("mac", "os x")
    _CHROMEOS_HINTS = ("chrome os", "chromeos", "chromebook", "cros")
    _MOBILE_HINTS = ("android", "ios", "iphone", "ipad")

    def __init__(self):
        super().__init__("W3Counter")
        self.supported_date_ranges = True

    def fetch_data(self, start_date=None, end_date=None):
        """Fetch monthly platform share from W3Counter."""
        now = datetime.utcnow()
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime(now.year, now.month, 1)
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime(now.year, now.month, 1)

        results = []
        current = date(start.year, start.month, 1)
        end_month = date(end.year, end.month, 1)

        while current <= end_month:
            ym = f"{current.year:04d}-{current.month:02d}"
            if self._month_file_exists(ym):
                print(f"  W3Counter {ym}: already stored, skipping")
            else:
                point = self._fetch_one_month(current.year, current.month)
                if point:
                    results.append(point)
            current = date(current.year + (current.month // 12), (current.month % 12) + 1, 1)

        return self.format_data(results)

    def _fetch_one_month(self, year, month):
        url = self._URL.format(year=year, month=month)
        print(f"  W3Counter {year:04d}-{month:02d}: fetching...")
        try:
            resp = requests.get(url, timeout=30, headers={"User-Agent": self._USER_AGENT})
            if resp.status_code != 200:
                print(f"  W3Counter {year:04d}-{month:02d}: HTTP {resp.status_code}")
                return None
            point = self._parse_html(resp.text, year, month)
            if point:
                print(
                    f"  W3Counter {year:04d}-{month:02d}: "
                    f"Linux={point['linux_share']:.2f}% Win={point['windows_share']:.2f}% Mac={point['mac_share']:.2f}%"
                )
            return point
        except Exception as exc:
            print(f"  W3Counter {year:04d}-{month:02d}: error - {exc}")
            return None

    def _parse_html(self, html, year, month):
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table", class_="datatable")
        platform_table = None
        for table in tables:
            header = table.find("th")
            if header and "Top 10 Platforms" in header.get_text(" ", strip=True):
                platform_table = table
                break
        if not platform_table:
            return None

        linux = windows = mac = chromeos = other = 0.0
        listed_total = 0.0
        details = {}

        for row in platform_table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue
            label = cells[1].get_text(" ", strip=True)
            pct = self._parse_pct(cells[2].get_text(" ", strip=True))
            listed_total += pct
            details[label] = round(pct, 2)
            lower = label.lower()
            if any(h in lower for h in self._CHROMEOS_HINTS):
                chromeos += pct
            elif any(h in lower for h in self._LINUX_HINTS):
                linux += pct
            elif any(h in lower for h in self._WIN_HINTS):
                windows += pct
            elif any(h in lower for h in self._MAC_HINTS):
                mac += pct
            elif any(h in lower for h in self._MOBILE_HINTS):
                other += pct
            else:
                other += pct

        # "Top 10 platforms" does not always add to 100%.
        # Keep remainder explicit as "Other" to preserve denominator.
        if listed_total < 100:
            other += (100 - listed_total)

        if linux == 0 and windows == 0 and mac == 0:
            return None

        return {
            "date": f"{year:04d}-{month:02d}-01",
            "linux_share": round(linux, 2),
            "windows_share": round(windows, 2),
            "mac_share": round(mac, 2),
            "chromeos_share": round(chromeos, 2),
            "other_share": round(other, 2),
            "details": details,
        }

    @staticmethod
    def _parse_pct(text):
        try:
            return float(text.replace("%", "").strip())
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _month_file_exists(year_month):
        path = os.path.join("data", "w3counter", f"{year_month}.json")
        return os.path.exists(path) and os.path.getsize(path) > 20

