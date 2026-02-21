import os
import json
from datetime import datetime
from src.adapters.steam_adapter import SteamAdapter
from src.adapters.statcounter_adapter import StatCounterAdapter
from src.adapters.dap_adapter import DAPAdapter
from src.storage.json_storage_handler import JSONStorageHandler

class LinuxGrooveEngine:
    """Main engine for LinuxGroove data aggregation"""
    
    def __init__(self):
        self.adapters = [
            SteamAdapter(),
            StatCounterAdapter(),
            DAPAdapter()
        ]
        self.storage = JSONStorageHandler()
        
    def collect_data(self, start_date=None, end_date=None, source=None):
        """Collect data from all adapters
        
        Args:
            start_date: Optional start date for date range (YYYY-MM-DD format)
            end_date: Optional end date for date range (YYYY-MM-DD format)
            source: Optional specific adapter name to collect from
        """
        print(f"Collecting data from all sources...")
        if start_date:
            print(f"Date range: {start_date} to {end_date}")
        
        adapters_to_collect = self.adapters
        if source:
            adapters_to_collect = [a for a in self.adapters if a.name.lower() == source.lower()]
            if not adapters_to_collect:
                print(f"Adapter '{source}' not found")
                return
        
        for adapter in adapters_to_collect:
            try:
                print(f"Collecting data from {adapter.name}...")
                data = adapter.fetch_data(start_date, end_date)
                if data:
                    self.storage.store_data(data)
                    print(f"Stored {len(data)} data points from {adapter.name}")
                else:
                    print(f"No data collected from {adapter.name}")
            except Exception as e:
                print(f"Error collecting data from {adapter.name}: {str(e)}")
        
        print("Data collection completed.")
        
    def get_data(self, source_id=None, start_date=None, end_date=None):
        """Retrieve data from storage
        
        Args:
            source_id: Optional source ID to filter by
            start_date: Optional start date for date range (YYYY-MM-DD format)
            end_date: Optional end date for date range (YYYY-MM-DD format)
        """
        return self.storage.get_data(source_id, start_date, end_date)
