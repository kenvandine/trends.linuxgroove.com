import json
from datetime import datetime

class BaseAdapter:
    """Base adapter class for all data sources"""
    
    def __init__(self, name):
        self.name = name
        self.supported_date_ranges = False
        
    def fetch_data(self, start_date=None, end_date=None):
        """Fetch data from the source. This should be overridden by subclasses.
        
        Args:
            start_date: Optional start date for date range (YYYY-MM-DD format)
            end_date: Optional end date for date range (YYYY-MM-DD format)
        """
        raise NotImplementedError("Subclasses must implement fetch_data method")
        
    def format_data(self, raw_data):
        """Format raw data into standard format"""
        formatted = []
        for item in raw_data:
            formatted_item = {
                "source": self.name,
                "date": item.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
                "linux_share": item.get("linux_share", 0),
                "details": item.get("details", {})
            }
            formatted.append(formatted_item)
        return formatted
    
    def parse_date_range(self, date_str):
        """Parse date string in YYYY-MM-DD format"""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None
    
    def get_month_range(self, year_month):
        """Get start and end dates for a given year-month (YYYY-MM)"""
        try:
            year, month = map(int, year_month.split('-'))
            start_date = datetime(year, month, 1)
            
            # Calculate end of month
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
                
            return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        except ValueError:
            return None, None
