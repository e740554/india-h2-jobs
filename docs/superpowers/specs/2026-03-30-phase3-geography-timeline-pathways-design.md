# Phase 3: Geography, Timeline & Reskilling Pathways

**Date:** 2026-03-30
**Branch:** `phase3/v1.3`
**Version target:** 1.4.0.0
**Status:** Design approved

## Overview

Phase 3 adds three features layered onto the existing treemap UI:

1. **Geography/Cluster Distribution** — Distribute national workforce demand across 10 hydrogen innovation clusters and 8+ states using archetype-affinity coefficients.
2. **Time Phasing (Annual Snapshots)** — Generate year-by-year workforce demand with construction/commissioning/operations phase ramp-up curves.
3. **Reskilling Pathways** — Explicit occupation-to-occupation transition mappings with duration, cost, training type, and bridging skills.

All three features integrate into the existing single-page treemap view — no new pages. This keeps the tool complementary to h2hubs.in (which provides the geographic map and infrastructure layer) rather than competing with it.

## Design Principles

- **Complement, don't compete** with h2hubs.in — they have the map, we have workforce depth
- **Same architecture** as Phases 1-2 — JSON data files, Python engine, JS mirror, parity tests
- **Layered onto existing UI** — new controls (cluster dropdown, year slider, pathway panel) extend the current page
- **MoSPI-enriched** — pull real labour statistics from PLFS, ASI, EC, AISHE datasets via MCP integration

---

## 1. Geography/Cluster Distribution

### Data Model: `model/clusters.json`

```json
{
  "clusters": [
    {
      "id": "kutch",
      "name": "Kutch Hydrogen Valley",
      "state": "Gujarat",
      "type": "hydrogen_valley",
      "lat": 23.7,
      "lng": 69.8,
      "archetype_affinity": {
        "alkaline_1gw": 0.35,
        "pem_500mw": 0.10,
        "ammonia_1mtpa": 0.25,
        "solar_wind_hybrid_2gw": 0.30
      }
    }
  ],
  "states": [
    {
      "id": "GJ",
      "name": "Gujarat",
      "clusters": ["kutch", "mundra", "jamnagar"],
      "plfs_state_code": "24"
    }
  ]
}
```

**Affinity constraints:**
- Every archetype ID in `archetypes.json` must be present in every cluster's `archetype_affinity` map. Missing entries are treated as 0.0.
- For each archetype, the sum of that archetype's affinity across all clusters must equal 1.0 (demand is fully distributed, none lost).
- A PEM-heavy scenario shifts demand toward clusters with higher PEM affinity.

### Initial Clusters (10)

| Cluster | State | Type | Key Driver |
|---------|-------|------|------------|
| Kutch | Gujarat | Hydrogen Valley | Largest announced capacity |
| Mundra | Gujarat | Industrial Hub | Adani green H2 complex |
| Jamnagar | Gujarat | Refinery Hub | Reliance refinery complex |
| Vizag | Andhra Pradesh | Port + Refinery | HPCL refinery + port access |
| Paradip | Odisha | Petrochemical | Fertilizer + petrochemical corridor |
| Tuticorin | Tamil Nadu | Port + Industrial | Southern industrial hub |
| Barmer/Jodhpur | Rajasthan | RE Corridor | Solar energy corridor |
| Haldia | West Bengal | Petrochemical | Eastern petrochemical corridor |
| Kochi | Kerala | Refinery | BPCL refinery |
| Bina | Madhya Pradesh | Refinery | BPCL refinery |

### Computation: `model/clusters.py`

```python
def distribute_demand_by_cluster(demand_records, clusters):
    """
    Distribute national demand to clusters using archetype affinities.

    Input: the un-aggregated demand records list from compute_multi_archetype_demand(),
    where each record has archetype_id, occupation_id, phase, and demand. The archetype_id
    is required to look up the correct cluster affinity for each record.

    Algorithm:
      1. For each demand record (which preserves archetype_id and phase):
         for each cluster:
           cluster_demand = record.demand * cluster.archetype_affinity[record.archetype_id]
      2. Aggregate per cluster, per occupation, per phase.

    This preserves phase information (construction/commissioning/operations) through
    to the cluster level, enabling per-cluster timeline snapshots downstream.
    """
```

**Input:** un-aggregated demand records list from `compute_multi_archetype_demand()` — each record has `archetype_id`, `occupation_id`, `phase`, `demand`. Must NOT use the aggregated `by_occupation` dict, as that loses archetype provenance needed for affinity lookup.

**Output:**
```json
{
  "kutch": {
    "occ_1234": {
      "construction": 80, "commissioning": 20, "operations": 50, "total": 150
    }
  },
  "vizag": {
    "occ_1234": {
      "construction": 40, "commissioning": 10, "operations": 30, "total": 80
    }
  }
}
```

### MoSPI Enrichment Per Cluster

| Dataset | Indicator | Use |
|---------|-----------|-----|
| ASI | Total Workers (32) by state + NIC code | Existing industrial workforce in H2-relevant sectors per state |
| PLFS | LFPR (1), UR (3) by state | Labour participation and unemployment — reskilling pool size |
| EC | District-level establishment counts | Map existing businesses to cluster regions |
| PLFS | Avg wages (6, 7, 8) by state | Wage baselines for reskilling cost-benefit analysis |

