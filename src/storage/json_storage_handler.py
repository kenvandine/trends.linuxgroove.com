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
        "description": "Desktop OS market share based on web traffic analysis (worldwide)",
        "url": "https://gs.statcounter.com/",
        "methodology": "Aggregated web traffic from millions of websites globally",
        "covers": "desktop",
        "region": "worldwide",
    },
    "statcounter-us": {
        "id": "statcounter-us",
        "name": "StatCounter US",
        "description": "Desktop OS market share based on web traffic analysis (United States)",
        "url": "https://gs.statcounter.com/os-market-share/desktop/united-states-of-america",
        "methodology": "Aggregated web traffic from millions of websites in the United States",
        "covers": "desktop",
        "region": "us",
    },
    "statcounter-ca": {
        "id": "statcounter-ca",
        "name": "StatCounter Canada",
        "description": "Desktop OS market share based on web traffic analysis (Canada)",
        "url": "https://gs.statcounter.com/os-market-share/desktop/canada",
        "methodology": "Aggregated web traffic from millions of websites in Canada",
        "covers": "desktop",
        "region": "ca",
    },
    "statcounter-gb": {
        "id": "statcounter-gb",
        "name": "StatCounter UK",
        "description": "Desktop OS market share based on web traffic analysis (United Kingdom)",
        "url": "https://gs.statcounter.com/os-market-share/desktop/united-kingdom",
        "methodology": "Aggregated web traffic from millions of websites in the United Kingdom",
        "covers": "desktop",
        "region": "gb",
    },
    "statcounter-de": {
        "id": "statcounter-de",
        "name": "StatCounter Germany",
        "description": "Desktop OS market share based on web traffic analysis (Germany)",
        "url": "https://gs.statcounter.com/os-market-share/desktop/germany",
        "methodology": "Aggregated web traffic from millions of websites in Germany",
        "covers": "desktop",
        "region": "de",
    },
    "statcounter-na": {
        "id": "statcounter-na",
        "name": "StatCounter North America",
        "description": "Desktop OS market share based on web traffic analysis (North America)",
        "url": "https://gs.statcounter.com/os-market-share/desktop/north-america",
        "methodology": "Aggregated web traffic from millions of websites in North America",
        "covers": "desktop",
        "region": "na",
    },
    "statcounter-eu": {
        "id": "statcounter-eu",
        "name": "StatCounter Europe",
        "description": "Desktop OS market share based on web traffic analysis (Europe)",
        "url": "https://gs.statcounter.com/os-market-share/desktop/europe",
        "methodology": "Aggregated web traffic from millions of websites in Europe",
        "covers": "desktop",
        "region": "eu",
    },
    "statcounter-as": {
        "id": "statcounter-as",
        "name": "StatCounter Asia",
        "description": "Desktop OS market share based on web traffic analysis (Asia)",
        "url": "https://gs.statcounter.com/os-market-share/desktop/asia",
        "methodology": "Aggregated web traffic from millions of websites in Asia",
        "covers": "desktop",
        "region": "as",
    },
    "statcounter-sa": {
        "id": "statcounter-sa",
        "name": "StatCounter South America",
        "description": "Desktop OS market share based on web traffic analysis (South America)",
        "url": "https://gs.statcounter.com/os-market-share/desktop/south-america",
        "methodology": "Aggregated web traffic from millions of websites in South America",
        "covers": "desktop",
        "region": "sa",
    },
    "statcounter-af": {
        "id": "statcounter-af",
        "name": "StatCounter Africa",
        "description": "Desktop OS market share based on web traffic analysis (Africa)",
        "url": "https://gs.statcounter.com/os-market-share/desktop/africa",
        "methodology": "Aggregated web traffic from millions of websites in Africa",
        "covers": "desktop",
        "region": "af",
    },
    "statcounter-oc": {
        "id": "statcounter-oc",
        "name": "StatCounter Oceania",
        "description": "Desktop OS market share based on web traffic analysis (Oceania)",
        "url": "https://gs.statcounter.com/os-market-share/desktop/oceania",
        "methodology": "Aggregated web traffic from millions of websites in Oceania",
        "covers": "desktop",
        "region": "oc",
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
    "firefox": {
        "id": "firefox",
        "name": "Firefox Public Data Report",
        "description": "OS distribution among Firefox desktop release channel users (weekly)",
        "url": "https://data.firefox.com/dashboard/hardware",
        "methodology": "Weekly sample of Firefox telemetry from the desktop release channel",
        "covers": "desktop",
        "region": "global",
    },
}


