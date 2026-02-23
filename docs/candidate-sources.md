# Candidate Data Sources

Sources considered for future integration. Sorted roughly by priority.

---

## Developer Surveys

### Eclipse Foundation Developer Survey
- **URL:** https://www.eclipse.org/community/eclipse_newsletter/
- **Cadence:** Annual
- **OS data:** Yes — includes primary development OS breakdown
- **Access:** Results published publicly as PDF/HTML reports
- **Notes:** Skews toward Java/enterprise developers; smaller sample than SO or JetBrains but a distinct audience. Would complement the others well. Data extraction would likely require PDF parsing or HTML scraping of the results page.

### SlashData State of the Developer Nation
- **URL:** https://www.slashdata.co/developer-nation
- **Cadence:** Biannual (two surveys per year)
- **OS data:** Possibly — covers platforms and tools broadly
- **Access:** Summary reports are free; granular data requires purchasing the full report
- **Notes:** Very large sample (~20,000 respondents). Free tier may not expose OS breakdown detail; worth checking each report to see what's publicly available.

### CNCF Annual Survey (Cloud Native Computing Foundation)
- **URL:** https://www.cncf.io/reports/cncf-annual-survey/
- **Cadence:** Annual
- **OS data:** Partial — covers development/deployment environments
- **Access:** Full results published publicly including raw data on GitHub
- **Notes:** Audience is heavily Kubernetes/cloud-native focused, so Linux numbers will be very high (not representative of general developers). Useful as a "cloud developer" niche signal. Raw data available at https://github.com/cncf/surveys

### InfoQ Developer Survey
- **URL:** https://www.infoq.com/articles/ (search "developer survey")
- **Cadence:** Irregular — not every year
- **OS data:** Sometimes — depends on the year's focus
- **Access:** Published publicly on InfoQ
- **Notes:** Inconsistent cadence and format make automation harder. Worth monitoring but low priority.

---

## Web / Traffic Analytics

### W3Schools Browser Statistics
- **URL:** https://www.w3schools.com/browsers/
- **Cadence:** Monthly
- **OS data:** Yes — includes OS breakdown
- **Access:** Published publicly on their site
- **Notes:** Heavily skewed toward beginner/learning developers visiting W3Schools tutorials. Not representative of general web traffic but an interesting niche signal. HTML scraping required.

### Wikimedia Analytics (Wikipedia traffic)
- **URL:** https://analytics.wikimedia.org/
- **Cadence:** Monthly
- **OS data:** Yes — OS breakdown available via their public API
- **Access:** Fully public REST API
- **Notes:** Wikipedia's global audience is broad and representative. API is well-documented and reliable. Relatively easy to add. See https://wikitech.wikimedia.org/wiki/Analytics

---

## Hardware / Gaming

### GOG Galaxy (CD PROJEKT RED)
- **URL:** https://www.gogalaxy.com/
- **Cadence:** Unknown — no public reports found
- **OS data:** Potentially via community reports or leaks
- **Notes:** GOG has a strong Linux user base relative to its size. No public data API identified; low priority unless they publish reports.

### Itch.io
- **URL:** https://itch.io/game-development/top-rated (developer stats)
- **Cadence:** Unknown
- **OS data:** Anecdotally discussed in community; no formal public data source identified
- **Notes:** Indie game dev community with meaningful Linux representation. No structured public data source found.

---

## Notes on Adding a New Source

1. Create `src/adapters/{name}_adapter.py` extending `BaseAdapter`
2. Add metadata to `SOURCE_METADATA` in `src/storage/json_storage_handler.py`
3. Add the source directory to the lists in `json_storage_handler.py` (`__init__`, `get_data`, `_source_dir`)
4. Register the adapter in `src/core/engine.py`
5. Add to `--source` choices in `src/main.py`
6. Add to `SOURCE_CONFIG` in `web/index.html` — set `survey: true` if it's a developer survey so it appears in the Developer Surveys section rather than the main market share charts