MoSPI data is fetched at build time and cached in `model/mospi_cache.json`. Not baked into clusters.json — kept separate for freshness. No real-time MoSPI queries in the browser.

### UI: Cluster Filter Dropdown

- Appears next to the scenario preset dropdown in Scenario/Gap modes
- Options: "All India (National)" (default) + each cluster + "By State" sub-group
- Selecting a cluster filters the treemap to show only demand allocated to that region
- Summary bar updates: "Kutch Valley: 3,200 workers needed"

---

## 2. Time Phasing (Annual Snapshots)

### Data Model: Scenario Extension

Existing `model/scenarios.json` adds a `start_year` field to each preset. The existing `year` field becomes `target_year` (renamed for clarity).

**Migration:** The existing `year` field is renamed to `target_year`. A new `start_year` field is added. For scenarios where `start_year` is absent, the default is `target_year - 3`.

The existing `production`/`downstream`/`upstream` structure is **preserved exactly** — no `archetype_mix` flattening. The three-tier structure carries distinct semantics (`share` vs `conversion_share` vs `re_ratio_gw_per_gw_electrolyser`) required by the multi-archetype demand engine.

```json
{
  "id": "nghm_5mt_2030_mix",
  "name": "5 MT by 2030 (Mixed)",
  "target_mt": 5,
  "start_year": 2026,
  "target_year": 2030,
  "description": "5 MT target with 60/40 alkaline/PEM split...",
  "production": [
    {"archetype_id": "alkaline_1gw", "share": 0.60},
    {"archetype_id": "pem_500mw", "share": 0.40}
  ],
  "downstream": [
    {"archetype_id": "ammonia_1mtpa", "conversion_share": 0.70}
  ],
  "upstream": [
    {"archetype_id": "solar_wind_hybrid_2gw", "re_ratio_gw_per_gw_electrolyser": 2.5}
  ]
}
```

**Backward compatibility:** Single-archetype scenarios (with `archetype_id` instead of `production`/`downstream`/`upstream`) also get `start_year`/`target_year`. Per Spec Correction: `year` is renamed to `target_year` with no alias (pre-1.0, no external consumers). All code reads `target_year` directly.

### Computation: `model/timeline.py`

```python
def compute_timeline(scenario, occupations, clusters=None):
    """
    Generate year-by-year demand snapshots with phase ramp-up curves.

    Phase model (linear interpolation):
      - Construction: ramps start_year → peak at target_year-2 → tapers to 0 by target_year
      - Commissioning: ramps target_year-2 → peak at target_year-1 → tapers to 0 by target_year+1
      - Operations: ramps target_year-1 → full at target_year → sustains indefinitely

    If clusters provided, output is per-cluster per-year.
    """
```

**Output:**
```json
{
  "2025": { "occ_1234": { "construction": 50, "commissioning": 0, "operations": 0, "total": 50 } },
  "2026": { "occ_1234": { "construction": 120, "commissioning": 0, "operations": 0, "total": 120 } },
  "2028": { "occ_1234": { "construction": 0, "commissioning": 30, "operations": 200, "total": 230 } }
}
```

### Phase Ramp-Up Model

```
Demand
  ^
  |        Construction
  |       /\
  |      /  \        Operations
  |     /    \      ___________
  |    /      \    /
  |   /  Comm  \  /
  |  /   /\    \/
  | /   /  \  /
  |/___/____\/________________> Time
  start    target-2  target  target+2
```

- Construction workforce is largest in early years, tapers as plants near completion
- Commissioning is a short peak near the target year
- Operations is the sustained long-term workforce

### UI: Year Slider

- Appears below the MT slider in Scenario/Gap modes
- Range: `start_year` to `target_year + 5`
- Dragging updates the treemap to show that year's demand (colored by phase)
- Summary bar: "Year 2028: 8,400 construction / 2,100 commissioning / 4,500 operations"
- Combined with cluster filter: "Kutch 2028: 1,200 construction / 300 commissioning"

---

## 3. Reskilling Pathways

### Data Model: `model/pathways.json`

