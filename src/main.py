#!/usr/bin/env python3
"""
LinuxGroove - Linux Usage Tracker
"""

import sys
import os
import argparse
from src.core.engine import LinuxGrooveEngine

def main():
    parser = argparse.ArgumentParser(
        description='LinuxGroove - Linux Usage Tracker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Collect current data from all sources
  python3 -m src.main

  # Collect data for a specific date range
  python3 -m src.main --range-from 2025-06-01 --range-to 2025-06-30

  # Collect data for a specific month
  python3 -m src.main --month 2025-06

  # Collect data from a specific source
  python3 -m src.main --source steam

  # Collect data from a specific source for a date range
  python3 -m src.main --source steam --range-from 2025-06-01 --range-to 2025-06-30
        '''
    )
    
    parser.add_argument('--range-from', '-f', 
                        help='Start date for data collection (YYYY-MM-DD format)')
    parser.add_argument('--range-to', '-t', 
                        help='End date for data collection (YYYY-MM-DD format)')
    parser.add_argument('--month', '-m', 
                        help='Month for data collection (YYYY-MM format)')
    parser.add_argument('--source', '-s', 
                        choices=['steam', 'statcounter', 'dap'],
                        help='Specific data source to collect from')
    
    args = parser.parse_args()
    
    # Parse date arguments
    start_date = None
    end_date = None
    
    if args.month:
        # If month is specified, calculate start and end dates for that month
        try:
            year, month = map(int, args.month.split('-'))
            start_date = f"{year:04d}-{month:02d}-01"
            
            # Calculate end of month
            if month == 12:
                end_date = f"{year + 1:04d}-01-01"
            else:
                end_date = f"{year:04d}-{month + 1:02d}-01"
                
            print(f"Collecting data for month: {args.month} ({start_date} to {end_date})")
        except ValueError:
            print(f"Invalid month format: {args.month}. Expected YYYY-MM")
            sys.exit(1)
    
    if args.range_from:
        start_date = args.range_from
    if args.range_to:
        end_date = args.range_to
    
    # Validate date range if both are provided
    if start_date and end_date:
        try:
            from datetime import datetime
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            if start > end:
                print("Error: Start date must be before or equal to end date")
                sys.exit(1)
        except ValueError as e:
            print(f"Invalid date format: {e}")
            sys.exit(1)
    
    print("Starting LinuxGroove Data Aggregation Engine...")
    
    # Initialize the engine
    engine = LinuxGrooveEngine()
    
    # Run the data collection process with optional date range
    engine.collect_data(start_date, end_date, args.source)
    
    print("Data collection completed.")

if __name__ == "__main__":
    main()
