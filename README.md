# India H2 Workforce Atlas

An open-source data intelligence tool that maps India's entire occupational landscape through a green hydrogen lens. Visualizes 4,000+ occupations scored across 6 H2-specific dimensions.

**Live atlas:** [hygoat.in/workforce-atlas](https://hygoat.in/workforce-atlas) (canonical)
**Mirror:** [ekavikalp.github.io/india-h2-jobs](https://ekavikalp.github.io/india-h2-jobs)

## Architecture

```
[ Data Pipeline ]  →  [ LLM Scoring ]  →  [ Frontend Atlas ]
  Python scripts        Claude Code          Static HTML/JS/D3
  NCS + PLFS +          6 H2-centric         Treemap + Summary Bar
  NCVET scrapers        dimensions           + CSV Download
  → occupations.csv     → scores.json        → hygoat.in/workforce-atlas
```

## Data Sources

| Source | Coverage | Access |
|--------|----------|--------|
| **NCS Portal** (ncs.gov.in) | 4,000+ occupation profiles | Playwright scraper |
| **PLFS** (NSO 2023–24) | Employment & wages by NCO-2015 | CSV download |
| **NCVET / Skill India Digital** | National Occupational Standards | Playwright scraper |

## Scoring Dimensions (0–10)

| Dimension | What it measures |
|-----------|-----------------|
| H2 Value Chain Adjacency | Direct presence in electrolysis, compression, storage, distribution, fuel cells |
| Green Transition Demand | Will demand rise as India scales toward 5 MMT H2 by 2030? |
| Skill Transferability | How quickly can someone upskill into H2-specific work? |
| Digital Automation Exposure | How much can AI/robotics automate this role in 5–10 years? |
| Formalization Rate | Formal vs informal employment (affects training scalability) |
| H2 Talent Scarcity Risk | Is this skill scarce enough to bottleneck H2 scale-up? |

## Quick Start

**Pre-built data ships with this repo.** No scraping or scoring needed to explore:

```bash
cd web && python -m http.server 8080
# Open http://localhost:8080
```

### Full Pipeline (maintainers only)

```bash
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt && playwright install chromium

python scrape/scrape_ncs.py        # Scrape NCS Portal
python scrape/download_plfs.py     # Download PLFS CSVs
python parse/parse_occupations.py  # Parse raw data
python tabulate/tabulate.py        # Generate occupations.csv
python score/score.py              # Score via Claude Code
python build/build.py              # Merge → occupations.json + web/main.js
```

## License

MIT — see [LICENSE](LICENSE).

## Credits

Built by [HyGOAT](https://hygoat.in) · [Ekavikalp Pvt Ltd](https://ekavikalp.com)
Data: NCS Portal, PLFS 2023–24, NCVET
Scoring: Claude AI (open-source prompts in `prompts/`)