```json
{
  "pathways": [
    {
      "source_nco": "3134.0100",
      "source_title": "Petroleum Refinery Operator",
      "target_nco": "3134.0200",
      "target_title": "Electrolyser Operations Technician",
      "reskill_months": 6,
      "reskill_cost_inr": 85000,
      "training_type": "certification",
      "training_provider": "NSDC / Skill India",
      "skill_overlap": 0.72,
      "bridging_skills": [
        "PEM membrane handling",
        "High-pressure H2 safety",
        "Electrolyser diagnostics"
      ],
      "source": "IRENA 2024 + CEEW skill mapping"
    }
  ]
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `source_nco` | string | NCO code of the source (existing) occupation |
| `target_nco` | string | NCO code of the target (H2) occupation |
| `reskill_months` | int | Estimated calendar time (3-24 months) |
| `reskill_cost_inr` | int | Estimated training cost in INR |
| `training_type` | enum | `on_the_job`, `certification`, `diploma`, `degree` |
| `training_provider` | string | Recommended provider (NSDC, ITI, university, etc.) |
| `skill_overlap` | float | 0-1 pairwise score, independently LLM-scored per pathway (not mechanically derived from the single-occupation `skill_transferability` dimension — that is a per-occupation score, not pairwise) |
| `bridging_skills` | array | Specific new skills needed for the transition |
| `source` | string | Data provenance |

### Generation Approach

LLM-scored in batches (same pattern as the 6-dimension scoring pipeline):
1. For each of the 480 H2-sector occupations, identify top 3-5 transition source occupations
2. Claude scores pathway attributes based on NCS occupation descriptions + qualification requirements
3. Results merged into `pathways.json`
4. Estimated output: ~1,500-2,000 pathway entries

### MoSPI Enrichment

| Dataset | Indicator | Pathway Use |
|---------|-----------|-------------|
| PLFS | Avg regular wages (6) | Wage uplift calculation: "(target wage - source wage) = INR X/month gain after reskilling" |
| PLFS | Worker distribution (4) by industry | Size the reskilling pool: "14,000 refinery operators nationally" |
| ASI | Workers by state + NIC (32) | State-level pool: "Gujarat has 4,200 chemical plant operators" |
| AISHE | Enrollment by state + discipline | Training capacity: "Tamil Nadu ITIs graduate 2,000 instrumentation techs/year" |

### Computation: `model/pathways.py`

```python
def get_pathways_for_occupation(nco_code, pathways, direction="both"):
    """
    Return pathways where this occupation is source (outbound) or target (inbound).

    direction: "in" (who can reskill into this), "out" (where this worker can go), "both"
    """

def compute_reskillable_supply(occupation, demand_gap, pathways, supply_data):
    """
    For a given occupation with a demand gap, compute how many workers from
    adjacent occupations could realistically fill the gap through reskilling.

    Returns: reskillable_count, avg_months, avg_cost, top_source_occupations
    """
```

### UI: Pathway Panel

Click any occupation tile in the treemap to expand the existing sidebar. New "Reskilling Pathways" tab shows:

- **Pathways IN** — occupations that can reskill into this job (sorted by highest skill overlap — Decision 7A: visual hierarchy and sort order tell the same story)
- **Pathways OUT** — where this occupation's workers can transition to (also sorted by highest overlap)
- Each pathway card (overlap-first visual hierarchy, Decision 4B):
  ```
  ┌──────────────────────────────────┐
  │ ███████████░░░░  72% overlap     │  ← Visual anchor: skill overlap bar
  │ Petroleum Ref → Electrolyser     │  ← Transition: source → target titles
  │ 6 months · ₹85k · Certification │  ← Metadata row: duration · cost · type badge
  │ ▸ 3 bridging skills              │  ← Expandable: click to reveal skill list
  └──────────────────────────────────┘
  ```
  - **Overlap bar** fills left-to-right, colored by range: ≥0.7 teal (`#0d9488`), 0.4-0.69 amber (`#f59e0b`), <0.4 red (`#ef4444`)
  - **Training type badge** uses existing `.sb-meta span` pattern (gray pill: `background: var(--gray-100)`)
  - **Bridging skills** collapsed by default. Expand reveals bullet list: "PEM membrane handling, High-pressure H2 safety, Electrolyser diagnostics"
  - Cards separated by 1px `var(--gray-100)` border (reuses `.upskill-item` separator pattern)
  - Pathway card click: no action (not navigable — this is the detail view)
- **MoSPI stats** when available: supply count, avg wage, state distribution
- **Reskillable supply summary** in Gap mode: "Shortage: 1,200 — Reskillable from adjacent: 890"

---

## 4. Extended CSV Export

New columns added to the downloadable CSV:

| Column | Source |
|--------|--------|
| `cluster` | Cluster assignment (if cluster filter active) |
| `year` | Year snapshot (if timeline active) |
| `phase_construction` | Construction demand for that year |
| `phase_commissioning` | Commissioning demand |
| `phase_operations` | Operations demand |
| `reskill_pathway_count` | Number of inbound reskilling pathways |
| `reskill_months_avg` | Average reskilling duration across pathways |
| `reskill_cost_avg` | Average reskilling cost across pathways |
| `reskillable_supply` | Estimated workers reskillable from adjacent occupations (blank if PLFS supply data absent for source occupations) |

When PLFS supply data is absent for a source occupation, `reskillable_supply` is left blank (empty string). Other pathway columns (`reskill_pathway_count`, `reskill_months_avg`, `reskill_cost_avg`) are always populated from `pathways.json` regardless of supply data availability.

This CSV is designed to complement h2hubs.in's downloadable reports — users can join on geography/sector to overlay workforce needs on infrastructure data.

---

## 5. Testing Strategy

### New Test Files

| Test File | Coverage | Est. Tests |
|-----------|----------|-----------|
| `test_clusters.py` | Cluster loading, affinity validation (sum to 1.0), demand distribution by cluster, state aggregation, missing cluster handling | ~15 |
| `test_timeline.py` | Annual snapshot generation, phase ramp-up curves, year interpolation, edge cases (start=target, short timelines), phase totals conservation | ~15 |
| `test_pathways.py` | Pathway loading, bidirectional lookup, skill overlap validation, cost/duration ranges, reskillable supply computation | ~12 |
| `test_parity.py` (extended) | Python/JS parity for cluster distribution + timeline computation | ~6 |

