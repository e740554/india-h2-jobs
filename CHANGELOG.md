# Changelog

All notable changes to this project will be documented in this file.

## [1.4.3.0] - 2026-05-14

### Added
- Checked in `model/plfs_supply.json` from PLFS 2023-24 Annual Report Table 25 NCO-2015 2-digit subdivision shares, with indicative headcounts derived from the PLFS all-age usual-status WPR and 2024 India population denominator.
- Added supply-backed gap activation, supply coverage metadata, PLFS supply fields in generated occupation JSON, dev/public `plfs_supply.json` copies, and supply columns in H2-ready/current/snapshot CSV export paths.

### Changed
- Headline workforce gap now uses `supply_estimate` for H2-ready occupations rather than requiring `employment` coverage.
- Gap and methodology copy now explicitly say the estimate is subdivision-allocated, indicative, and not occupation-observed. Unit-level PLFS microdata remains post-WHS.
- Removed the shipped PLFS supply-input item from `TODOS.md`.

### Tests
- Added regression tests for checked-in PLFS supply coverage, H2-ready supply gating, supply-backed gap support, CSV supply fields, and zero-H2-ready null handling.
- Verified with `python -m pytest`, JS syntax checks, and headless Chrome QA for Atlas, Scenario, Gap, CSV export, Methodology, and About.

## [1.4.2.1] - 2026-05-11

### Changed
- **Build-time HTML chunk includes** (`build/build.py`): extracted shared `<nav class="atlas-nav">` and `<footer class="atlas-footer">` from 3 pages into `web/_chunks/nav.html` and `web/_chunks/footer.html`. Pages use `<!-- #include nav -->` and `<!-- #include footer -->` markers resolved at build time with `{{var}}` substitution (rel_root, aria_current per page, mode_toggle block, footer secondary). Zero new dependencies — pure Python `str.replace()`, no Jinja2. Single source of truth for chrome eliminates copy-paste drift across atlas, methodology, and about pages
- `web/` is now fully canonical for all page templates; the old `docs/ → web/` backward sync for static pages is removed

### Tests
- `test_build_outputs_methodology_and_about_pages` updated: supplies `_chunks/` fixtures in temp dir and verifies forward-sync `web/ → docs/` via include resolution. 166/166 passing

## [1.4.2.0] - 2026-05-11

WHS Rotterdam 2026 launch release. Atlas augmentations plus two new static pages, packaged as a credibility instrument for the World Hydrogen Summit (Tue May 19 17:30 CEST).

### Added
- **`/methodology/` page**: single-column research document with sticky 280px TOC (desktop) / native `<select>` "Jump to section" (mobile). Six H₂ adjacency dimensions rendered as semantic `<dl>` with green left-border accents. Bordered "Caveats and limitations" callout for sample-size policy. NCO extension policy, scoring reproducibility section with inline repo link. No CTA buttons, no feature grids, no icons-in-circles
- **`/about/` page**: minimal Contact-only page. Advisory Circle removed per founder decision; institutional grounding deferred to post-WHS TODO
- **Shared atlas chrome across all three pages**: 3-link nav (Atlas / Methodology / About) with `aria-current` and 2px green underline active state; shared minimal footer with `mailto:ekansh@ekavikalp.com`
- **`?lens=maritime` URL deep-link**: parses on init, preselects Maritime sector in sidebar `<select id="sectorFilter">`, renders dismissible lens-arrival banner. Banner: 3px green left accent, gray-50 bg, copy `Viewing: Maritime Occupations lens.`, 44×44 close button with `aria-label`. Dismisses on close click OR first user filter change. One-way URL→state contract: filter changes do not mutate `location.search`
- **Sidebar inline methodology link** on every occupation entry: `How is this scored? → Methodology` in Mukta 0.75rem, `--text-muted`, plain text (not a button)
- **`low_sample` tooltip**: gap-mode returns `low_sample` status when `supply.sample_count < 30`, regardless of demand. Renders 6px orange dot (`--color-goat`) next to the supply number; tooltip reuses DESIGN.md dark-slate pattern with copy `PLFS 2023-24 sample size <30, indicative only`. Hover, focus, and mobile tap all show
- **Freshness badge** in summary bar (right-aligned): `Last Updated: May 2026 · PLFS 2023-24`
- **Atlas subtitle** under summary bar: `India's 1,802 occupations scored against the H₂ economy.`
- **Slow-load state**: muted `Loading 1,802 occupations…` line in `#treemap` area, hidden by JS once D3 paints. Chrome (nav, summary bar, controls, footer) renders immediately from static HTML
- **`URL_FREEZE.md`**: canonical URLs snapshot with build-time guarantee. Frozen paths must not change between Fri May 15 EOD and Tue May 19 17:30 CEST without an explicit redirect entry
- **`RUNBOOK.md`**: bus-factor recovery doc per Critical Path 8. Clone, build, deploy, hotfix, rollback, domain ownership, troubleshooting. F2 dry-run on clean machine required before launch
- **`scripts/generate_qr.py`**: reads canonical URL from `URL_FREEZE.md` (drift-proof), outputs `assets/qr-workforce-atlas.svg` and `qr-workforce-atlas-1024.png` with error correction level Q
- **`scripts/smoke_prod.ps1`**: PowerShell production smoke for Sun May 17 morning. Curls every URL in `URL_FREEZE.md`, asserts 200, asserts page content markers
- **QR assets**: `assets/qr-workforce-atlas.svg` (vector) and `qr-workforce-atlas-1024.png` (1024×1024) for the one-pager designer

