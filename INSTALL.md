# LinuxGroove Installation Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- git (for cloning the repository)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/kenvandine/linuxgroove.git
cd linuxgroove
```

### 2. Create a Virtual Environment (Optional but Recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
# Check Python version
python3 --version

# Check pip version
pip --version

# Run the main script
python3 -m src.main --help
```

## Manual Installation

If you prefer to install packages individually:

```bash
pip install requests beautifulsoup4 pandas matplotlib influxdb-client
```

## Docker Installation (Optional)

```bash
docker build -t linuxgroove .
docker run -it linuxgroove python3 -m src.main
```

## Troubleshooting

### Permission Errors

```bash
pip install --user -r requirements.txt
```

### Missing Dependencies

```bash
pip install requests beautifulsoup4 pandas matplotlib influxdb-client
```

### Virtual Environment Issues

```bash
# Deactivate current environment
deactivate

# Create new virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Next Steps

After installation:

1. Run data collection:
```bash
python3 -m src.main
```

2. View collected data:
```bash
ls -la data/steam/
ls -la data/statcounter/
ls -la data/dap/
```

3. Visualize data:
```bash
python3 -m src.visualization.visualize
```

## License

MIT License