| `test_ui_logic.py` | dominantPhase() 6 cases, cluster suggestion logic 3 cases | ~9 |
| `test_timeline.py` (extended) | + cache invalidation on cluster/scenario change | +2 |
| `test_csv_export.py` (new or extended) | Full-snapshot row count validation | ~1 |

**Target: ~71 new tests (59 original + 12 from design review), bringing total from 96 to ~167.**

### Test Invariants

- Cluster affinity scores sum to 1.0 per archetype → demand is conserved (national total = sum of all clusters per occupation)
- **Timeline conservation:** For any single year snapshot, the sum of construction + commissioning + operations demand is a valid total. The **steady-state operations demand** (at `target_year` and beyond) equals the scenario's total operations demand from the demand engine. Construction and commissioning are temporary additional workforce that ramp up and taper to zero. The timeline does NOT conserve total demand across all years summed — it produces a time series of annual snapshots.
- Every archetype ID in `archetypes.json` must appear in every cluster's `archetype_affinity` map (missing = 0.0)
- Pathway source/target NCO codes must exist in occupations dataset
- Reskillable supply ≤ total supply of source occupations

---

## 6. Build Pipeline Changes

`build/build.py` extended:

1. Add `clusters.json` and `pathways.json` to the existing `MODEL_JSON_FILES` list (alongside `archetypes.json` and `scenarios.json`) so they are copied by the existing `sync_model_data()` loop
2. No separate one-off copy code — same pattern as existing model files
3. `model/timeline.py` functions called during build to pre-compute default scenario timelines
4. MoSPI cache refresh (optional, behind flag): fetch latest PLFS/ASI state-level data
5. New CSV export columns populated from clusters + timeline + pathways data

---

## 7. JS Engine Extension

`web/main.js.template` extended with:

- `distributeDemandByCluster(demandRecords, clusters)` — mirrors `distribute_demand_by_cluster()` in `clusters.py`
- `computeTimeline(scenario, occupations)` — mirrors `compute_timeline()` in `timeline.py`
- `getPathwaysForOccupation(ncoCode, direction)` — mirrors `get_pathways_for_occupation()` in `pathways.py`
- `computeReskillableSupply(occupation, gap, pathways)` — mirrors `compute_reskillable_supply()` in `pathways.py`

**Year keys in timeline output:** Both Python and JS use string keys ("2025", "2026") for year-keyed dicts/objects to ensure JSON serialization parity.
- Python/JS parity verified by extended `test_parity.py`

---

## 8. Implementation Order

1. **Clusters** (data + engine + tests) — foundation for geography
2. **Timeline** (data + engine + tests) — builds on scenario engine
3. **Pathways** (data + LLM scoring + engine + tests) — independent, can parallel with 1-2
4. **UI integration** (cluster dropdown, year slider, pathway panel) — after engines work
5. **MoSPI enrichment** (API calls + cache + display) — after UI scaffolding
6. **CSV export extension** — after all data flows work
7. **Python/JS parity tests** — after both engines stable

---

## 9. Non-Goals (Explicit)

- **No map visualization** — h2hubs.in covers this; we provide data they don't
- **No real-time MoSPI queries in browser** — cached at build time, refreshed periodically
- **No district-level granularity** — clusters and states are the resolution
- **No custom scenario builder for timelines** — use preset scenarios with start/target years
- **No NCVET/NQR qualification database integration** — pathways reference providers by name only

---

## 10. Relationship to h2hubs.in

| h2hubs.in Provides | We Provide |
|--------------------|------------|
| Project locations on map | Workforce demand per cluster |
| Production/demand analysis by sector | Occupation-level demand by archetype |
| Infrastructure layers (pipelines, storage) | Skills gaps and reskilling pathways |
| Downloadable project CSV | Downloadable workforce CSV (joinable by geography) |

Users download CSVs from both tools and join on state/cluster for the complete picture: infrastructure + workforce.

---

## 11. UI Information Architecture (Design Review)

### Page Layout with New Controls

```
┌─────────────────────────────────────────────────────────────┐
│ .atlas-nav                                                  │
│  HyGOAT  [Atlas] [Scenario] [Gap]              [⬇ Export]  │
├─────────────────────────────────────────────────────────────┤
│ .summary-bar                                                │
│   480 Occupations  │  12,400 Workers  │  Kutch  │  2028     │
│                                        (cluster)  (year)    │
├─────────────────────────────────────────────────────────────┤
│ .controls (pills: H2 Adjacency, Demand, Skill Transfer...) │
├─────────────────────────────────────────────────────────────┤
│ .scenario-bar (Scenario/Gap modes only)                     │
│  Row 1: Scenario [dropdown]  │  Cluster [dropdown]          │
│  Row 2: H₂ Target [===○=] 5.0 MT  │  Year [===○===] 2028   │
│  Row 3: [✓] Show unmapped  │  ■ Constr ■ Comm ■ Ops        │
├─────────────────────────────────────────────────────────────┤
│ .atlas-main (flex row)                                      │
│ ┌──────────────────────────┐ ┌────────────────────────────┐ │
│ │ .treemap-container       │ │ .sidebar (320px)           │ │
│ │                          │ │ ┌────────────────────────┐ │ │
│ │  [treemap SVG]           │ │ │ Electrolyser Ops Tech  │ │ │
│ │  cells colored by:       │ │ │ [NCO 3134] [Diploma]   │ │ │
│ │  - Atlas: score band     │ │ ├────────────────────────┤ │ │
│ │  - Scenario: demand band │ │ │ [Overview] [Pathways●3]│ │ │
│ │  - Year active: phase    │ │ ├────────────────────────┤ │ │
│ │                          │ │ │ (scrollable tab content)│ │ │
│ │                          │ │ │                        │ │ │
│ └──────────────────────────┘ │ └────────────────────────┘ │ │
│                              └────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ .legend (mode-specific color swatches)                      │
├─────────────────────────────────────────────────────────────┤
│ .atlas-footer                                               │
└─────────────────────────────────────────────────────────────┘
```