### Changed
- **Build pipeline** (`build/build.py`) supports nested doc subdirectories. `DOC_STATIC_SUBDIRS` constant lists `methodology` and `about`; sync creates parent dirs when copying nested paths and reverse-syncs static pages `docs/ → web/` for dev parity. Sync direction documented in a comment block; mtime check warns when a newer source would be overwritten
- **Mobile nav (≤768px)** uses `flex-wrap` with shrunken typography (0.78rem links, 0.85rem logo) so all three nav links fit in a 375px viewport. Fixes Browser QA P1 finding where Methodology and About were off-screen
- **Footer pattern** unified across atlas, methodology, and about

### Removed
- **Plausible analytics snippet** stripped from all pages. Telemetry deferred to post-WHS TODO; Plausible/Cloudflare built-in referrer view covers WHS week sufficiently
- **Green Iron lens (T0.12)** cut from WHS scope per `/plan-design-review` outside-voice review. Indian-context occupation specificity too thin relative to Maritime / RFNBO; would become the most-attacked surface for a hostile economist. Move to post-WHS
- **RFNBO lens (T0.11)** removed from URL freeze and lens whitelist pending confirmed sector mapping when `H2-RFNBO-*` occupations land
- **Advisory Circle** section on `/about/` per founder

### Tests
- **DR-1** (`tests/test_build.py`): `<link rel="stylesheet" href="../style.css">` present in both `docs/methodology/index.html` and `docs/about/index.html`. Catches inlined-style regression
- **DR-2** (`tests/test_build.py`): `Mukta` string present in `docs/style.css`. Catches `@import` drop on stylesheet regeneration
- **DR-3** (`tests/test_ui_logic.py`): sector `<select>` lives inside the sidebar; `style="display:none"` in HTML source; visibility unhidden only when `activeLens` is set
- **Freshness** (ER-15): `Last Updated` and `PLFS 2023-24` strings present in `docs/index.html` and `docs/methodology/index.html`
- **Analytics absence**: explicit assertion that no Plausible snippet exists on any page (post-strip safety net)
- **URL freeze** (`tests/test_url_freeze.py`, 6 tests): every canonical path in `URL_FREEZE.md` resolves under `docs/` after build
- **QR** (`tests/test_qr.py`, 5 tests): generator produces SVG + PNG, PNG ≥ 1024×1024, SVG viewBox square
- **Runbook** (`tests/test_runbook.py`, 2 tests): file exists, required sections present

166 tests total (up from 141), all green.

### Plan provenance
Drives test plan: `74055-master-eng-review-test-plan-20260511-145750.md`. Eng review: CLEAR (PLAN), 9 issues, 3 critical gaps resolved. Design review: CLEAR (FULL), score 3/10 → 9/10, 17 decisions added. Outside voice: DeepSeek V4 Pro, 5 hard rejections all addressed. Browser QA: 5 PASS, 1 founder-call, 2 deferred — SHIP-WITH-FIXES; P1 mobile nav addressed in this release; deploy gap closed by this release's `docs/` regeneration and push.

## [1.4.1.0] - 2026-03-31

