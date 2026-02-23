import os
from datetime import datetime
from src.adapters.base_adapter import BaseAdapter


class JetBrainsAdapter(BaseAdapter):
    """Adapter for JetBrains Developer Ecosystem Survey OS data.

    Unlike Stack Overflow, JetBrains does not publish raw survey CSV/ZIP
    downloads. OS share figures are manually sourced from their published
    interactive results pages:

        https://www.jetbrains.com/lp/devecosystem-{year}/

    Look under the "Team Tools" or "Development" section for the OS question.

    Data represents the percentage of respondents who use each OS for
    development (multi-select question). Shares can exceed 100% because
    a respondent may list more than one OS.

    To add a new survey year:
      1. Visit https://www.jetbrains.com/lp/devecosystem-{year}/
      2. Find the OS usage chart and note the percentages and respondent count.
      3. Add an entry to KNOWN_DATA below.
      4. Run: python3 -m src.main --source jetbrains --range-from {year}-01-01 --range-to {year}-12-31
    """

    SOURCE_INFO = {
        "name": "JetBrains Developer Ecosystem Survey",
        "description": "OS used for development among software developers (annual survey)",
        "url": "https://www.jetbrains.com/lp/devecosystem/",
        "methodology": "Self-reported annual survey of ~20,000+ developers worldwide. "
                       "Multi-select OS question; shares can exceed 100%.",
    }

    # OS share data from JetBrains survey results.
    # All values are percentages of respondents; multi-select so sums exceed 100%.
    # Question: "On which operating systems are your development environments?" (CHECKBOX)
    #
    # 2025 onwards: JetBrains publishes raw CSV data at:
    #   https://resources.jetbrains.com/storage/products/research/DevEco{YEAR}/RawData.zip
    # Parse the one-hot columns: os_devenv::Linux / os_devenv::Windows / os_devenv::macOS
    #
    # Earlier years: sourced from published report charts; values are approximate.
    # Verify at https://www.jetbrains.com/lp/devecosystem-{year}/
    KNOWN_DATA = {
        2019: {"linux": 47.0, "windows": 56.0, "mac": 49.0, "respondents": 6000},
        2020: {"linux": 49.0, "windows": 59.0, "mac": 49.0, "respondents": 19696},
        2021: {"linux": 47.0, "windows": 61.0, "mac": 45.0, "respondents": 31743},
        2022: {"linux": 40.0, "windows": 62.0, "mac": 44.0, "respondents": 29000},
        2023: {"linux": 46.0, "windows": 62.0, "mac": 42.0, "respondents": 26348},
        2024: {"linux": 49.0, "windows": 58.0, "mac": 42.0, "respondents": 23000},
        # 2025: computed from raw CSV (os_devenv one-hot columns), n=24,534
        2025: {"linux": 47.5, "windows": 59.9, "mac": 53.0, "respondents": 24534},
    }

    _FIRST_YEAR = 2019

    def __init__(self):
        super().__init__("JetBrains")
        self.supported_date_ranges = True

    def fetch_data(self, start_date=None, end_date=None):
        """Return OS share data points for each known survey year in range.

        Args:
            start_date: Start date (YYYY-MM-DD). Defaults to most recent year.
            end_date: End date (YYYY-MM-DD). Defaults to most recent year.

        Returns:
            List of annual data points with linux_share, windows_share, mac_share.
        """
        now = datetime.utcnow()
        from_year = datetime.strptime(start_date, "%Y-%m-%d").year if start_date else now.year
        to_year   = datetime.strptime(end_date,   "%Y-%m-%d").year if end_date   else now.year

        from_year = max(from_year, self._FIRST_YEAR)

        results = []
        for year in range(from_year, to_year + 1):
            ym = f"{year:04d}-01"
            existing = f"data/jetbrains/{ym}.json"
            if os.path.exists(existing):
                print(f"  Skipping {year} survey (already stored)")
                continue

            if year not in self.KNOWN_DATA:
                print(
                    f"  No data for {year} — visit "
                    f"https://www.jetbrains.com/lp/devecosystem-{year}/ "
                    f"and add an entry to JetBrainsAdapter.KNOWN_DATA"
                )
                continue

            d = self.KNOWN_DATA[year]
            point = {
                "date":          f"{year:04d}-01-01",
                "linux_share":   d["linux"],
                "windows_share": d["windows"],
                "mac_share":     d["mac"],
                "details": {
                    "Linux":             d["linux"],
                    "Windows":           d["windows"],
                    "macOS":             d["mac"],
                    "total_respondents": d["respondents"],
                    "note":              "Multi-select; shares can exceed 100%",
                },
            }
            results.extend(self.format_data([point]))
            print(
                f"  {year}: Linux {d['linux']:.1f}%  "
                f"Windows {d['windows']:.1f}%  "
                f"macOS {d['mac']:.1f}%  "
                f"(n={d['respondents']:,})"
            )

        return results