### Control Hierarchy

The scenario bar groups controls by semantic dimension:

| Row | Dimension | Controls | Rationale |
|-----|-----------|----------|-----------|
| 1 | **What** | Scenario preset dropdown, Cluster dropdown | Defines the scenario and geography filter |
| 2 | **How much / When** | MT slider (magnitude), Year slider (time) | Quantitative parameters |
| 3 | **Options** | Ghost toggle, Phase legend inline | Secondary controls |

- **Cluster dropdown** only appears in Scenario/Gap modes (same visibility as scenario bar)
- **Year slider** only appears when a scenario with `start_year` is selected
- When year slider is hidden, Row 2 shows only the MT slider (current behavior)

### Phase Colors (Timeline Mode)

When the year slider is active, treemap cells are colored by dominant phase:

| Phase | Color | Hex | Semantic |
|-------|-------|-----|----------|
| Construction | Blue | `#3b82f6` | Building — temporary workforce |
| Commissioning | Violet | `#8b5cf6` | Testing/transition — short peak |
| Operations | Teal | `#0d9488` | Sustained — long-term workforce |
| Mixed (no dominant) | Gray | `#6b7280` | No single phase > 50% of demand |

**"Dominant phase" rule:** A cell's color reflects whichever phase contributes > 50% of that occupation's demand for the selected year. If no phase exceeds 50%, the cell is gray (mixed). This avoids misleading single-color assignment for balanced demand.

Phase colors are intentionally distinct from existing color families (green=atlas, orange=scenario, red=gap) to signal "you are viewing a time snapshot" without confusion.

### Sidebar Tab Architecture

```
SIDEBAR (320px)
┌──────────────────────────────────┐
│ Occupation Title (h2)            │  ← Always visible
│ [Sector] [NCO code] [Education]  │  ← Metadata badges
├──────────────────────────────────┤
│ [Overview]    [Pathways ●3]      │  ← Tab bar
├──────────────────────────────────┤
│                                  │
│  OVERVIEW TAB:                   │  PATHWAYS TAB:
│  - Stats (employment, wage)      │  - Pathways IN heading
│  - Score bars (6 dimensions)     │  - Pathway cards (sorted
│  - Score rationale               │    by shortest duration)
│  - Scenario details (if active)  │  - Pathways OUT heading
│  - Gap details (if active)       │  - Pathway cards
│  - Top 5 Upskill Paths          │  - MoSPI stats (if avail)
│                                  │  - Reskillable supply
│  (scrolls independently)         │    summary (Gap mode)
│                                  │
└──────────────────────────────────┘
```

- **Tab bar** uses existing `.pill` button pattern: inactive = transparent border, active = filled
- **Pathway count badge** (`●3`): small circle with count, colored `var(--color-goat)` when pathways exist, `var(--gray-300)` when zero
- **Default tab:** Overview. Pathways tab auto-activates when user clicks a pathway-related link (e.g., from upskill paths)
- **No pathways:** Pathways tab shows count `●0` and is still clickable — tab content shows empty state (see Interaction States)

### Interaction States

Since all data is bundled JSON (no network requests in the browser), loading states are instant for most features. The key interaction states are **empty** and **partial**:

