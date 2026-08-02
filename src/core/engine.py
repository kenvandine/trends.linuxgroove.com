import os
import json
from datetime import datetime
from src.adapters.steam_adapter import SteamAdapter
from src.adapters.statcounter_adapter import StatCounterAdapter
from src.adapters.dap_adapter import DAPAdapter
from src.adapters.cloudflare_adapter import CloudflareAdapter
from src.adapters.stackoverflow_adapter import StackOverflowAdapter
from src.adapters.jetbrains_adapter import JetBrainsAdapter
from src.adapters.firefox_adapter import FirefoxAdapter
from src.storage.json_storage_handler import JSONStorageHandler


class MarketTrendsEngine:
    """Main engine for Linux Groove Market Trends data aggregation."""

    def __init__(self):
        self.adapters = [
            SteamAdapter(),
            StatCounterAdapter(),          # worldwide
            StatCounterAdapter("US"),       # United States
            StatCounterAdapter("CA"),       # Canada
            StatCounterAdapter("GB"),       # United Kingdom
            StatCounterAdapter("DE"),       # Germany
            StatCounterAdapter("IN"),       # India
            StatCounterAdapter("JP"),       # Japan
            StatCounterAdapter("BR"),       # Brazil
            StatCounterAdapter("na"),       # North America
            StatCounterAdapter("eu"),       # Europe
            StatCounterAdapter("as"),       # Asia
            StatCounterAdapter("sa"),       # South America
            StatCounterAdapter("af"),       # Africa
            StatCounterAdapter("oc"),       # Oceania
            DAPAdapter(),
            CloudflareAdapter(),
            StackOverflowAdapter(),
            JetBrainsAdapter(),
            FirefoxAdapter(),
        ]
        self.storage = JSONStorageHandler()

    def collect_data(self, start_date=None, end_date=None, source=None):
        """Collect data from all (or a specific) adapter.

        After collection, regenerates manifest.json and combined.json so the
        web UI always reflects the latest data.

        Args:
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
            source: Optional adapter name to collect from ('steam', 'statcounter', 'statcounter-us', etc.).
        """
        print("Collecting data from sources...")
        if start_date:
            print(f"Date range: {start_date} to {end_date}")

        adapters_to_run = self.adapters
        if source:
            # Map source arg to adapter names
            source_map = {
                "statcounter": "StatCounter",
                "statcounter-us": "StatCounter (United States)",
                "statcounter-ca": "StatCounter (Canada)",
                "statcounter-gb": "StatCounter (United Kingdom)",
                "statcounter-de": "StatCounter (Germany)",
                "statcounter-in": "StatCounter (India)",
                "statcounter-jp": "StatCounter (Japan)",
                "statcounter-br": "StatCounter (Brazil)",
                "statcounter-na": "StatCounter (North America)",
                "statcounter-eu": "StatCounter (Europe)",
                "statcounter-as": "StatCounter (Asia)",
                "statcounter-sa": "StatCounter (South America)",
                "statcounter-af": "StatCounter (Africa)",
                "statcounter-oc": "StatCounter (Oceania)",
            }
            target_name = source_map.get(source, source)
            adapters_to_run = [a for a in self.adapters if a.name.lower() == target_name.lower()]
            if not adapters_to_run:
                names = ", ".join(a.name.lower() for a in self.adapters)
                print(f"Unknown adapter '{source}'. Available: {names}")
                return

        for adapter in adapters_to_run:
            print(f"\n[{adapter.name}]")
            try:
                data = adapter.fetch_data(start_date, end_date)
                if data:
                    self.storage.store_data(data)
                    print(f"  Stored {len(data)} data point(s)")
                else:
                    print(f"  No data returned")
            except Exception as e:
                print(f"  Error: {e}")

        print("\nRegenerating manifest and combined data file...")
        self.storage.generate_manifest()
        self.storage.generate_combined()
        print("Done.")

    def get_data(self, source_id=None, start_date=None, end_date=None):
        """Retrieve stored data.

        Args:
            source_id: Optional source filter ('steam', 'statcounter', 'dap').
            start_date: Optional start date (YYYY-MM-DD).
            end_date: Optional end date (YYYY-MM-DD).
        """
        return self.storage.get_data(source_id, start_date, end_date)

    def rebuild_index(self):
        """Regenerate manifest.json and combined.json from existing stored data."""
        print("Rebuilding index from stored data...")
        self.storage.generate_manifest()
        self.storage.generate_combined()
        print("Done.")
