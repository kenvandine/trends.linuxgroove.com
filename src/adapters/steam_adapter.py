import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from src.adapters.base_adapter import BaseAdapter


class SteamAdapter(BaseAdapter):
    """Adapter for Steam Hardware & Software Survey data.

    Parses the OS distribution from the Steam survey page, specifically the
    #osversion_details section which has top-level category rows (div.stats_row)
    for Windows, OSX, and Linux with their aggregate percentages.
    """

    SOURCE_INFO = {
        "name": "Steam Hardware & Software Survey",
        "description": "OS distribution among active Steam users (gaming population)",
        "url": "https://store.steampowered.com/hwsurvey/",
        "methodology": "Monthly opt-in hardware/software survey of Steam users",
    }

    def __init__(self):
        super().__init__("Steam")
        self.url = (
            "https://store.steampowered.com/hwsurvey/"
            "Steam-Hardware-Software-Survey-?language=english"
        )
        self.supported_date_ranges = False  # Steam only publishes current month
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    def fetch_data(self, start_date=None, end_date=None):
        """Fetch current OS distribution from the Steam hardware survey page.

        Steam only publishes the most recent month's survey results, so
        start_date / end_date are ignored.

        Returns:
            List with one data point for the current survey period.
        """
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
    # Parsing                                                              #
    # ------------------------------------------------------------------ #

    def _parse_page(self, html):
        """Extract top-level OS percentages from #osversion_details.

        Steam's page structure (as of 2025-2026):

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
        """
        soup = BeautifulSoup(html, "html.parser")
        container = soup.find(id="osversion_details")
        if not container:
            return None

        totals = {"windows": 0.0, "mac": 0.0, "linux": 0.0}
        linux_details = {}

        # Track which top-level category we're currently inside
        current_category = None

        for child in container.children:
            if not hasattr(child, "get"):
                continue
            classes = child.get("class", [])

            if "stats_row" in classes:
                # Top-level category row: "Windows 94.62% +0.39%"
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
                # Sub-entry name for a Linux distro
                linux_details["_last_name"] = child.get_text(" ", strip=True)

            elif current_category == "linux" and "stats_col_right" in classes and "stats_col_right2" not in classes:
                # Sub-entry percentage for the Linux distro we just saw
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
