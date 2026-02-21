# Linux Groove Market Trends Usage Guide

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run data collection:
```bash
# Current data
python3 -m src.main

# Specific month
python3 -m src.main --month 2025-06

# Date range
python3 -m src.main --range-from 2025-06-01 --range-to 2025-06-30
```

3. Visualize data:
```bash
python3 -m src.visualization.visualize --month 2025-06
```

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--month` | Collect data for a specific month | `--month 2025-06` |
| `--range-from` | Start date for data collection | `--range-from 2025-06-01` |
| `--range-to` | End date for data collection | `--range-to 2025-06-30` |
| `--source` | Specific data source | `--source steam` |

## Data Sources

| Source | URL | Description |
|--------|-----|-------------|
| Steam | https://store.steampowered.com/hwsurvey | OS distribution from Steam surveys |
| StatCounter | https://gs.statcounter.com/desktop-market-share | Web traffic market share |
| DAP | https://analytics.usa.gov/data/live/desktop.json | US Government web analytics |

## Output Files

- Data is stored in `data/` directory
- Organized by source: `data/steam/`, `data/statcounter/`, `data/dap/`
- Monthly files: `YYYY-MM.json`
- Visualization output: `linux_share_trend.png`

## Troubleshooting

- **Connection errors**: Try specific source with `--source` flag
- **Missing dependencies**: Install from `requirements.txt`
- **No data**: Ensure data collection runs first

## License

MIT License
