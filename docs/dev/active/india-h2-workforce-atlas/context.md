---
title: India H2 Workforce Atlas — Technical Context
status: active
created: 2026-03-18
---

# Technical Context

## Key Files

| File | Role |
|------|------|
| `scrape/scrape_ncs.py` | Highest-risk — NCS Portal Playwright scraper |
| `score/score.py` | Core scoring — Claude Code subagents, idempotent |
| `build/build.py` | Glue — merge, upskill paths, workforce gap, BASE_URL |
| `web/main.js.template` | Most complex frontend — D3 treemap, sidebar, toggles |
| `build/nco_ncs_crosswalk.csv` | Hand-built NCO-2015 → NCS mapping |

## Architecture Decisions

1. **No API key** — scoring via Claude Code subagents, not Anthropic API
2. **Pre-built data ships** — contributors don't need to scrape or score
3. **Static frontend** — vanilla HTML/CSS/D3.js, zero framework
4. **Dual hosting** — hygoat.in/workforce-atlas (canonical) + GitHub Pages (mirror)
5. **`__BASE_URL__` sentinel** — build.py injects correct path prefix

## Session Log

### 2026-03-18 — Sprint 0 scaffolding
- Created full directory structure per spec §2
- Initialized git repo with .gitignore, MIT license
- Created all 6 scoring prompt files
- Created config.py (no API, Claude Code only)
- README, DATASOURCES.md, dev docs
- Next: data source reconnaissance (NCS, PLFS, NCVET)
