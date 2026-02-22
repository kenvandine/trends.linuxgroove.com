import os
import io
import csv
import time
import zipfile
import requests
from datetime import datetime
from src.adapters.base_adapter import BaseAdapter


class StackOverflowAdapter(BaseAdapter):
    """Adapter for Stack Overflow Developer Survey OS data.

    Downloads annual survey ZIP files and counts respondents using any
    Linux-based OS for personal use. Data is one point per year (dated
    YYYY-06-01 since surveys typically publish mid-year).

    Column names vary by year:
      2021+: "OpSysPersonal use"
      2020:  "OpSys"
      2017-2019: "OperatingSystem"

    Values are semicolon-delimited multi-select (a respondent may select
    multiple OSes). Linux share = respondents with any Linux entry / total.
    """

    SOURCE_INFO = {
        "name": "Stack Overflow Survey",
        "description": "OS used for personal use among software developers (annual survey)",
        "url": "https://insights.stackoverflow.com/survey",
        "methodology": "Self-reported annual survey of ~65,000 developers worldwide",
    }

    _ZIP_URL = "https://survey.stackoverflow.co/datasets/stack-overflow-developer-survey-{year}.zip"

    # Survey years with available data
    _FIRST_YEAR = 2017
    # Column name for each era
    _COL_PERSONAL = "OpSysPersonal use"   # 2021+
    _COL_OPSYS    = "OpSys"               # 2020
    _COL_OLD      = "OperatingSystem"     # 2017-2019

    # Keywords that indicate a Linux-based OS entry (case-insensitive substring match)
    _LINUX_KEYWORDS = (
        "linux",
        "ubuntu",
        "debian",
        "fedora",
        "arch",
        "centos",
        "red hat",
        "suse",
        "mint",
        "manjaro",
        "elementary",
        "pop!_os",
        "kali",
    )
    # Keywords for Windows / macOS
    _WIN_KEYWORDS = ("windows",)
    _MAC_KEYWORDS = ("macos", "mac os", "os x")

    def __init__(self):
        super().__init__("StackOverflow")
        self.supported_date_ranges = True
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        }

    def fetch_data(self, start_date=None, end_date=None):
        """Fetch OS data from Stack Overflow Developer Surveys.

        Args:
            start_date: Start date (YYYY-MM-DD). Defaults to most recent year.
            end_date: End date (YYYY-MM-DD). Defaults to most recent year.

        Returns:
            List of annual data points with linux_share, windows_share, mac_share.
        """
        now = datetime.utcnow()
        from_year = datetime.strptime(start_date, "%Y-%m-%d").year if start_date else now.year
        to_year   = datetime.strptime(end_date,   "%Y-%m-%d").year if end_date   else now.year

        # Clamp to supported range
        from_year = max(from_year, self._FIRST_YEAR)

        results = []
        for year in range(from_year, to_year + 1):
            ym = f"{year:04d}-06"
            existing = f"data/stackoverflow/{ym}.json"
            if os.path.exists(existing):
                print(f"  Skipping {year} survey (already stored)")
                continue

            print(f"  Fetching Stack Overflow survey {year}...")
            time.sleep(2)
            point = self._fetch_one_year(year)
            if point:
                results.extend(self.format_data([point]))
                print(f"    Linux: {point['linux_share']:.1f}%  "
                      f"Windows: {point['windows_share']:.1f}%  "
                      f"macOS: {point['mac_share']:.1f}%")
            else:
                print(f"    No data found for {year}")

        return results

    def _fetch_one_year(self, year):
        """Download and parse the survey ZIP for a given year, with retry on 429."""
        url = self._ZIP_URL.format(year=year)
        delays = [10, 30, 60]
        for attempt, delay in enumerate([0] + delays):
            if delay:
                print(f"    Rate limited — waiting {delay}s before retry...")
                time.sleep(delay)
            try:
                resp = requests.get(url, headers=self._headers, timeout=120)
            except Exception as exc:
                print(f"    Download error for {year}: {exc}")
                return None

            if resp.status_code == 429:
                if attempt < len(delays):
                    continue
                print(f"    Still rate limited after retries — skipping {year}")
                return None
            if resp.status_code == 404:
                print(f"    Survey ZIP not found for {year}: {url}")
                return None
            if resp.status_code != 200:
                print(f"    HTTP {resp.status_code} for {year}")
                return None

            # Success
            try:
                return self._parse_zip(resp.content, year)
            except Exception as exc:
                print(f"    Parse error for {year}: {exc}")
                return None

        return None

    def _parse_zip(self, zip_bytes, year):
        """Extract the survey CSV from the ZIP and parse OS columns."""
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            # Find the main survey results CSV (not schema)
            csv_names = [
                n for n in zf.namelist()
                if n.endswith(".csv") and "schema" not in n.lower() and "readme" not in n.lower()
            ]
            if not csv_names:
                print(f"    No CSV found in ZIP for {year}. Files: {zf.namelist()[:5]}")
                return None

            # Prefer a file with "survey_results" or "results" in name
            preferred = [n for n in csv_names if "result" in n.lower()]
            csv_name = preferred[0] if preferred else csv_names[0]

            with zf.open(csv_name) as f:
                text = f.read().decode("utf-8", errors="replace")

        return self._parse_csv(text, year)

    def _parse_csv(self, csv_text, year):
        """Parse the survey CSV and extract OS shares."""
        csv.field_size_limit(10 * 1024 * 1024)  # 10 MB — surveys can have large fields
        reader = csv.DictReader(io.StringIO(csv_text))
        headers = reader.fieldnames or []

        # Detect column name for this survey year
        col = self._detect_column(headers, year)
        if not col:
            print(f"    Could not find OS column in {year} survey. Headers: {headers[:10]}")
            return None

        linux_count = windows_count = mac_count = total = 0

        for row in reader:
            val = (row.get(col) or "").strip()
            if not val:
                continue
            total += 1

            # Multi-select: split on semicolon
            choices = [c.strip().lower() for c in val.split(";") if c.strip()]

            if any(any(kw in c for kw in self._LINUX_KEYWORDS) for c in choices):
                linux_count += 1
            if any(any(kw in c for kw in self._WIN_KEYWORDS) for c in choices):
                windows_count += 1
            if any(any(kw in c for kw in self._MAC_KEYWORDS) for c in choices):
                mac_count += 1

        if total == 0:
            return None

        linux_pct   = round(linux_count   / total * 100, 2)
        windows_pct = round(windows_count / total * 100, 2)
        mac_pct     = round(mac_count     / total * 100, 2)
        other_pct   = round(max(0, 100 - linux_pct - windows_pct - mac_pct), 2)

        # Surveys publish roughly in June; use June 1 as the date
        date_str = f"{year:04d}-06-01"
        return {
            "date":          date_str,
            "linux_share":   linux_pct,
            "windows_share": windows_pct,
            "mac_share":     mac_pct,
            "other_share":   other_pct,
            "details": {
                "Linux":   linux_pct,
                "Windows": windows_pct,
                "macOS":   mac_pct,
                "Other":   other_pct,
                "total_respondents": total,
            },
        }

    def _detect_column(self, headers, year):
        """Return the OS column name for the given survey year."""
        # Try the expected column for each era
        candidates = [self._COL_PERSONAL, self._COL_OPSYS, self._COL_OLD]
        for col in candidates:
            if col in headers:
                return col
        # Fuzzy fallback: any header containing "os" or "operating"
        for h in headers:
            hl = h.lower()
            if "operating" in hl or (("os" in hl) and ("personal" in hl or "use" in hl)):
                return h
        return None
