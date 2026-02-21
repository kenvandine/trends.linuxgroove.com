# LinuxGroove

A comprehensive Linux desktop market share tracking and visualization tool that collects data from multiple sources (Steam, StatCounter, DAP) and provides powerful analysis capabilities.

## Features

- **Multi-Source Data Collection**: Gather data from Steam, StatCounter, and DAP
- **Date Range Support**: Analyze data for specific dates, months, or custom ranges
- **Visual Analytics**: Generate charts and trends for Linux market share
- **Flexible Storage**: Store data in JSON files or InfluxDB for time-series analysis
- **Extensible Architecture**: Easy to add new data sources with adapter pattern

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/kenvandine/linuxgroove.git
cd linuxgroove

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Collect current data from all sources
python3 -m src.main

# Collect data for specific month
python3 -m src.main --month 2025-06

# Collect data for date range
python3 -m src.main --range-from 2025-06-01 --range-to 2025-06-30

# Visualize the collected data
python3 -m src.visualization.visualize
```

## Data Sources

### Steam
Collects Linux desktop market share data from Steam hardware survey.

### StatCounter
Gathers global desktop OS market share statistics.

### DAP (Digital Analytics Program)
Provides government and enterprise Linux adoption data.

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| --source | Specify data source | --source steam |
| --month | Collect monthly data | --month 2025-06 |
| --range-from | Start date for range | --range-from 2025-06-01 |
| --range-to | End date for range | --range-to 2025-06-30 |
| --verbose | Enable verbose output | --verbose |

## Project Structure

```
linuxgroove/
├── src/
│   ├── adapters/          # Data source adapters
│   │   ├── base_adapter.py
│   │   ├── steam_adapter.py
│   │   ├── statcounter_adapter.py
│   │   └── dap_adapter.py
│   ├── core/
│   │   └── engine.py      # Main orchestration engine
│   ├── storage/
│   │   ├── json_storage_handler.py
│   │   └── influxdb_handler.py
│   └── visualization/
│       └── visualize.py
├── data/                  # Collected data storage
│   ├── steam/
│   ├── statcounter/
│   └── dap/
├── docs/                  # Documentation
├── tests/                 # Test files
├── README.md
├── USAGE.md
├── IMPLEMENTATION.md
└── requirements.txt
```

## Documentation

- [USAGE.md](USAGE.md) - Detailed usage instructions
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Technical implementation details
- [TEST.md](TEST.md) - Testing guidelines
- [INSTALL.md](INSTALL.md) - Installation instructions
- [EXAMPLES.md](EXAMPLES.md) - Usage examples
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

## Data Storage

Data is organized by source and date:

```
data/
├── steam/
│   ├── 2025-01.json
│   ├── 2025-02.json
│   └── ...
├── statcounter/
│   ├── 2025-01.json
│   └── ...
└── dap/
    ├── 2025-01.json
    └── ...
```

Each JSON file contains an array of data points with:
- Timestamp
- Source identifier
- OS name and version
- Market share percentage
- User count

## Visualization

The visualization module generates charts showing:
- Linux market share trends over time
- OS distribution breakdown
- Source-specific statistics

Output files are saved as PNG images in the project root.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Steam for their hardware survey data
- StatCounter for market statistics
- DAP for government adoption data
