import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import date, datetime
from pathlib import Path
from src.adapters.base_adapter import BaseAdapter


class SteamAdapter(BaseAdapter):
    """Adapter for Steam Hardware & Software Survey data.

    Parses the OS distribution from the Steam survey page, specifically the
    #osversion_details section which has top-level category rows (div.stats_row)
    for Windows, OSX, and Linux with their aggregate percentages.

    Historical data (2014-present) is fetched via the Wayback Machine CDX API,
    which archives monthly snapshots of the Steam survey page.  The same HTML
    parser is used for both live and archived pages.  Months that already have
    stored data files are skipped automatically.
    """

    SOURCE_INFO = {
        "name": "Steam Hardware & Software Survey",
        "description": "OS distribution among active Steam users (gaming population)",
        "url": "https://store.steampowered.com/hwsurvey/",
        "methodology": "Monthly opt-in hardware/software survey of Steam users",
    }

    # Wayback Machine CDX API
    _CDX_API = "https://web.archive.org/cdx/search/cdx"
    # Steam survey canonical URL prefixes (ordered by preference).
    # matchType=prefix is used so ?language=english variants are included.
    # Tracking-param snapshots (gclid, fbclid, etc.) are filtered out server-side.
    _CDX_URL_PATTERNS = [
        "store.steampowered.com/hwsurvey/Steam-Hardware-Software-Survey-Welcome-to-Steam",
        "store.steampowered.com/hwsurvey/Steam-Hardware-Software-Survey-",
        "store.steampowered.com/hwsurvey/",
    ]

    def __init__(self):
        super().__init__("Steam")
        self.url = (
            "https://store.steampowered.com/hwsurvey/"
            "Steam-Hardware-Software-Survey-?language=english"
        )
        self.supported_date_ranges = True
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    def fetch_data(self, start_date=None, end_date=None):
        """Fetch OS distribution from Steam hardware survey.

        When start_date and end_date are both provided, fetches historical data
        month-by-month via the Wayback Machine.  Skips months that already have
        stored data files.

        When called without dates, fetches the current survey from Steam directly.

        Args:
            start_date: Start date (YYYY-MM-DD). Requires end_date.
            end_date:   End date   (YYYY-MM-DD). Requires start_date.

        Returns:
            List of data points, one per available monthly snapshot.
        """
        if start_date and end_date:
            return self._fetch_historical(start_date, end_date)
        return self._fetch_current()

    # ------------------------------------------------------------------ #
    # Current data                                                         #
    # ------------------------------------------------------------------ #

    def _fetch_current(self):
        try:
            print("  Fetching Steam hardware survey...")
            response = requests.get(self.url, headers=self._headers, timeout=30)

            if response.status_code != 200:
                print(f"  Steam HTTP {response.status_code}")
                return []

            result = self._parse_page(response.text)
            if not result:
                print("  Could not parse OS data from Steam survey page")
                return []

            date_str = self._extract_survey_date(response.text)
            print(
                f"  Steam ({date_str[:7]}): "
                f"Linux={result['linux_share']:.2f}%  "
                f"Win={result['windows_share']:.2f}%  "
                f"Mac={result['mac_share']:.2f}%"
            )
            return self.format_data([{"date": date_str, **result}])

        except Exception as exc:
            print(f"  Steam error: {exc}")
            return []

    # ------------------------------------------------------------------ #
    # Historical data via Wayback Machine                                 #
    # ------------------------------------------------------------------ #

    def _fetch_historical(self, start_date, end_date):
        """Fetch historical Steam survey data via Wayback Machine CDX API."""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        from_ts = start.strftime("%Y%m01000000")
        to_ts = end.strftime("%Y%m31235959")

        print("  Querying Wayback Machine CDX API for Steam survey snapshots...")
        snapshots = self._get_wayback_snapshots(from_ts, to_ts)

        if not snapshots:
            print("  No Wayback Machine snapshots found for the requested range")
            return []

        print(f"  Found {len(snapshots)} monthly snapshots to process")
        results = []

        for snap in snapshots:
            timestamp = snap["timestamp"]          # e.g. "20200615123456"
            original_url = snap["original"]
            year_month = f"{timestamp[:4]}-{timestamp[4:6]}"

            # Stay within requested date range
            if year_month < start_date[:7] or year_month > end_date[:7]:
                continue

            # Skip single-OS platform views — they don't show the cross-OS totals
            if re.search(r"platform=(linux|mac|windows)", original_url, re.IGNORECASE):
                continue

            # Skip obviously garbage URLs (spaces, non-HTML resources, junk paths)
            if not self._is_valid_survey_url(original_url):
                print(f"  Steam {year_month}: skipping garbage URL: {original_url[:80]}")
                continue

            if self._month_file_exists(year_month):
                print(f"  Steam {year_month}: already stored, skipping")
                continue

            archive_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
            print(f"  Steam {year_month}: fetching from Wayback Machine...")

            try:
                resp = self._fetch_with_retry(archive_url)
                if resp is None:
                    print(f"  Steam {year_month}: failed after retries, skipping")
                    continue

                if resp.status_code != 200:
                    print(f"  Steam {year_month}: HTTP {resp.status_code}, skipping")
                    time.sleep(2)
                    continue

                parsed = self._parse_page(resp.text)
                if not parsed:
                    print(f"  Steam {year_month}: could not parse page, skipping")
                    time.sleep(2)
                    continue

                # Use the date extracted from the page; fall back to snapshot month
                date_str = self._extract_survey_date(resp.text)
                if not date_str.startswith(year_month):
                    date_str = f"{year_month}-01"

                print(
                    f"  Steam {year_month}: "
                    f"Linux={parsed['linux_share']:.2f}%  "
                    f"Win={parsed['windows_share']:.2f}%  "
                    f"Mac={parsed['mac_share']:.2f}%"
                )
                results.extend(self.format_data([{"date": date_str, **parsed}]))

            except Exception as exc:
                print(f"  Steam {year_month}: error — {exc}")

            # Respectful delay between Wayback Machine requests
            time.sleep(2)

        return results

    def _is_valid_survey_url(self, url):
        """Return False for obviously garbage Wayback Machine URLs.

        CDX sometimes returns crawl artifacts: URLs with spaces (%20) in the
        path, trailing punctuation, static file extensions, or very long paths
        that are clearly not the main Steam survey HTML page.
        """
        # Must be under the hwsurvey path
        if "/hwsurvey" not in url.lower():
            return False
        # Reject URLs where the path contains encoded spaces (%20) — link text
        # got mistakenly appended to the URL in the crawl
        if "%20" in url:
            return False
        # Reject non-HTML resources
        if re.search(r"\.(ico|js|css|png|gif|jpg|svg|woff|ttf)(\?|$)", url, re.IGNORECASE):
            return False
        # Reject URLs with trailing garbage (slashes pile-up, trailing dot, comma)
        path = url.split("?")[0]
        if re.search(r"(/{3,}|[.,]$)", path):
            return False
        return True

    def _fetch_with_retry(self, url, max_retries=3):
        """Fetch a URL with exponential backoff on connection errors."""
        delay = 5
        for attempt in range(max_retries):
            try:
                return requests.get(url, headers=self._headers, timeout=60)
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    print(f"    Connection error, waiting {delay}s before retry...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    return None
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
                else:
                    return None
        return None

    def _get_wayback_snapshots(self, from_ts, to_ts):
        """Query CDX API and return one snapshot per month for Steam survey pages.

        Queries URL patterns without collapse so we get multiple candidates per
        month, then picks the cleanest URL for each month in Python.  This is
        more robust than collapse=timestamp:6, which can hand back garbage URLs
        if the first crawl of a month was a tracking/language variant.
        """
        all_snaps = []  # raw snapshot dicts

        for url_pattern in self._CDX_URL_PATTERNS:
            query = (
                f"url={url_pattern}"
                f"&matchType=prefix"
                f"&output=json"
                f"&fl=timestamp,original,statuscode"
                f"&filter=statuscode:200"
                f"&filter=!original:.*gclid.*"
                f"&filter=!original:.*fbclid.*"
                f"&filter=!original:.*%3Fved.*"
                f"&filter=!original:.*platform%3D(linux|mac|windows).*"
                f"&from={from_ts}"
                f"&to={to_ts}"
                f"&limit=3000"
            )
            try:
                resp = self._fetch_with_retry(f"{self._CDX_API}?{query}")
                if resp is None or not resp.ok:
                    print(f"  CDX unavailable for {url_pattern}, skipping")
                    continue
                rows = resp.json()
            except Exception as exc:
                print(f"  CDX query error for {url_pattern}: {exc}")
                continue

            if len(rows) < 2:
                continue

            headers = rows[0]
            all_snaps.extend(dict(zip(headers, row)) for row in rows[1:])

        if not all_snaps:
            return []

        # Group by year-month, pick the best URL for each month.
        # Preference order: no query params > ?language=english > any ?l= > ?platform=
        per_month: dict = {}
        for snap in all_snaps:
            if not self._is_valid_survey_url(snap["original"]):
                continue
            ym = f"{snap['timestamp'][:4]}-{snap['timestamp'][4:6]}"
            if ym not in per_month or self._url_score(snap["original"]) > self._url_score(per_month[ym]["original"]):
                per_month[ym] = snap

        return sorted(per_month.values(), key=lambda s: s["timestamp"])

    def _url_score(self, url):
        """Score a URL for preference (higher = better).

        Clean URLs with no query params are best; language variants are fine;
        platform=combined is acceptable.
        """
        if "?" not in url:
            return 3
        if "language=english" in url or url.endswith("?language=english"):
            return 2
        if re.search(r"\?l=", url):
            return 1
        return 0

    def _month_file_exists(self, year_month):
        """Return True if a non-empty data file already exists for this month."""
        path = Path("data") / "steam" / f"{year_month}.json"
        return path.exists() and path.stat().st_size > 20

    # ------------------------------------------------------------------ #
    # Parsing                                                              #
    # ------------------------------------------------------------------ #

    def _parse_page(self, html):
        """Extract top-level OS percentages from #osversion_details.

        Steam's page structure (as of 2016-2026):

            <div id="osversion_details">
              <div class="stats_row">Windows 94.62% +0.39%</div>
              <div class="stats_col_mid data_row">Windows 11 64 bit</div>
              <div class="stats_col_right data_row">66.71%</div>
              ...
              <div class="stats_row">OSX 2.01% -0.17%</div>
              ...
              <div class="stats_row">Linux 3.38% -0.20%</div>
              ...
            </div>

        Top-level aggregates are in div.stats_row; sub-entries use data_row classes.
        Falls back to a regex scan for older archived page formats.
        """
        soup = BeautifulSoup(html, "html.parser")
        container = soup.find(id="osversion_details")
        if container:
            result = self._parse_osversion_details(container)
            if result:
                return result

        # Fallback: regex scan for aggregate OS percentages in older page formats
        return self._parse_fallback(html)

    def _parse_osversion_details(self, container):
        """Parse the #osversion_details div (current page format)."""
        totals = {"windows": 0.0, "mac": 0.0, "linux": 0.0}
        linux_details = {}
        current_category = None

        for child in container.children:
            if not hasattr(child, "get"):
                continue
            classes = child.get("class", [])

            if "stats_row" in classes:
                text = child.get_text(" ", strip=True)
                pct = self._extract_first_pct(text)
                lower = text.lower()

                if lower.startswith("windows"):
                    totals["windows"] = pct
                    current_category = "windows"
                elif lower.startswith("osx") or lower.startswith("mac"):
                    totals["mac"] = pct
                    current_category = "mac"
                elif lower.startswith("linux"):
                    totals["linux"] = pct
                    current_category = "linux"
                else:
                    current_category = None

            elif current_category == "linux" and "stats_col_mid" in classes:
                linux_details["_last_name"] = child.get_text(" ", strip=True)

            elif (
                current_category == "linux"
                and "stats_col_right" in classes
                and "stats_col_right2" not in classes
            ):
                name = linux_details.pop("_last_name", None)
                if name:
                    pct = self._extract_first_pct(child.get_text(" ", strip=True))
                    linux_details[name] = pct

        if totals["linux"] == 0 and totals["windows"] == 0:
            return None

        other = max(0.0, round(100.0 - totals["windows"] - totals["mac"] - totals["linux"], 2))
        return {
            "linux_share":   round(totals["linux"],   2),
            "windows_share": round(totals["windows"], 2),
            "mac_share":     round(totals["mac"],     2),
            "other_share":   other,
            "details":       {k: round(v, 2) for k, v in linux_details.items()},
        }

    def _parse_fallback(self, html):
        """Regex-based fallback parser for older archived Steam survey pages.

        Older page formats (pre-2016) used tables and different div structures.
        This parser looks for the pattern used in survey-results tables where
        OS names appear alongside their aggregate percentages.
        """
        # Look for a surveycol table row pattern: "Windows ... XX.XX%"
        # These appeared in Steam's older HTML table format
        soup = BeautifulSoup(html, "html.parser")

        totals = {"windows": 0.0, "mac": 0.0, "linux": 0.0}

        # Try table rows: each row has OS name in one cell, percentage in another
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            name_text = cells[0].get_text(" ", strip=True).lower()
            pct_text = " ".join(c.get_text(" ", strip=True) for c in cells[1:])
            pct = self._extract_first_pct(pct_text)
            if not pct:
                continue
            if name_text.startswith("windows"):
                totals["windows"] = max(totals["windows"], pct)
            elif name_text.startswith(("osx", "mac os", "macos")):
                totals["mac"] = max(totals["mac"], pct)
            elif name_text.startswith("linux") or name_text.startswith("steamos"):
                totals["linux"] = max(totals["linux"], pct)

        if totals["linux"] == 0 and totals["windows"] == 0:
            return None

        other = max(0.0, round(100.0 - totals["windows"] - totals["mac"] - totals["linux"], 2))
        return {
            "linux_share":   round(totals["linux"],   2),
            "windows_share": round(totals["windows"], 2),
            "mac_share":     round(totals["mac"],     2),
            "other_share":   other,
            "details":       {},
        }

    def _extract_first_pct(self, text):
        """Return the first bare percentage number found in text."""
        m = re.search(r"([\d.]+)\s*%", text)
        return float(m.group(1)) if m else 0.0

    def _extract_survey_date(self, html):
        """Extract the survey month from the page title or headings."""
        # "Steam Hardware & Software Survey: January 2026"
        m = re.search(r"Survey[:\s]+(\w+ \d{4})", html, re.IGNORECASE)
        if m:
            try:
                return datetime.strptime(m.group(1), "%B %Y").strftime("%Y-%m-01")
            except ValueError:
                pass
        return datetime.utcnow().strftime("%Y-%m-01")
