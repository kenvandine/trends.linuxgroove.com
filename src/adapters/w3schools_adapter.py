from datetime import datetime

import requests
from bs4 import BeautifulSoup

from src.adapters.base_adapter import BaseAdapter


class W3SchoolsAdapter(BaseAdapter):
    """Adapter for W3Schools OS Platform Statistics."""

    SOURCE_INFO = {
        "name": "W3Schools",
        "description": "OS platform share from W3Schools monthly log-based statistics",
        "url": "https://www.w3schools.com/browsers/browsers_os.asp",
        "methodology": "Monthly percentages from W3Schools website traffic logs",
    }

    _URL = "https://www.w3schools.com/browsers/browsers_os.asp"
    _USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self):
        super().__init__("W3Schools")
        self.supported_date_ranges = True

    def fetch_data(self, start_date=None, end_date=None):
        """Fetch monthly OS shares parsed from annual tables on one page."""
        print("  Fetching W3Schools OS statistics...")
        try:
            resp = requests.get(self._URL, timeout=30, headers={"User-Agent": self._USER_AGENT})
            if resp.status_code != 200:
                print(f"  W3Schools HTTP {resp.status_code}")
                return []
            points = self._parse_html(resp.text)
        except Exception as exc:
            print(f"  W3Schools fetch error: {exc}")
            return []

        if start_date:
            points = [p for p in points if p["date"] >= start_date]
        if end_date:
            points = [p for p in points if p["date"] <= end_date]

        print(f"  W3Schools: parsed {len(points)} month(s)")
        return self.format_data(points)

    def _parse_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table", class_="ws-table-all")
        results = []

        for table in tables:
            header_cells = table.find_all("th")
            if len(header_cells) < 3:
                continue

            year_text = header_cells[0].get_text(" ", strip=True)
            if not year_text.isdigit():
                continue
            year = int(year_text)
            if year < 2003 or year > 2100:
                continue

            columns = [c.get_text(" ", strip=True).lower() for c in header_cells[1:]]
            for row in table.find_all("tr")[1:]:
                cells = row.find_all("td")
                if len(cells) != len(columns) + 1:
                    continue

                month_name = cells[0].get_text(" ", strip=True)
                date_str = self._to_date(year, month_name)
                if not date_str:
                    continue

                linux = windows = mac = chromeos = other = 0.0
                details = {}
                for idx, col in enumerate(columns):
                    value = self._parse_pct(cells[idx + 1].get_text(" ", strip=True))
                    details[col] = round(value, 2)

                    if col.startswith("win") or col in ("vista", "nt*", "nt"):
                        windows += value
                    elif col.startswith("linux"):
                        linux += value
                    elif col.startswith("mac"):
                        mac += value
                    elif "chromeos" in col or "chrome os" in col:
                        chromeos += value
                    else:
                        other += value

                results.append({
                    "date": date_str,
                    "linux_share": round(linux, 2),
                    "windows_share": round(windows, 2),
                    "mac_share": round(mac, 2),
                    "chromeos_share": round(chromeos, 2),
                    "other_share": round(other, 2),
                    "details": details,
                })

        # Deduplicate by date (latest table on page wins if duplicates exist)
        by_date = {}
        for point in results:
            by_date[point["date"]] = point

        return [by_date[d] for d in sorted(by_date.keys())]

    @staticmethod
    def _to_date(year, month_name):
        month_name = month_name.strip()
        for fmt in ("%B", "%b"):
            try:
                dt = datetime.strptime(f"{month_name} {year}", f"{fmt} %Y")
                return dt.strftime("%Y-%m-01")
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_pct(text):
        try:
            return float(text.replace("%", "").strip())
        except (ValueError, TypeError):
            return 0.0

