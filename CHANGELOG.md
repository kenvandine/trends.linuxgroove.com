# Changelog

All notable changes to Linux Groove Market Trends will be documented in this file.

## [0.2.0] - 2025-06-30

### Added
- CLI argument parsing with date range support
- `--month` option for month-based data collection
- `--range-from` and `--range-to` options for date ranges
- Enhanced JSON storage handler with date filtering
- Improved visualization with date range support
- Comprehensive documentation (README, USAGE, IMPLEMENTATION, TEST, INSTALL, CONTRIBUTING)

### Changed
- Updated adapters to support date range fetching
- Modified engine to handle date parameters
- Improved data structure for better filtering

### Fixed
- Syntax errors in adapters and storage handlers
- Date format inconsistencies
- Data organization issues

## [0.1.0] - 2025-06-25

### Added
- Base adapter class with mock data
- Steam adapter with mock data
- StatCounter adapter with mock data
- DAP adapter with mock data
- JSON storage handler
- InfluxDB storage handler
- Data visualization module
- Core engine for orchestration

### Changed
- Initial project structure
- Adapter base implementation
- Storage handler implementations

## Version Format

- Major.Minor.Patch (e.g., 0.1.0)
- Breaking changes: Major version bump
- New features: Minor version bump
- Bug fixes: Patch version bump

## Release Notes

### 0.2.0 - Date Range Support
- Added comprehensive CLI argument parsing
- Implemented date range filtering across all components
- Enhanced data storage with date-based organization
- Improved visualization with date filtering
- Added extensive documentation

### 0.1.0 - Initial Release
- Implemented Source-Adapter-Storage pattern
- Created base adapter and concrete adapters
- Added storage handlers (JSON and InfluxDB)
- Basic data visualization

## Migration Guide

### From 0.1.0 to 0.2.0

1. Update dependencies:
```bash
pip install -r requirements.txt
```

2. Use new CLI options:
```bash
# Old way
python3 -m src.main

# New way with date range
python3 -m src.main --month 2025-06
python3 -m src.main --range-from 2025-06-01 --range-to 2025-06-30
```

3. Update data collection scripts to use new options

## Future Releases

### Planned for 0.3.0
- Real-time data collection
- Historical data archives
- Distribution breakdown visualization
- Statistical analysis tools

### Planned for 0.4.0
- Export to CSV/Excel
- Database backend support
- Web UI for data exploration

## License

MIT License
