import calendar
from datetime import date, datetime
from pathlib import Path

import requests

from src.adapters.base_adapter import BaseAdapter


class StatsBetaGouvAdapter(BaseAdapter):
    """Adapter for stats.beta.gouv.fr (France public service analytics)."""

    SOURCE_INFO = {
        "name": "stats.beta.gouv.fr",
        "description": "OS distribution across beta.gouv.fr public digital services (all devices)",
        "url": "https://stats.beta.gouv.fr/",
        "methodology": "Public Matomo Reporting API aggregated over sites",
    }

    _API_URL = "https://stats.beta.gouv.fr/"
    _USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    _LINUX_KEYS = frozenset(["gnu/linux", "linux"])
    _WIN_KEYS = frozenset(["windows"])
    _MAC_KEYS = frozenset(["mac", "macos", "os x"])
    _CHROMEOS_KEYS = frozenset(["chrome os", "chromeos"])

    def __init__(self):
        super().__init__("StatsBetaGouv")
        self.supported_date_ranges = True

    def fetch_data(self, start_date=None, end_date=None):
        now = datetime.utcnow()
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime(now.year, now.month, 1)
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime(now.year, now.month, 1)

        results = []
        current = date(start.year, start.month, 1)
        end_month = date(end.year, end.month, 1)

        while current <= end_month:
            ym = f"{current.year:04d}-{current.month:02d}"
            if self._month_file_exists(ym):
                print(f"  StatsBetaGouv {ym}: already stored, skipping")
            else:
                point = self._fetch_one_month(current.year, current.month)
                if point:
                    results.append(point)
            current = date(current.year + (current.month // 12), (current.month % 12) + 1, 1)

        return self.format_data(results)

    def _fetch_one_month(self, year, month):
        date_param = f"{year:04d}-{month:02d}-01"
        last_day = calendar.monthrange(year, month)[1]
        print(f"  StatsBetaGouv {year:04d}-{month:02d}: querying Matomo API...")
        params = {
            "module": "API",
            "method": "DevicesDetection.getOsFamilies",
            "idSite": "all",
            "period": "month",
            "date": date_param,
            "format": "json",
            "filter_limit": 1000,
            "expanded": 1,
        }
        try:
            resp = requests.get(self._API_URL, params=params, timeout=60, headers={"User-Agent": self._USER_AGENT})
            if resp.status_code != 200:
                print(f"  StatsBetaGouv {year:04d}-{month:02d}: HTTP {resp.status_code}")
                return None
            payload = resp.json()
        except Exception as exc:
            print(f"  StatsBetaGouv {year:04d}-{month:02d}: error - {exc}")
            return None

        point = self._parse_month(payload, year, month, last_day)
        if point:
            print(
                f"  StatsBetaGouv {year:04d}-{month:02d}: "
                f"Linux={point['linux_share']:.2f}% Win={point['windows_share']:.2f}% Mac={point['mac_share']:.2f}%"
            )
        return point

    def _parse_month(self, payload, year, month, last_day):
        if not isinstance(payload, dict):
            return None

        by_os = {}
        total_visits = 0.0

        for _, entries in payload.items():
            if not isinstance(entries, list):
                continue
            for row in entries:
                label = str(row.get("label", "")).strip()
                visits = self._to_float(row.get("nb_visits", 0))
                if not label or visits <= 0:
                    continue
                by_os[label] = by_os.get(label, 0.0) + visits
                total_visits += visits

        if total_visits <= 0:
            return None

        linux = windows = mac = chromeos = other = 0.0
        for label, visits in by_os.items():
            key = label.lower()
            if any(k in key for k in self._CHROMEOS_KEYS):
                chromeos += visits
            elif any(k in key for k in self._LINUX_KEYS):
                linux += visits
            elif any(k in key for k in self._WIN_KEYS):
                windows += visits
            elif any(k in key for k in self._MAC_KEYS):
                mac += visits
            else:
                other += visits

        def pct(v):
            return round((v * 100.0) / total_visits, 2)

        details_pct = {k: round((v * 100.0) / total_visits, 2) for k, v in sorted(by_os.items(), key=lambda x: -x[1])}
        date_str = f"{year:04d}-{month:02d}-01"
        return {
            "date": date_str,
            "linux_share": pct(linux),
            "windows_share": pct(windows),
            "mac_share": pct(mac),
            "chromeos_share": pct(chromeos),
            "other_share": pct(other),
            "details": details_pct,
            "period_end": f"{year:04d}-{month:02d}-{last_day:02d}",
        }

    @staticmethod
    def _to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _month_file_exists(year_month):
        path = Path("data") / "statsbetagouv" / f"{year_month}.json"
        return path.exists() and path.stat().st_size > 20