### Added
- **Focus view default**: atlas opens to ~64 high-relevance occupations (H2 Adjacency ≥ 5) with a 3-state progressive disclosure toggle (focus → 480 H2-sector → 1,802 all) replacing the old 2-state boolean
- **Client-side KPI recomputation**: summary bar H2-Ready and Fast Upskill Paths counts now update per view tier from the displayed occupation set
- **Treemap keyboard navigation**: roving-tabindex pattern — one SVG tab stop, arrow keys traverse cells, Enter/Space activates, focus ring restored on blur
- **Sidebar header accent**: colored left border matching the selected occupation's H2 adjacency score band
- **Pathway CTA** on Overview tab switches directly to Pathways when pathways exist
- **Skill pills**: bridging skills rendered as rounded badge pills instead of a plain list
- **Source → Target directional styling** in pathway cards (muted from, orange arrow, bold to)
- **Dark 2-row footer** matching nav bar
- **CSS design token block**: formal spacing (`--space-1`–`--space-12`), elevation (`--shadow-sm/md/lg`), radius (`--radius-sm/md/lg/full`), transition (`--ease-out`, `--duration-fast/normal`), and `--sidebar-width`
- **Sidebar** expanded to 360px with thin custom scrollbar and bottom fade gradient overlay
- **Gap tab** restyled as data-gated (`.mode-btn-gated`) with "data pending" label — kept as shipped feature

### Changed
- Sector toggle hidden (not disabled) in Scenario/Gap modes and correctly restored on Atlas return
- Full Scenario Snapshot CSV download hidden outside scenario+valid-scenario state
- Sidebar scrollable state initialised on content show via `requestAnimationFrame`, not only on scroll
- Scroll fade overlay moved from broken `sticky ::after` on scroll container to `position: absolute ::after` on `.atlas-main` with `:has()` selector (cross-browser reliable)
- Nav bar depth shadow added via `--shadow-md`; mode button active/inactive contrast improved

### Fixed
- SVG roving tabindex: container restored to `tabindex="0"` on `focusout`; was leaving two sequential tab stops after first navigation
- `querySelector(".pathway-cta")` scoped to `#overviewPanel` to prevent wrong-panel removal
- `fastUpskillCount` null guards made consistent with `h2_adjacency` null check
- Dead `menu-item-disabled` guard removed from snapshot download click handler
- `scrollIntoView` uses `requestAnimationFrame` instead of bare `setTimeout(50)` for bridging skills expand

### Tests
- 6 new `tests/test_ui_logic.py` cases: focus filter count, focus filter exclusion, client-side metric recomputation, boundary (adj=5.0 passes focus but is not H2-ready), `viewTier` state cycle, mode-switch resets

## [1.4.0.0] - 2026-03-30

### Added
- **Phase 3 frontend/runtime integration** in the single-page atlas: geography filter, year slider,
  phase recoloring, pathways tab/cards, empty states, and chunked CSV export progress
- **Cluster distribution layer** with `model/clusters.json`, `model/clusters.py`, and synced
  `docs/` / `web/` model data
- **Timeline layer** with `model/timeline.py`, scenario `start_year` / `target_year`, and
  annual workforce snapshots through `target_year + 5`
- **Reskilling pathway layer** with `model/pathways.json`, `model/pathways.py`, and sidebar
  pathway summaries including overlap, duration, cost, and bridging skills
- **Extended export coverage** for current-view and full-snapshot CSV outputs with cluster, year,
  phase, and pathway-derived fields
- **New tests** for clusters, timeline, pathways, UI helper logic, and CSV export shape

### Changed
- `web/main.js.template` now exports a shared runtime used by both the browser SPA and the Node
  parity harness
- JS parity coverage now compares Python and JS cluster distribution and timeline output, not only
  the single-archetype demand path
- Build output now syncs `clusters.json` and `pathways.json` to `docs/` and `web/`
- Documentation updated to reflect Phase 3 as shipped rather than planned

### Fixed
- JS rounding now matches Python's banker-style rounding for parity-sensitive timeline and cluster
  calculations
- Gap mode now shows the correct legend instead of inheriting the scenario legend
- Full snapshot export and runtime helper coverage now validate the generated row set explicitly

## [1.3.0.0] - 2026-03-30

### Added
- **Supply gap engine (Phase 2)** — 3-way Atlas/Scenario/Gap mode toggle. Gap mode shows
  red (shortage) to green (surplus) treemap with per-occupation supply vs. demand breakdown
- **3 new archetypes** — PEM electrolyser (500 MW), green ammonia synthesis (1 MTPA), and
  dedicated solar+wind hybrid (2 GW) with full coefficient arrays across project phases
- **Multi-archetype scenarios** — composable scenarios with production/downstream/upstream
  chains. 4 new presets: 1 MT pilot, 5 MT mixed, 10 MT ambitious, Adani Kutch Phase 1
- **PLFS supply baseline** — `model/supply.py` loads and allocates PLFS 2023-24 labour
  supply estimates by NCO subdivision to individual occupations
