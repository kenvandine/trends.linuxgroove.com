# Linux Groove Market Trends

**Live site:** https://trends.linuxgroove.com &nbsp;|&nbsp; **Repo:** https://github.com/kenvandine/trends.linuxgroove.com

Track Linux desktop market share across multiple real-world data sources and explore the trends through an interactive web dashboard.

## What it does

Linux Groove Market Trends collects OS market share data from three public sources, stores it as plain JSON files, and serves an interactive chart page that lets you compare Linux, Windows, and macOS adoption over time — by source, by OS, and across any timeframe.

| Source | What it measures | Historical data |
|--------|-----------------|-----------------|
| [Steam Hardware Survey](https://store.steampowered.com/hwsurvey/) | OS share among Steam users (gaming) | Current month only |
| [StatCounter Global Stats](https://gs.statcounter.com/) | Desktop web traffic OS share (worldwide) | 2018 – present |
| [US Digital Analytics Program](https://analytics.usa.gov/) | OS share across US federal websites (all devices) | Current period only |

## Hosting

**GitHub Pages** — the included workflow (`.github/workflows/pages.yml`) deploys automatically on every push to `main`. In your repository settings, set Pages source to **GitHub Actions**.

**Local development** — either of these works:

```bash
# From the project root
python3 -m http.server 8000
# → http://localhost:8000/web/

# Or from inside the web/ directory (uses the web/data symlink)
cd web && python3 -m http.server 8000
# → http://localhost:8000/
```

The dashboard lets you:
- **Toggle sources** — compare Steam vs StatCounter vs DAP side-by-side
- **Toggle OS types** — overlay Linux, Windows, and macOS on the same chart
- **Change timeframe** — 1 year, 3 years, 5 years, or all available data
- **Read the stats table** — latest readings and month-over-month Linux change per source

## Quick start

```bash
git clone https://github.com/kenvandine/trends.linuxgroove.com.git
cd trends.linuxgroove.com

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Collect current data from all three sources
python3 -m src.main

# Open the dashboard
python3 -m http.server 8000
# → http://localhost:8000/web/
```

## Data collection

```bash
# Collect current data (all sources)
python3 -m src.main

# Collect from one source only
python3 -m src.main --source steam
python3 -m src.main --source statcounter
python3 -m src.main --source dap

# Fetch historical StatCounter data (supports any date range)
python3 -m src.main --source statcounter \
    --range-from 2019-01-01 --range-to 2026-02-01

# Collect a specific month
python3 -m src.main --month 2025-06

# Rebuild manifest.json and combined.json from existing files (no network)
python3 -m src.main --rebuild-index
```

After any collection run, `data/manifest.json` and `data/combined.json` are automatically regenerated so the web UI reflects the latest data.

## Project structure

```
trends.linuxgroove.com/
├── src/
│   ├── adapters/
│   │   ├── base_adapter.py          # Common interface for all adapters
│   │   ├── steam_adapter.py         # Steam hardware survey (HTML parsing)
│   │   ├── statcounter_adapter.py   # StatCounter CSV export API
│   │   └── dap_adapter.py           # analytics.usa.gov JSON API
│   ├── core/
│   │   └── engine.py                # Orchestrates adapters + storage
│   ├── storage/
│   │   └── json_storage_handler.py  # Monthly files + manifest + combined
│   ├── visualization/
│   │   └── visualize.py             # Matplotlib chart (CLI alternative)
│   └── main.py                      # CLI entry point
├── web/
│   └── index.html                   # Interactive web dashboard (static)
├── data/
│   ├── steam/          YYYY-MM.json
│   ├── statcounter/    YYYY-MM.json
│   ├── dap/            YYYY-MM.json
│   ├── manifest.json   (generated — source metadata + file list)
│   └── combined.json   (generated — all data merged, loaded by web UI)
└── requirements.txt
```

## Data format

Each monthly JSON file contains an array of data points:

```json
[
  {
    "source": "StatCounter",
    "date": "2026-01-01",
    "linux_share": 4.01,
    "windows_share": 67.59,
    "mac_share": 11.82,
    "chromeos_share": 1.22,
    "other_share": 15.35,
    "details": {
      "Linux": 4.01,
      "Windows": 67.59,
      "macOS": 11.82,
      "ChromeOS": 1.22,
      "Other": 15.35
    }
  }
]
```

`windows_share`, `mac_share`, `chromeos_share`, and `other_share` are populated for StatCounter (full history), Steam (current month), and DAP (current period). Older stored files that pre-date this feature only have `linux_share`; the web UI handles missing fields gracefully.

## Adding a new data source

1. Create `src/adapters/{name}_adapter.py` extending `BaseAdapter`
2. Add source metadata to `SOURCE_METADATA` in `src/storage/json_storage_handler.py`
3. Add a `SOURCE_CONFIG` entry in `web/index.html`
4. Register the adapter in `src/core/engine.py`

That's it — the engine, storage, manifest generation, and web UI all pick it up automatically.

## Current readings (as of February 2026)

| Source | Linux | Windows | macOS |
|--------|-------|---------|-------|
| Steam | 3.38% | 94.62% | 2.01% |
| StatCounter | 4.01% | 67.59% | 11.82% |
| DAP (US Gov) | 3.13% | 46.48% | 12.74% |

*DAP figures include mobile traffic (Android, iOS) in the denominator.*

## License

GPL-3.0 — see [LICENSE](LICENSE).
