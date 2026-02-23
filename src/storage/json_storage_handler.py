import json
import os
from datetime import datetime
from pathlib import Path


# Metadata for each known data source — extensible by adding entries here
SOURCE_METADATA = {
    "steam": {
        "id": "steam",
        "name": "Steam Hardware Survey",
        "description": "OS distribution among active Steam users (gaming population)",
        "url": "https://store.steampowered.com/hwsurvey/",
        "methodology": "Monthly opt-in survey of Steam users worldwide",
        "covers": "desktop",
        "region": "global",
    },
    "statcounter": {
        "id": "statcounter",
        "name": "StatCounter Global Stats",
        "description": "Desktop OS market share based on web traffic analysis",
        "url": "https://gs.statcounter.com/",
        "methodology": "Aggregated web traffic from millions of websites globally",
        "covers": "desktop",
        "region": "global",
    },
    "dap": {
        "id": "dap",
        "name": "US Digital Analytics Program",
        "description": "OS distribution across US federal government websites (all devices)",
        "url": "https://analytics.usa.gov/",
        "methodology": "Analytics from participating US government agencies",
        "covers": "all_devices",
        "region": "us",
    },
    "cloudflare": {
        "id": "cloudflare",
        "name": "Cloudflare Radar",
        "description": "OS share across all HTTP traffic observed by Cloudflare (all devices, worldwide)",
        "url": "https://radar.cloudflare.com/",
        "methodology": "Aggregated from Cloudflare's global network traffic",
        "covers": "all_devices",
        "region": "global",
    },
    "stackoverflow": {
        "id": "stackoverflow",
        "name": "Stack Overflow Survey",
        "description": "OS used for personal use among software developers (annual survey)",
        "url": "https://insights.stackoverflow.com/survey",
        "methodology": "Self-reported annual survey of ~65,000 developers worldwide",
        "covers": "desktop",
        "region": "global",
    },
    "jetbrains": {
        "id": "jetbrains",
        "name": "JetBrains Developer Ecosystem Survey",
        "description": "OS used for development among software developers (annual survey)",
        "url": "https://www.jetbrains.com/lp/devecosystem/",
        "methodology": "Self-reported annual survey of ~20,000+ developers worldwide. "
                       "Multi-select OS question; shares can exceed 100%.",
        "covers": "desktop",
        "region": "global",
    },
}


class JSONStorageHandler:
    """Handles storage of data in monthly JSON files with manifest generation."""

    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        for subdir in ["steam", "statcounter", "dap", "cloudflare", "stackoverflow", "jetbrains"]:
            (self.data_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _source_dir(self, source_name):
        """Map a source display name to its directory name."""
        mapping = {
            "Steam": "steam",
            "StatCounter": "statcounter",
            "DAP": "dap",
            "Cloudflare": "cloudflare",
            "StackOverflow": "stackoverflow",
            "JetBrains": "jetbrains",
        }
        return mapping.get(source_name, source_name.lower())

    def store_data(self, data_points):
        """Store data points in monthly JSON files (one file per source per month)."""
        for point in data_points:
            source = point.get("source", "unknown")
            date_str = point.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                year_month = date_obj.strftime("%Y-%m")
            except ValueError:
                year_month = date_str[:7]

            source_dir = self._source_dir(source)
            file_path = self.data_dir / source_dir / f"{year_month}.json"
            file_path.parent.mkdir(parents=True, exist_ok=True)

            existing_data = []
            if file_path.exists():
                try:
                    with open(file_path, "r") as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    existing_data = []

            # Replace any existing entry for the same date
            date_key = point.get("date", "")
            existing_data = [e for e in existing_data if e.get("date") != date_key]
            existing_data.append(point)

            with open(file_path, "w") as f:
                json.dump(existing_data, f, indent=2)

    def get_data(self, source_id=None, start_date=None, end_date=None):
        """Retrieve data points filtered by source and/or date range."""
        source_dirs = [source_id.lower()] if source_id else ["steam", "statcounter", "dap", "cloudflare", "stackoverflow", "jetbrains"]
        data = []

        for source_dir in source_dirs:
            source_path = self.data_dir / source_dir
            if not source_path.exists():
                continue
            for file_path in sorted(source_path.iterdir()):
                if file_path.is_file() and file_path.suffix == ".json":
                    try:
                        with open(file_path, "r") as f:
                            data.extend(json.load(f))
                    except (json.JSONDecodeError, IOError):
                        continue

        if start_date or end_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
            filtered = []
            for item in data:
                try:
                    item_dt = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                    if start_dt and item_dt < start_dt:
                        continue
                    if end_dt and item_dt > end_dt:
                        continue
                    filtered.append(item)
                except ValueError:
                    filtered.append(item)
            data = filtered

        return data

    def generate_manifest(self):
        """Generate data/manifest.json listing all available data files and source metadata."""
        manifest = {
            "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sources": {},
        }

        for source_id, meta in SOURCE_METADATA.items():
            source_path = self.data_dir / source_id
            if not source_path.exists():
                continue

            files = sorted([
                f.stem  # "YYYY-MM" without .json
                for f in source_path.iterdir()
                if f.is_file() and f.suffix == ".json"
            ])
            if not files:
                continue

            manifest["sources"][source_id] = {
                **meta,
                "files": files,
                "date_range": {
                    "from": files[0],
                    "to": files[-1],
                },
            }

        manifest_path = self.data_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        print(f"Generated {manifest_path}")
        return manifest

    def generate_combined(self):
        """Generate data/combined.json — all data points merged and sorted.

        This single file is loaded by the web UI for efficient one-shot data loading.
        """
        all_data = self.get_data()

        # Sort by date then source for consistent ordering
        all_data.sort(key=lambda x: (x.get("date", ""), x.get("source", "")))

        # Build combined output
        sources_seen = sorted({p.get("source", "") for p in all_data})
        dates_seen = sorted({p.get("date", "") for p in all_data})

        combined = {
            "metadata": {
                "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "sources": sources_seen,
                "date_range": {
                    "from": dates_seen[0] if dates_seen else None,
                    "to": dates_seen[-1] if dates_seen else None,
                },
                "fields": ["linux_share", "windows_share", "mac_share", "chromeos_share", "wsl_share", "other_share"],
            },
            "data": all_data,
        }

        combined_path = self.data_dir / "combined.json"
        with open(combined_path, "w") as f:
            json.dump(combined, f, indent=2)

        print(f"Generated {combined_path} ({len(all_data)} data points)")
        return combined