class JSONStorageHandler:
    """Handles storage of data in monthly JSON files with manifest generation."""

    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        for subdir in ["steam", "statcounter", "dap", "cloudflare", "stackoverflow", "jetbrains", "firefox"]:
            (self.data_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _source_dir(self, source_name):
        """Map a source display name to its directory name."""
        mapping = {
            "Steam": "steam",
            "StatCounter": "statcounter",
            "StatCounter (US)": "statcounter",
            "StatCounter (United States)": "statcounter",
            "StatCounter (Canada)": "statcounter",
            "StatCounter (UK)": "statcounter",
            "StatCounter (United Kingdom)": "statcounter",
            "StatCounter (Germany)": "statcounter",
            "StatCounter (India)": "statcounter",
            "StatCounter (Japan)": "statcounter",
            "StatCounter (Brazil)": "statcounter",
            "StatCounter (North America)": "statcounter",
            "StatCounter (Europe)": "statcounter",
            "StatCounter (Asia)": "statcounter",
            "StatCounter (South America)": "statcounter",
            "StatCounter (Africa)": "statcounter",
            "StatCounter (Oceania)": "statcounter",
            "DAP": "dap",
            "Cloudflare": "cloudflare",
            "StackOverflow": "stackoverflow",
            "JetBrains": "jetbrains",
            "Firefox": "firefox",
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

            # Replace any existing entry for the same source and date
            source_key = point.get("source", "")
            date_key = point.get("date", "")
            existing_data = [e for e in existing_data
                             if not (e.get("source") == source_key and e.get("date") == date_key)]
            existing_data.append(point)

            with open(file_path, "w") as f:
                json.dump(existing_data, f, indent=2)

    def get_data(self, source_id=None, start_date=None, end_date=None):
        """Retrieve data points filtered by source and/or date range."""
        source_dirs = [source_id.lower()] if source_id else ["steam", "statcounter", "dap", "cloudflare", "stackoverflow", "jetbrains", "firefox"]
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
            # Handle statcounter region variants — they share the statcounter dir
            if source_id.startswith("statcounter"):
                source_path = self.data_dir / "statcounter"
                if not source_path.exists():
                    continue

                # Scan all files and extract unique source names
                source_files = {}  # {source_name: [files]}
                for file_path in sorted(source_path.iterdir()):
                    if file_path.is_file() and file_path.suffix == ".json":
                        try:
                            with open(file_path, "r") as f:
                                points = json.load(f)
                            for p in points:
                                src = p.get("source", "StatCounter")
                                if src not in source_files:
                                    source_files[src] = []
                                if file_path.stem not in source_files[src]:
                                    source_files[src].append(file_path.stem)
                        except (json.JSONDecodeError, IOError):
                            continue

                for src_name, files in source_files.items():
                    if not files:
                        continue
                    files.sort()
                    # Find matching metadata - use specific matching rules
                    src_meta = meta  # default to worldwide
                    if src_name == "StatCounter":
                        src_meta = SOURCE_METADATA["statcounter"]
                    elif "United States" in src_name:
                        src_meta = SOURCE_METADATA["statcounter-us"]
                    elif "Canada" in src_name:
                        src_meta = SOURCE_METADATA["statcounter-ca"]
                    elif "United Kingdom" in src_name:
                        src_meta = SOURCE_METADATA["statcounter-gb"]
                    elif "Germany" in src_name:
                        src_meta = SOURCE_METADATA["statcounter-de"]
                    elif "India" in src_name:
                        src_meta = SOURCE_METADATA["statcounter-in"]
                    elif "Japan" in src_name:
                        src_meta = SOURCE_METADATA["statcounter-jp"]
                    elif "Brazil" in src_name:
                        src_meta = SOURCE_METADATA["statcounter-br"]
                    elif "North America" in src_name:
                        src_meta = SOURCE_METADATA["statcounter-na"]
                    elif "Europe" in src_name:
                        src_meta = SOURCE_METADATA["statcounter-eu"]
                    elif "Asia" in src_name:
                        src_meta = SOURCE_METADATA["statcounter-as"]
                    elif "South America" in src_name:
                        src_meta = SOURCE_METADATA["statcounter-sa"]
                    elif "Africa" in src_name:
                        src_meta = SOURCE_METADATA["statcounter-af"]
                    elif "Oceania" in src_name:
                        src_meta = SOURCE_METADATA["statcounter-oc"]

                    # Build a display name for the source_id key
                    if src_name == "StatCounter":
                        manifest_key = "statcounter"
                    elif "United States" in src_name:
                        manifest_key = "statcounter-us"
                    elif "Canada" in src_name:
                        manifest_key = "statcounter-ca"
                    elif "United Kingdom" in src_name:
                        manifest_key = "statcounter-gb"
                    elif "Germany" in src_name:
                        manifest_key = "statcounter-de"
                    elif "India" in src_name:
                        manifest_key = "statcounter-in"
                    elif "Japan" in src_name:
                        manifest_key = "statcounter-jp"
                    elif "Brazil" in src_name:
                        manifest_key = "statcounter-br"
                    elif "North America" in src_name:
                        manifest_key = "statcounter-na"
                    elif "Europe" in src_name:
                        manifest_key = "statcounter-eu"
                    elif "Asia" in src_name:
                        manifest_key = "statcounter-as"
                    elif "South America" in src_name:
                        manifest_key = "statcounter-sa"
                    elif "Africa" in src_name:
                        manifest_key = "statcounter-af"
                    elif "Oceania" in src_name:
                        manifest_key = "statcounter-oc"
                    else:
                        manifest_key = f"statcounter-{src_name.lower().replace(' ', '-')}"

                    manifest["sources"][manifest_key] = {
                        **src_meta,
                        "files": files,
                        "date_range": {
                            "from": files[0],
                            "to": files[-1],
                        },
                    }
                continue

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
