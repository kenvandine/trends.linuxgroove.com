# Candidate Data Sources

Sources considered for future integration. Sorted roughly by priority.

---

## Developer Surveys

### Devographics — State of Devs
- **URL:** https://stateofdevs.com
- **Cadence:** Annual (first edition: 2025)
- **OS data:** Yes — "What is the primary operating system in which you work?" (macOS / Windows / Linux)
- **Access:** Results published at https://2025.stateofdevs.com/en-US/technology/; raw data likely on GitHub at https://github.com/Devographics/surveys
- **2025 results:** macOS 57%, Windows 28%, Linux 15%
- **Notes:** New survey launched in 2025 covering non-technical aspects of developer life. Only one data point so far — not useful for trend tracking yet. Implement once a second year of data is published. State of JS / State of CSS / State of HTML (the older Devographics surveys) do **not** include an OS question.

### SlashData State of the Developer Nation
- **URL:** https://www.slashdata.co/developer-nation
- **Cadence:** Biannual (two surveys per year)
- **OS data:** Possibly — covers platforms and tools broadly
- **Access:** Summary reports are free; granular data requires purchasing the full report
- **Notes:** Very large sample (~20,000 respondents). Free tier may not expose OS breakdown detail; worth checking each report to see what's publicly available.

### InfoQ Developer Survey
- **URL:** https://www.infoq.com/articles/ (search "developer survey")
- **Cadence:** Irregular — not every year
- **OS data:** Sometimes — depends on the year's focus
- **Access:** Published publicly on InfoQ
- **Notes:** Inconsistent cadence and format make automation harder. Worth monitoring but low priority.

---

## AI / ML Developer Surveys

### Linux Foundation AI & Data / Open Source AI Report
- **URL:** https://www.linuxfoundation.org/research
- **Cadence:** Annual
- **OS data:** Possible — covers development environment and tooling
- **Access:** Free PDF download; raw data not always published
- **Notes:** Focuses on open-source AI tools and practitioners. Smaller sample than Kaggle/SO. Linux representation likely higher than average due to audience. Would need PDF extraction or manual data entry. Worth checking each year's report for an OS question.

### O'Reilly AI & Technology Salary Survey
- **URL:** https://www.oreilly.com/radar/
- **Cadence:** Annual
- **OS data:** Possible — includes developer environment questions
- **Access:** Report available free (registration may be required)
- **Notes:** Large sample of tech professionals; not strictly AI-focused but includes ML/AI practitioners. OS breakdown not confirmed in every edition; review report before implementing.

### Hugging Face Annual Report / Community Survey
- **URL:** https://huggingface.co/blog
- **Cadence:** Irregular
- **OS data:** Unknown — no confirmed OS question found
- **Access:** Published publicly on their blog
- **Notes:** Audience is AI/ML focused with heavy open-source use. No structured data download identified. Low priority unless they publish a formal survey with an OS question.

---

## Investigated — No OS Data

### Anaconda State of Data Science Survey
- **URL:** https://www.anaconda.com/state-of-data-science
- **Raw data:** https://github.com/anaconda/state-of-data-science
- **Status:** **No OS data** — investigated and ruled out
- **Notes:** The survey covers data science tools, workflows, and deployment environments (local vs. cloud) but does not ask which operating system respondents use. The 2023 CSV (the only edition with public raw data) confirms no OS question.

### CNCF Cloud Native Survey
- **URL:** https://www.cncf.io/reports/cncf-annual-survey/
- **Raw data:** https://github.com/cncf/surveys
- **Status:** **No OS data** — investigated and ruled out
- **Notes:** Raw CSVs focus on Kubernetes/container adoption, cloud providers, and CI/CD practices. Multiple years examined (2018, 2019, 2020, 2022) — none include a question about which OS developers use for their workstation or development environment.

### Eclipse Foundation Developer Survey
- **URL:** https://www.eclipse.org/community/eclipse_newsletter/
- **Status:** **Not viable** — investigated and ruled out
- **Notes:** The Eclipse IDE/developer platform survey (which tracked Windows/Linux/macOS workstation usage) ran 2007–2011 only and is no longer published. The ongoing Eclipse IoT & Edge Developer Survey (2018–present) tracks which OS runs *on embedded devices* (Linux vs FreeRTOS vs Zephyr), which is unrelated to desktop developer OS share.

### Wikimedia Analytics (Wikipedia traffic)
- **URL:** https://analytics.wikimedia.org/
- **Status:** **No public OS API** — investigated and ruled out
- **Notes:** OS data exists internally in Wikimedia's Hive/Druid infrastructure (`user_agent_map['os_family']`), but is not exposed through any public REST API. The public `wikimedia.org/api/rest_v1/metrics/` endpoints only provide pageview and unique-device counts without OS dimension. Accessing OS data requires authorized access to their analytics cluster.

### Kaggle ML & Data Science Survey
- **URL:** https://www.kaggle.com/c/kaggle-survey-2022
- **Status:** **Historical data only (2017–2022)** — not implemented; no ongoing updates
- **Notes:** The traditional ML & DS survey ran annually 2017–2022. The 2023 edition was replaced by an AI Report essay competition with no demographic OS data. No traditional survey with OS data has been published since 2022. The historical data is downloadable via the Kaggle API but without ongoing updates, this source doesn't meaningfully track continued Linux adoption.

---

## Web / Traffic Analytics

### W3Schools Browser Statistics
- **URL:** https://www.w3schools.com/browsers/
- **Cadence:** Monthly
- **OS data:** Yes — includes OS breakdown
- **Access:** Published publicly on their site
- **Notes:** Heavily skewed toward beginner/learning developers visiting W3Schools tutorials. Not representative of general web traffic but an interesting niche signal. HTML scraping required.

### W3Counter
- **URL:** https://www.w3counter.com/globalstats.php
- **Cadence:** Monthly
- **OS data:** Yes — OS breakdown published publicly
- **Access:** HTML scraping of their public stats page
- **Notes:** Similar to StatCounter but smaller sample. Publishes monthly OS stats going back several years. Would require HTML scraping since no public API exists. Lower priority given StatCounter already covers this niche.

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