- **Scenario preset dropdown** — select from NGHM scenario presets, slider syncs to target
- **67 new tests** — `test_multi_archetype.py` (18), `test_gap.py` (12), `test_supply.py` (11),
  plus updated `test_compute.py` for backwards compatibility (96 total)
- **Gap sidebar** — per-occupation supply, demand, gap, and percentage breakdown
- **Archetype breakdown** — sidebar shows demand contribution from each archetype

### Changed
- Scenario mode colours use brand palette (green→red) instead of orange gradient
- Footer shows GitHub icon+link instead of plain text attribution
- Logo image removed from header nav
- README rewritten as comprehensive self-explanatory guide
- Scenario bar updated with preset dropdown and expanded MT slider range (0.5-15)
- `build.py` merges PLFS supply data and writes explicit null supply fields

### Fixed
- `decodeEntities()` regression — HTML entities in 22 occupation titles now render correctly
  (DOMParser-based decoder replaces broken textContent pattern)
- JS/Python parity for NCO 9312 — unallocated demand now tracked in JS engine (was silently
  dropped, causing ~12% under-report for RE scenarios)
- Phase bar division-by-zero edge case when demand rounds to 0
- Slider/scenario initial state mismatch on first mode switch

### Removed
- `CLAUDE.md` untracked from git (moved to .gitignore, local-only)

## [1.2.0.0] - 2026-03-30

### Added
- **Scenario engine (Phase 1)** — set an MT hydrogen capacity target on a slider and see
  occupation-level workforce demand cascade across the treemap. One archetype (1 GW alkaline
  electrolyser) with 48 occupation coefficients across construction, commissioning, and operations
- **Atlas/Scenario mode toggle** — switch between the scored occupation atlas and the demand
  scenario model. Scenario mode shows orange demand-intensity tiles, phase breakdown per
  occupation, and coefficient provenance in the sidebar
- **`model/` directory** — `archetypes.json` (asset archetypes with occupation coefficients),
  `scenarios.json` (3 NGHM presets: 1 MT/2027, 5 MT/2030, 10 MT/2035), and `compute.py`
  (Python validation/export engine matching JS logic)
- **Python/JS parity tests** — verify both engines produce identical demand results for the
  same inputs (tested at 1 MT and 5 MT)
- **29 compute engine tests** — comprehensive pytest coverage for the 5-step model chain
  (MT → units → demand → allocation → aggregation)
- **Build pipeline** copies `archetypes.json` and `scenarios.json` to `docs/` and `web/`

### Changed
- **Summary bar** relabels in scenario mode: "Occupations in Demand", "Total Workforce Demand",
  "Plant Units Needed" — restores original labels when switching back to Atlas mode
- **Treemap sizing** uses demand headcount in scenario mode (instead of H2 relevance scores)
- **Sector toggle** is disabled in scenario mode (demand is archetype-scoped, not sector-filtered)

## [1.1.1.0] - 2026-03-30

### Added
- **21 unit tests** for the build pipeline (`pct`, `merge_scores`, `compute_upskill_paths`,
  `compute_workforce_gap`, `compute_summary_metrics`, `compute_data_quality`) — run with
  `python -m pytest`
- **GitHub Actions CI** runs tests on every push and PR
- **`TESTING.md`** — how to run tests, coverage conventions, and test layer descriptions
- **`TODOS.md`** — planned work backlog: branding polish, DESIGN.md, test coverage expansion,
  and treemap O(n²) optimization

### Changed
- `requirements.txt` now includes `pytest` and `pytest-cov` — `pip install -r requirements.txt`
  gives a complete dev environment with tests ready to run
- `CLAUDE.md` documents the test setup and coverage expectations for contributors

### Fixed
- Clarified the `compute_workforce_gap` edge case when no H2-ready occupations exist:
  the function returns the full target gap (not `None`) due to vacuous evaluation on an empty
  list — documented in tests with an explanatory comment

## [1.0.0.0] - 2026-03-29

### Added
- **Public atlas baseline** with 1,802 scored NCS occupations and a default filtered view of
  480 occupations across 12 H2-relevant sectors
- **Static D3 treemap frontend** with atlas tiles, sidebar details, summary metrics, and CSV
  download for the public GitHub Pages mirror
- **GitHub Pages publish output** in `docs/` and an open-source-ready source/publish repo layout
- **Contributor-facing repo docs** for the public atlas baseline, including the first
  `CONTRIBUTING.md` workflow guidance

### Changed
- The repository layout was aligned around `web/` as the editable frontend source of truth and
  `docs/` as generated publish output