| Feature | Loading | Empty | Error | Success | Partial |
|---------|---------|-------|-------|---------|---------|
| **Cluster dropdown** | N/A (bundled data) | N/A (always has "All India" + 10 clusters) | N/A | Dropdown populated, selection filters treemap | N/A |
| **Year slider** | N/A (O(1) cache lookup per eng decision #11) | Hidden when scenario has no `start_year` | N/A | Treemap recolors by phase | 1-year span: slider shows single year, all phases overlap (eng decision #3). Label: "Short timeline — phases overlap" |
| **Treemap (cluster active)** | N/A | **Contextual empty state** (see below) | N/A | Cells sized by demand, colored by mode | Low-demand cluster: cells are very small. Tooltip: "Low affinity — most demand is in [top cluster]" |
| **Treemap (year active)** | N/A | Same as cluster empty | N/A | Cells colored by dominant phase (blue/violet/teal/gray) | Boundary year: most cells gray (mixed phases). Legend updates to show "Mixed — no dominant phase" |
| **Pathway panel IN** | N/A (bundled) | "No known reskilling pathways into this role. This may be a specialist occupation requiring formal education." + subtle illustration | N/A | Pathway cards sorted by highest skill overlap (Decision 7A) | Some pathways missing MoSPI data → individual cards show "Supply data unavailable" in muted text |
| **Pathway panel OUT** | N/A | "No mapped transition pathways from this role. Workers in this occupation may transition through general retraining programs." | N/A | Pathway cards sorted by highest skill overlap (Decision 7A) | Same MoSPI partial as IN |
| **Reskillable supply** | N/A | "Supply data unavailable for source occupations — cannot estimate reskillable pool." Muted text, no bar visualization. | N/A | "Shortage: 1,200 — Reskillable from adjacent: 890" with bar showing coverage | Some sources have data, some don't → show available count with caveat: "Based on N of M source occupations with PLFS data" |
| **MoSPI stats (sidebar)** | N/A | "State-level statistics not available for this occupation." Single muted line, not a full empty state block. | N/A | Supply count, avg wage, state distribution | Some indicators available → show what exists, omit missing (no gray placeholders) |
| **CSV full-snapshot** | Progress bar: "Generating full snapshot... [=====>    ] 2,400 / 4,800 rows" (eng decision #6) | N/A (always has data when button is visible) | Browser download blocked → "Download blocked by browser. Try right-click → Save As." | File downloads, button shows "✓ Downloaded" for 2s | N/A |

#### Cluster Empty State (Decision 2A)

When a cluster has zero demand for the current scenario:

```
┌──────────────────────────────────────────────┐
│                                              │
│    No workforce demand in {Cluster Name}     │
│    for the {Scenario Name} scenario.         │
│                                              │
│    {Cluster Name} specializes in             │
│    {top archetype type}. Try {suggested      │
│    cluster with highest affinity for          │
│    current scenario's dominant archetype}     │
│    for this workforce profile.               │
│                                              │
│    [View All India]                           │
│                                              │
└──────────────────────────────────────────────┘
```

- Centered in treemap container area
- Text color: `var(--text-muted)` (`#6b7280`)
- "View All India" is a text button in `var(--color-goat)` that resets the cluster dropdown
- Suggested cluster is computed: find the cluster with highest affinity for the current scenario's dominant archetype

### Responsive Behavior (≤768px)

Mobile layout for new controls (Decision 6A: collapse to row):

```
MOBILE (≤768px)
┌──────────────────────────────────┐
│ HyGOAT  [Atlas][Scen][Gap] [⬇]  │
├──────────────────────────────────┤
│  480 Occ  │  12,400 Workers      │
├──────────────────────────────────┤
│ [H2 Adj] [Demand] [Skill] ...   │
├──────────────────────────────────┤
│ 5MT Mix ▼   [====○=] 5.0 MT     │  ← Row 1: scenario + MT
│ Kutch ▼     [===○===] 2028      │  ← Row 2: cluster + year
│ ■ Constr ■ Comm ■ Ops           │  ← Row 3: phase legend
├──────────────────────────────────┤
│ ┌──────────────────────────────┐ │
│ │     TREEMAP (min-h: 350px)   │ │
│ │                              │ │
│ └──────────────────────────────┘ │
├──────────────────────────────────┤
│ ┌──────────────────────────────┐ │
│ │     SIDEBAR (max-h: 50vh)    │ │
│ │     [Overview] [Pathways●3]  │ │
│ │     (scrollable)             │ │
│ └──────────────────────────────┘ │
└──────────────────────────────────┘
```

Mobile-specific adjustments:
- **Cluster dropdown:** Abbreviated labels — "Kutch" not "Kutch Hydrogen Valley". Full name in tooltip on long-press.
- **Year slider:** Same width as MT slider. Label: just the year number ("2028"), no "Year:" prefix.
- **Summary bar:** Cluster and year info hidden on mobile to save space. Visible in scenario bar instead.
- **Pathway cards:** Full width, overlap bar stretches to container. Bridging skills always collapsed.
- **Sidebar tabs:** Tab bar stays sticky at top of sidebar section. Badge shrinks to 12px circle.

### Accessibility (Borrowing from HyGOAT Pilot UI_UX.md)

Following WCAG 2.2 AA standards established in the HyGOAT Pilot design system:

**Keyboard Navigation:**

| Control | Keys | Behavior |
|---------|------|----------|
| Cluster dropdown | `Enter`/`Space` to open, `↑↓` to navigate, `Enter` to select, `Esc` to close | Focus ring: `outline: 2px solid #3b82f6; outline-offset: 2px` |
| Year slider | `←→` arrow keys to step ±1 year, `Home`/`End` for min/max | Uses native `<input type="range">` keyboard behavior |
| Sidebar tabs | `Tab` to reach tab bar, `←→` to switch tabs | `role="tablist"`, `role="tab"`, `role="tabpanel"` with `aria-selected` |
| Pathway card expand | `Enter`/`Space` to toggle bridging skills | `aria-expanded="true/false"` on the expand trigger |
| Treemap cells | Existing click behavior + `Enter` on focused cell | Tab order follows treemap rendering order (largest cells first) |

**ARIA Live Regions:**

| Dynamic Content | ARIA Pattern | Rationale |
|----------------|-------------|-----------|
| Summary bar (cluster change) | `aria-live="polite"`, immediate | Announces new cluster context on dropdown selection |
| Summary bar (year change) | `aria-live="polite"`, debounced — announce on slider `change` event (mouseup/touchend), NOT on `input` event | Prevents rapid-fire announcements during drag (eng review decision #12) |
| Treemap recolor (phase change) | No `aria-live` on treemap | Do NOT announce individual cell color changes — too noisy. Summary bar announcement is sufficient. |
| Pathway panel content | `aria-live="polite"` on tab panel | Announces when pathways load for selected occupation |
| CSV export progress | `aria-live="assertive"` + `role="progressbar"` | Export progress is time-sensitive feedback |

**Touch Targets:**
- Cluster dropdown trigger: min 44px height (matches existing scenario dropdown)
- Year slider thumb: browser default (typically 44px on mobile Safari/Chrome)
- Sidebar tab buttons: min 44px height, full available width
- Pathway card expand trigger: 44px hit area (even if visual element is smaller)

**Color Contrast:**
- Phase colors on treemap: white text labels on blue/violet/teal all meet 4.5:1 at the specified hex values
- Overlap bar: percentage text positioned outside the bar (not inside) to avoid contrast issues on partially-filled bars
- Empty state text: `var(--text-muted)` (#6b7280) on white background = 4.6:1 (passes AA)

### Design System: New Tokens & Components

Phase 3 introduces these new CSS custom properties (extend existing `style.css`):

```css
/* Phase colors — timeline mode only */
--phase-construction: #3b82f6;   /* blue-500 */
--phase-commissioning: #8b5cf6;  /* violet-500 */
--phase-operations: #0d9488;     /* teal-600 */
--phase-mixed: #6b7280;          /* gray-500, reuses existing --text-muted */

/* Pathway overlap bar colors */
--overlap-high: #0d9488;    /* teal-600, ≥70% overlap */
--overlap-medium: #f59e0b;  /* amber-500, 40-69% */
--overlap-low: #ef4444;     /* red-500, <40% */
```

New component classes (extend existing vocabulary):

| Component | Class | Pattern Source | Notes |
|-----------|-------|---------------|-------|
| Sidebar tab bar | `.sidebar-tabs` | New (flexbox, gap: 2px) | Contains `.pill` buttons, same border-radius: 999px |
| Active tab | `.pill.active` | Existing `.pill.active` | Background: `var(--color-goat)`, white text |
| Tab badge | `.tab-badge` | New (inline-flex, 16px circle) | Orange when count > 0, gray when 0 |
| Pathway card | `.pathway-card` | Adapted from `.upskill-item` | Same separator, adds overlap bar |
| Overlap bar track | `.overlap-track` | Adapted from `.score-bar-track` | Same 8px height, gray-100 background |
| Overlap bar fill | `.overlap-fill` | Adapted from `.score-bar-fill` | Color varies by range (high/medium/low) |
| Phase legend (inline) | `.phase-legend` | New (flex, gap: 12px) | Sits in scenario bar Row 3 |
| Cluster dropdown | `.cluster-select` | Adapted from `.scenario-select` | Same styling as scenario preset dropdown |
| Year slider | `.year-slider` | Reuses `.mt-slider` | Same accent-color, height, max-width |
| Empty state (treemap) | `.treemap-empty` | New (centered, muted text) | For zero-demand cluster states |

No new fonts, no new spacing scale, no new border-radius values. All new components derive from existing patterns.

### User Journey & Discovery

**New control onboarding:** Phase 3 adds controls that change the treemap's meaning. Users need contextual cues — not a tutorial, but enough to understand what changed.

| New Control | Discovery Cue | First Interaction Help |
|-------------|---------------|----------------------|
| Cluster dropdown | Default label: "All India (National)" signals geography is available | First selection: summary bar animates to show cluster name, treemap transitions with 300ms fade |
| Year slider | Appears with label: "Timeline: {start_year} → {target_year}" | First drag: inline legend auto-expands showing phase color key (blue=construction, violet=commissioning, teal=operations). Legend collapses after 5s or user interaction |
| Pathways tab | Badge shows pathway count (`●3`) in orange when pathways exist | First tab click: no special treatment needed — the content is self-explanatory |

**Phase color transition:** When the user first activates the year slider, the treemap color scheme changes from demand bands (green→orange→red) to phase colors (blue/violet/teal/gray). This is a jarring transition. Mitigation:
- The scenario bar Row 3 shows an inline phase legend: `■ Construction  ■ Commissioning  ■ Operations` — always visible when year slider is active
- The main legend below the treemap also updates to show phase colors
- Tooltip includes phase name: "Construction: 80 workers (65%)" alongside the occupation name

**Cluster → Year flow:** The natural exploration path is: select scenario → narrow by geography → explore over time. This matches the control layout (Row 1: what/where, Row 2: how much/when) and the computation pipeline (demand → clusters → timeline per eng decision #1).

### Summary Bar Layout

The summary bar adds cluster and year context when active:

| Metric | Visibility | Example |
|--------|-----------|---------|
| Occupation count | Always | "480 Occupations" |
| Total demand | Scenario/Gap modes | "12,400 Workers" |
| Cluster name | When cluster filter ≠ "All India" | "Kutch Valley" |
| Year + phase breakdown | When year slider active | "2028: 3,200 constr / 800 comm / 2,100 ops" |

When both cluster and year are active, the summary reads naturally left-to-right: "Kutch 2028: 1,200 construction / 300 commissioning / 600 operations"

---

## 12. Engineering Review Decisions (2026-03-30)

Resolved during `/plan-eng-review`. These override the corresponding spec sections above.

| # | Decision | Detail |
|---|---|---|
| 1 | **Cluster-first ordering** | Timeline runs AFTER cluster distribution. Pipeline: demand → clusters → timeline |
| 2 | **Round-last reconciliation** | Cluster engine uses floats internally, applies largest-remainder rounding at output. Guarantees: Σ clusters == national total |
| 3 | **Clamp phases to span** | When `target_year - start_year < 3`, phase boundaries clamp to `max(start_year, computed_boundary)`. For 1-year span: all phases overlap |
| 4 | **Reskillable supply overlap accepted** | Per-target reskillable counts may overlap across targets. UI shows caveat: "not additive across target occupations" |
| 5 | **Pathway quality gates** | Add `confidence` field (high/medium/low), bounds validation (months 1-36, cost 10k-500k, overlap 0-1), 50-pathway spot-check sample |
| 6 | **Two CSV exports** | View-export (current treemap state) + full-snapshot button (occupation×cluster×year cross-product with progress indicator) |
| 7 | **Timeline accepts demand records** | `compute_timeline(cluster_demand, start_year, target_year)` — NOT `compute_timeline(scenario, occupations, clusters=None)` |
| 8 | **Archetype-level construction_years** | New field in archetypes.json (e.g., alkaline: 3, ammonia: 5, RE: 2). Timeline uses per-archetype phase boundaries |
| 9 | **71 tests target** | Original 59 + 12 from design review: 6 dominantPhase, 3 cluster suggestion, 2 cache invalidation, 1 CSV row count |
| 10 | **O(n²) recolourTreemap fix** | Bundled with Phase 3: pre-build `Map<id, occupation>` lookup. Removed from TODOS.md |
| 11 | **Pre-compute timeline cache** | Timeline computed once per scenario OR cluster change, stored as `timelineCache[year]`. Year slider indexes into cache (O(1)). Cache invalidated on: scenario preset change, MT slider change, cluster dropdown change. |

### Eng Review Run 2 Decisions (post-design-review)

| # | Decision | Detail |
|---|---|---|
| 12 | **Debounced aria-live** | Summary bar `aria-live="polite"`: immediate for cluster dropdown, `change` event only (mouseup/touchend) for year slider. Prevents rapid-fire screen reader announcements during slider drag. |
| 13 | **Chunked CSV export** | Full-snapshot CSV generated in async chunks of 1000 rows via `setTimeout(0)` yielding. Progress bar updates between chunks. No Web Worker needed. |

### Spec Corrections

- **Remove `lat`/`lng` from clusters.json schema** — YAGNI (no map visualization)
- **Add `source_type` field to pathway schema** — reuse `"modeled_estimate"` / `"literature"` pattern from coefficients
- **Add `confidence` field to pathway schema** — `"high"` / `"medium"` / `"low"`
- **Rename `year` → `target_year` in scenarios.json** — no alias, just rename (pre-1.0, no external consumers)
- **"By State" UI label → "By State (cluster-based)"** — honest about resolution
- **Build-time validation:** assert every archetype in archetypes.json has affinity entries in all clusters summing to 1.0

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 1 | CLEAR | 10 findings, 8 incorporated |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 2 | CLEAR | Run 1: 18 issues, 0 critical gaps. Run 2: 5 issues, 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | CLEAR (FULL) | score: 3/10 → 9/10, 7 decisions |

- **CODEX:** GPT-5.4 found 10 issues — timeline ordering, rounding drift, short-timeline math, geography honesty, reskillable supply double-counting, pathway quality, CSV grain, MoSPI brittleness, scope overload. 8/10 incorporated into eng review decisions.
- **CROSS-MODEL:** Claude and Codex agreed on 5 issues (timeline ordering, rounding, short timelines, reskillable supply, CSV grain). Codex uniquely flagged "phase is overstuffed" — noted but not actioned since features are independently testable.
- **DESIGN:** Added 7 design specs: page layout/info architecture, interaction states for 8 features, user journey/discovery cues, pathway card visual hierarchy (overlap-first), 8 new CSS tokens + 10 component classes, responsive mobile layout, WCAG 2.2 AA keyboard/ARIA/touch specs. Created DESIGN.md. Borrowed a11y patterns from HyGOAT Pilot UI_UX.md.
- **ENG RUN 2:** Post-design-review validation. 5 issues: timeline cache invalidation on cluster change (fixed), aria-live debouncing for slider (fixed), chunked CSV export (fixed), selectOccupation() refactoring (planned), dominantPhase() extraction (planned). Test target increased 59 → 71 (+12 design-spec tests). 2 plan contradictions fixed.
- **UNRESOLVED:** 0
- **VERDICT:** ENG (x2) + DESIGN CLEARED — ready to implement
