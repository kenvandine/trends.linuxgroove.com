import json
import os
from datetime import datetime
from pathlib import Path

class JSONStorageHandler:
    """Handles storage of data in JSON files with directory structure"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        # Ensure data directories exist
        for subdir in ["steam", "statcounter", "dap"]:
            (self.data_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    def store_data(self, data_points):
        """Store data points in JSON files"""
        for point in data_points:
            source = point.get("source", "unknown")
            date_str = point.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
            
            # Convert date to YYYY-MM format for monthly files
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                year_month = date_obj.strftime("%Y-%m")
            except ValueError:
                year_month = date_str[:7]  # Assume YYYY-MM format
            
            # Determine file path based on source and date
            if source == "Steam":
                file_path = self.data_dir / "steam" / f"{year_month}.json"
            elif source == "StatCounter":
                file_path = self.data_dir / "statcounter" / f"{year_month}.json"
            elif source == "DAP":
                file_path = self.data_dir / "dap" / f"{year_month}.json"
            else:
                # Default to a generic approach
                file_path = self.data_dir / "raw" / f"{source}-{year_month}.json"
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing data if file exists
            existing_data = []
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    existing_data = []
            
            # Check if entry with same date already exists
            date_key = point.get("date", "")
            existing_entry = None
            for i, entry in enumerate(existing_data):
                if entry.get("date") == date_key:
                    existing_entry = entry
                    # Remove existing entry with same date
                    existing_data.pop(i)
                    break
            
            # Append or replace the data point
            existing_data.append(point)
            
            # Write back to file
            with open(file_path, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
    def get_data(self, source_id=None, start_date=None, end_date=None):
        """Retrieve data from JSON files
        
        Args:
            source_id: Optional source ID to filter by (steam, statcounter, dap)
            start_date: Optional start date for date range (YYYY-MM-DD format)
            end_date: Optional end date for date range (YYYY-MM-DD format)
        """
        data = []
        
        # If source_id is specified, look only in that source directory
        if source_id:
            source_dirs = [source_id.lower()]
        else:
            source_dirs = ["steam", "statcounter", "dap"]
        
        for source_dir in source_dirs:
            source_path = self.data_dir / source_dir
            if source_path.exists():
                # Read all files in the source directory
                for file_path in source_path.iterdir():
                    if file_path.is_file() and file_path.suffix == '.json':
                        try:
                            with open(file_path, 'r') as f:
                                file_data = json.load(f)
                                data.extend(file_data)
                        except (json.JSONDecodeError, IOError):
                            continue
        
        # Apply date filtering if needed
        if start_date or end_date:
            filtered_data = []
            for item in data:
                try:
                    item_date = datetime.strptime(item.get('date', ''), "%Y-%m-%d")
                    if start_date and item_date >= datetime.strptime(start_date, "%Y-%m-%d"):
                        if not end_date or item_date <= datetime.strptime(end_date, "%Y-%m-%d"):
                            filtered_data.append(item)
                    elif end_date and item_date <= datetime.strptime(end_date, "%Y-%m-%d"):
                        filtered_data.append(item)
                    elif not start_date and not end_date:
                        filtered_data.append(item)
                except ValueError:
                    filtered_data.append(item)
            data = filtered_data
        
        return data
