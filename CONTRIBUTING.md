# Contributing to Linux Groove Market Trends

Thank you for your interest in contributing to Linux Groove Market Trends! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Accept constructive feedback gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

- Use the GitHub issue tracker
- Include detailed steps to reproduce
- Include expected vs actual behavior
- Include system information (OS, Python version)

### Suggesting Enhancements

- Provide clear description of the feature
- Explain why it would be useful
- Include examples if possible

### Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip and git

### Installation

```bash
git clone https://github.com/kenvandine/linuxgroove.git
cd linuxgroove
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Tests

```bash
# Run adapter tests
python3 test_adapters.py

# Test individual adapters
python3 -c "from src.adapters.steam_adapter import SteamAdapter; a = SteamAdapter(); print(a.fetch_data())"

# Run full data collection
python3 -m src.main
```

## Coding Standards

### Python Style

- Follow PEP 8 style guidelines
- Use 4 spaces for indentation
- Keep lines under 80 characters
- Write meaningful variable names

### Documentation

- Document all public functions
- Include type hints
- Add docstrings to classes
- Update README.md for new features

### Code Organization

```
src/
├── adapters/          # Data source adapters
├── core/              # Core engine logic
├── storage/           # Data storage handlers
└── visualization/     # Data visualization
```

## Project Structure

### Adapters

All adapters should:
- Extend BaseAdapter
- Implement fetch_data()
- Handle date ranges
- Format data consistently

### Storage

Storage handlers should:
- Implement store_data()
- Implement get_data()
- Support date filtering
- Organize data by source

## Review Process

1. Maintainers review pull requests
2. Tests must pass
3. Code must meet standards
4. Documentation updated

## Recognition

- Contributors listed in README.md
- GitHub contributors page
- Release notes mentions

## Questions?

- Open an issue
- Check existing documentation
- Contact maintainers

## License

MIT License
