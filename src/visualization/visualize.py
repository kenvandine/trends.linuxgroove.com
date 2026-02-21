import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime


def load_and_visualize_data(data_dir="data", start_date=None, end_date=None):
    """Load data from JSON files and create visualizations

    Args:
        data_dir: Directory containing data files
        start_date: Optional start date for filtering (YYYY-MM-DD format)
        end_date: Optional end date for filtering (YYYY-MM-DD format)
    """
    print("Loading data for visualization...")

    # Load data from all sources
    all_data = []

    data_path = Path(data_dir)
    for source_dir in ["steam", "statcounter", "dap"]:
        source_path = data_path / source_dir
        if source_path.exists():
            for file_path in source_path.iterdir():
                if file_path.is_file() and file_path.suffix == ".json":
                    try:
                        with open(file_path, "r") as f:
                            file_data = json.load(f)
                            for item in file_data:
                                item["source"] = source_dir
                                all_data.append(item)
                    except (json.JSONDecodeError, IOError):
                        continue

    if not all_data:
        print("No data found for visualization")
        return

    # Apply date filtering if specified
    if start_date or end_date:
        filtered_data = []
        for item in all_data:
            try:
                item_date = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                if start_date and item_date >= datetime.strptime(
                    start_date, "%Y-%m-%d"
                ):
                    if not end_date or item_date <= datetime.strptime(
                        end_date, "%Y-%m-%d"
                    ):
                        filtered_data.append(item)
                elif end_date and item_date <= datetime.strptime(end_date, "%Y-%m-%d"):
                    filtered_data.append(item)
                elif not start_date and not end_date:
                    filtered_data.append(item)
            except ValueError:
                filtered_data.append(item)
        all_data = filtered_data

    if not all_data:
        print("No data found for the specified date range")
        return

    # Create a DataFrame
    df = pd.DataFrame(all_data)
    df["date"] = pd.to_datetime(df["date"])

    # Group by source and date
    grouped = df.groupby(["source", "date"])["linux_share"].mean().reset_index()

    # Create the plot
    plt.figure(figsize=(12, 6))
    for source in grouped["source"].unique():
        source_data = grouped[grouped["source"] == source]
        plt.plot(
            source_data["date"],
            source_data["linux_share"],
            marker="o",
            label=source,
            linewidth=2,
        )

    plt.xlabel("Date")
    plt.ylabel("Linux Share (%)")
    plt.title("Linux Desktop Market Share Over Time")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.ylim(0, 50)
    plt.tight_layout()
    plt.savefig("linux_share_trend.png")
    plt.show()

    print("Visualization saved as linux_share_trend.png")

    # Print summary statistics
    print(" Summary Statistics:")
    for source in grouped["source"].unique():
        source_data = grouped[grouped["source"] == source]
        print(f"{source}:")
        print(f"  Current: {source_data['linux_share'].iloc[-1]:.2f}%")
        print(f"  Min: {source_data['linux_share'].min():.2f}%")
        print(f"  Max: {source_data['linux_share'].max():.2f}%")
        if len(source_data) > 1:
            change = (
                source_data["linux_share"].iloc[-1] - source_data["linux_share"].iloc[0]
            )
            print(f"  Change: {change:+.2f}%")


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Visualize Linux Groove Market Trends data")
    parser.add_argument(
        "--range-from", "-f", help="Start date for visualization (YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--range-to", "-t", help="End date for visualization (YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--month", "-m", help="Month for visualization (YYYY-MM format)"
    )

    args = parser.parse_args()

    start_date = None
    end_date = None

    if args.month:
        try:
            year, month = map(int, args.month.split("-"))
            start_date = f"{year:04d}-{month:02d}-01"
            if month == 12:
                end_date = f"{year + 1:04d}-01-01"
            else:
                end_date = f"{year:04d}-{month + 1:02d}-01"
        except ValueError:
            print(f"Invalid month format: {args.month}. Expected YYYY-MM")
            sys.exit(1)

    if args.range_from:
        start_date = args.range_from
    if args.range_to:
        end_date = args.range_to

    load_and_visualize_data(start_date=start_date, end_date=end_date)
