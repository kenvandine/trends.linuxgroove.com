import json
from datetime import datetime

class InfluxDBHandler:
    """Handles storage of data in InfluxDB"""
    
    def __init__(self, bucket="linuxgroove", org="linuxgroove-org", token="my-token"):
        self.client = None
        self.bucket = bucket
        self.org = org
        self.token = token
        self.write_api = None
        
        # Try to import influxdb_client, but don't fail if not available
        try:
            import influxdb_client
            from influxdb_client.client.write_api import SYNCHRONOUS
            
            self.client = influxdb_client.InfluxDBClient(
                url="http://localhost:8086",
                token=token,
                org=org
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        except ImportError:
            print("InfluxDB client not available. Install with: pip install influxdb-client")
        
    def store_data(self, data_points):
        """Store data points in InfluxDB"""
        if not self.client:
            print("InfluxDB client not initialized")
            return
            
        for point in data_points:
            # Format the data for InfluxDB
            try:
                record = {
                    "measurement": "linux_share",
                    "tags": {
                        "source": point.get("source", "unknown"),
                        "source_id": point.get("source", "unknown"),
                    },
                    "time": point.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
                    "fields": {
                        "value": point.get("linux_share", 0),
                        "metadata": json.dumps(point.get("details", {}))
                    }
                }
                self.write_api.write(bucket=self.bucket, org=self.org, record=record)
            except Exception as e:
                print(f"Error writing to InfluxDB: {str(e)}")
                
    def get_data(self, source_id=None, start_date=None, end_date=None):
        """Retrieve data from InfluxDB
        
        Args:
            source_id: Optional source ID to filter by
            start_date: Optional start date for date range (YYYY-MM-DD format)
            end_date: Optional end date for date range (YYYY-MM-DD format)
        """
        if not self.client:
            print("InfluxDB client not initialized")
            return []
            
        try:
            # Build Flux query
            query = f'from(bucket: "{self.bucket}")'
            query += f' |> range(start: {start_date if start_date else "-365d"})'
            
            if source_id:
                query += f' |> filter(fn: (r) => r.source_id == "{source_id}")'
                
            if end_date:
                query += f' |> range(start: {start_date}, stop: {end_date})'
            
            result = self.client.query_api().query(query)
            
            # Convert result to list of dictionaries
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        "source": record.values.get("source", "unknown"),
                        "date": record.values.get("time", ""),
                        "linux_share": record.values.get("value", 0),
                        "details": json.loads(record.values.get("metadata", "{}"))
                    })
            
            return data
        except Exception as e:
            print(f"Error querying InfluxDB: {str(e)}")
            return []
