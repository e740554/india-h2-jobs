# Phase 2 Design Spec: Supply Gap Engine (v1.3.0.0)

**Branch:** `phase2/supply-gap-engine`
**Date:** 2026-03-30
**Status:** Draft (Rev 2 — spec review fixes applied)

## Goal

Transform the atlas from a demand-only scenario engine into a supply-gap analyser. A policymaker sets an MT target and asset mix, and sees which occupations face shortage vs. surplus — answering "Where will we struggle to hire at 5 MT?"

## Three Pillars

### Pillar 1: PLFS Labour Supply Baseline

**Problem:** All 480 H2-relevant occupations have `supply_estimate = None`. The `workforce_gap` metric is blocked.

**Data source:** PLFS 2023-24 Annual Report PDF (Option A from DATASOURCES.md). The MoSPI eSankhyiki API was tested and only provides 1-digit NCO division-level data (10 categories); we need 2-digit NCO subdivision granularity from Statement 16/17 of the PDF.

**Pipeline:**

```
PLFS 2023-24 PDF (Statement 16/17)
  → tabula-py parse NCO subdivision % distribution
  → multiply by total workforce estimate (WPR × working-age population)
  → join to occupations by nco_code[:2]
  → allocate within subdivision by (h2_adjacency + transition_demand) weight
  → populate supply_estimate field per occupation
```

**Output fields added to each occupation:**
- `supply_estimate` (int) — estimated current workforce headcount
- `supply_source` (str) — "PLFS 2023-24"
- `supply_nco_subdivision` (str) — 2-digit NCO subdivision used for allocation

**Script:** `scrape/parse_plfs.py`
- Input: PLFS Annual Report PDF (downloaded to `scrape/raw/plfs/`)
- Output: `plfs_supply.json` — `{nco_subdivision: {pct: float, headcount: int}}`
- The build pipeline (`build/build.py`) joins this to occupations during the merge step

**Limitation:** 2-digit NCO gives ~40 subdivisions, not 4-digit. Within each subdivision, headcount is allocated using the same weighted approach as the scenario engine (h2_adjacency + transition_demand). This is a modeled estimate, not measured per-occupation employment. Caveats must appear in the UI and data exports.

**PLFS parsing detail:**
- **PDF:** `AnnualReport_PLFS2023-24L2.pdf` from mospi.gov.in
- **Statement 16:** "Percentage distribution of usually employed (PS+SS) by NCO 2-digit subdivision" — Table appears around pages 120-130 (varies by edition)
- **Table structure:** Rows = NCO subdivision (2-digit code + title), Columns = Rural Male / Rural Female / Urban Male / Urban Female / Rural Total / Urban Total / All
- **Fallback:** If tabula-py fails on this PDF (scanned/typeset quality issues), create `plfs_supply_manual.json` with hand-transcribed values from the PDF and source provenance. The build pipeline consumes the JSON regardless of how it was produced.
- **PDF not checked into repo** — downloaded to `scrape/raw/plfs/` (gitignored). The parsed JSON output (`plfs_supply.json`) IS checked in as the reproducible artifact.

**Validation:** A test must verify that the sum of per-occupation supply estimates within each 2-digit subdivision equals the PLFS subdivision total (conservation check). Cross-check against any available external benchmarks (e.g., NSSO employment in chemical/electrical occupations).

### Pillar 2: Three New Archetypes

India's NGHM target is ~70% ammonia by volume. The value chain requires three asset types beyond the existing alkaline electrolyser.

**Unit convention:** All archetypes use MW for capacity (not GW). The scenario engine converts to GW internally where needed (`capacity_mw / 1000`). This maintains consistency with the existing `alkaline_1gw` schema.

**Archetype type discriminator:** Each archetype gets an `archetype_type` field:
- `"production"` — produces H2 (has `h2_output_mt_per_year`)
- `"downstream"` — consumes H2 (has `h2_input_mt_per_unit`)
- `"upstream"` — provides energy input (has `energy_output_twh_per_year`)

The engine uses `archetype_type` to select the correct unit-derivation formula.

**Existing archetype update — `alkaline_1gw`:**
Add `"archetype_type": "production"` to the existing archetype. All other fields unchanged.

#### Archetype 2: `pem_500mw` — PEM Electrolyser (500 MW)

**JSON schema:**
```json
{
  "id": "pem_500mw",
  "archetype_type": "production",
  "name": "500 MW PEM Electrolyser Plant",
  "capacity_mw": 500,
  "h2_output_mt_per_year": 0.075,
  "description": "...",
  "caveats": "...",
  "coefficients": [...]
}
```

- **Scale:** 500 MW PEM electrolyser
- **H2 output:** 0.075 MT/year (45 kWh/kg, 80% CF)
- **Rationale:** PEM is 20-30% of India's planned electrolyser capacity. 500 MW reflects actual Indian project scales (Ohmium/NTPC-type). Different workforce profile: more electronics/precision, less heavy welding.
- **Coefficient sources:** IRENA 2023 "Green Hydrogen for Industry", CEEW 2023 workforce analysis, scaled with India labor intensity multiplier (1.3-1.5x global)

**Workforce profile (vs. alkaline):**
- Fewer welders/pipe fitters (smaller footprint, less high-pressure pipework)
- More electrical/electronic assemblers (stack assembly is electronics-intensive)
- Specialized membrane technicians (PEM maintenance)
- Shorter construction timeline (12-18 months vs 18-24 for alkaline)
- Construction: ~1,500-2,000 peak workers
- Operations: ~120-180 permanent

**Estimated coefficients by phase:**

| Phase | Total | Key NCO groups |
|-------|-------|----------------|
| Construction | ~1,800 | 8212 (E&E assemblers) high, 7212 (welders) lower than alkaline, 7413 (electrical) high |
| Commissioning | ~250 | 3113 (elec. tech), 2145 (chem. eng), 3135 (process controllers) |
| Operations | ~150 | 3113 (elec. tech) high share, 8131 (chemical ops), 3134 (plant ops) |

#### Archetype 3: `ammonia_1mtpa` — Green Ammonia Synthesis (1 MTPA)

**JSON schema:**
```json
{
  "id": "ammonia_1mtpa",
  "archetype_type": "downstream",
  "name": "1 MTPA Green Ammonia Synthesis Plant",
  "capacity_mw": null,
  "h2_input_mt_per_unit": 0.18,
  "nh3_output_mtpa": 1.0,
  "description": "...",
  "caveats": "...",
  "coefficients": [...]
}
```

- **Scale:** 1.0 million tonnes per annum NH3 (Haber-Bosch + ASU + H2 compression + cryogenic storage)
- **H2 input:** Consumes ~0.18 MT H2/year as feedstock
- **Rationale:** This is WHERE India's green H2 goes. Adani Kutch, ACME Bikaner, Greenko — all center on ammonia. Domestic fertilizer replacement + export to EU/Japan/Korea.
- **Does NOT include** the electrolyser or RE — those are separate archetypes. This is the downstream synthesis plant only.
- **Coefficient sources:** TERI 2023, conventional Indian ammonia plant benchmarks (IFFCO, NFL, RCF), IRENA modeled estimates

**Workforce profile:**
- High share of chemical process operators (NCO 8131) — this is a chemical plant
- Cryogenic technicians (ammonia storage at -33 C)
- High-pressure equipment specialists (150-300 bar operating pressure)
- Air separation unit operators
- More lab/analytical chemists than electrolyser plants
- Catalyst handling specialists (unique to ammonia synthesis)

**Estimated coefficients by phase:**

| Phase | Total | Key NCO groups |
|-------|-------|----------------|
| Construction (24 months) | ~4,000 | 7212 (welders, pressure vessel), 7126 (HP pipe fitters), 7214 (structural), 8211 (heavy rigging) |
| Commissioning (4-6 months) | ~400 | 2145 (chem. eng, catalyst loading), 3134 (plant ops), 3116 (lab setup) |
| Operations (permanent) | ~300 | 8131 (chemical ops, largest group), 3134 (shift operators), 7233 (maintenance), 3116 (lab/QC) |

#### Archetype 4: `solar_wind_hybrid_2gw` — Dedicated RE Farm (2 GW)

**JSON schema:**
```json
{
  "id": "solar_wind_hybrid_2gw",
  "archetype_type": "upstream",
  "name": "2 GW Hybrid Solar+Wind Farm (Dedicated RE)",
  "capacity_mw": 2200,
  "energy_output_twh_per_year": 4.5,
  "description": "...",
  "caveats": "...",
  "coefficients": [...]
}
```

- **Scale:** ~1.5 GW solar PV + ~0.7 GW onshore wind (serves one 1 GW electrolyser)
- **Output:** ~4-5 TWh/year electricity (blended ~25% CF)
- **Rationale:** MNRE's Green Hydrogen Standard requires RE "additionality" — new capacity, not grid power. Every large Indian H2 project bundles dedicated RE. This is the LARGEST headcount driver during construction.
- **Coefficient sources:** IRENA 2024 "RE and Jobs: Annual Review", CEEW/NRDC India-specific coefficients

**Workforce profile:**
- Very high share of semi-skilled labor during construction (panel mounting, trenching, cable laying)
- Wind O&M requires specialized technicians (blade repair, high-altitude work)
- Solar O&M is lower-skill but labor-intensive (panel cleaning in dusty Rajasthan/Gujarat)
- HV substation, inverter, transformer operations

**Estimated coefficients by phase:**

| Phase | Total | Key NCO groups |
|-------|-------|----------------|
| Construction (12-18 months) | ~8,000 | 7413 (electrical line installers), 7126 (cable layers), 9312 (civil labourers), 7214 (structural, wind towers), 8343 (crane operators) |
| Operations (permanent) | ~700 | 7413 (electrical maintenance), 7233 (wind turbine mechanics), 9312 (panel cleaning crews), 3113 (SCADA/monitoring) |

### Pillar 3: Supply Gap Engine

**Computation:**
```
gap[occupation] = supply[occupation] (from PLFS) - demand[occupation] (from scenario engine)
```
- Positive gap = surplus talent available
- Negative gap = shortage, reskilling/recruitment pressure

**Model extensions in `model/compute.py`:**

```python
def compute_demand_for_units(units: float, archetype: dict, occupations: list) -> list:
    """Low-level demand computation for a pre-computed number of units.

    Refactored from compute_demand() to decouple unit derivation from
    demand distribution. compute_demand() remains as the public API for
    single-archetype scenarios (calls this internally).

    Args:
        units: Number of plant units (pre-computed by caller)
        archetype: Archetype dict with coefficients
        occupations: List of occupation dicts with scores

    Returns: List of demand records (same schema as compute_demand output,
             plus 'archetype_id' field)
    """

def compute_multi_archetype_demand(
    scenario: dict, archetypes: list, occupations: list
) -> list:
    """Compute demand across a multi-archetype scenario.

    Detects scenario format (single vs. multi-archetype) and dispatches
    accordingly. For multi-archetype:
      1. Production: units = (target_mt * share) / archetype.h2_output_mt_per_year
      2. Downstream: units = (target_mt * conversion_share) / archetype.h2_input_mt_per_unit
      3. Upstream: units = (sum_production_capacity_mw / 1000 * re_ratio) / (archetype.capacity_mw / 1000)

    Args:
        scenario: Scenario dict (single-archetype or multi-archetype format)
        archetypes: List of all archetype dicts
        occupations: List of occupation dicts with scores

    Returns: List of demand records with 'archetype_id' field, merged across
             all archetypes. Records are NOT aggregated — caller uses
             aggregate_demand() for summaries.
    """

def compute_gap(demand_by_occupation: dict, supply_data: dict) -> list:
    """Compute supply-demand gap per occupation.

    Sign convention: gap = supply - demand
      Positive = surplus (more workers available than needed)
      Negative = shortage (more workers needed than available)

    This REPLACES the existing compute_workforce_gap() in build.py, which
    used the opposite convention. build.py will be updated to use this function.

    Args:
        demand_by_occupation: dict {occupation_id: int} from aggregate_demand()
        supply_data: dict {occupation_id: int} from PLFS supply estimates

    Returns: List of dicts:
        {occupation_id, supply, demand, gap, gap_pct, gap_status}
        - gap_pct = (supply - demand) / demand * 100 when demand > 0, else None
          (reads as: "we can fill X% of demand from existing workforce")
        - gap_status = "surplus" | "shortage" | "balanced" | "no_data"
        - When supply is None for an occupation: gap=None, gap_status="no_data"
          (frontend shows "Supply data unavailable", not a misleading red tile)
    """
```

**Deprecation:** `compute_workforce_gap()` in `build/build.py` is deprecated and replaced by `compute_gap()` in `model/compute.py`. The old function used the opposite sign convention (positive = shortage). All callers will be updated to the new convention.

**JS parity:** `computeMultiArchetypeDemand()` and `computeSupplyGap()` in `web/main.js.template` must match Python exactly.

**Frontend:**
- New **Gap** mode toggle: Atlas | Scenario | Gap
- Gap mode shows treemap tiles colored red (shortage) to green (surplus)
- Intensity proportional to gap magnitude
- Summary bar: "Occupations in Shortage: N" | "Total Workforce Gap: +/-X" | "Largest Shortage: [occupation name]"
- Sidebar detail: per-occupation supply vs. demand breakdown

## Multi-Archetype Scenario Model

### Schema extension for `scenarios.json`

Current format (single archetype):
```json
{"id": "nghm_5mt_2030", "target_mt": 5, "archetype_id": "alkaline_1gw"}
```

New format (composable):
```json
{
  "id": "nghm_5mt_2030_integrated",
  "name": "NGHM 5 MT by 2030 (Integrated)",
  "target_mt": 5,
  "year": 2030,
  "description": "5 MT target with 60/40 alkaline/PEM split, 70% to ammonia, dedicated RE",
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

**Backwards compatibility:** Old single-archetype format (`archetype_id` at top level) continues to work. The engine detects the format and falls back to single-archetype computation.

### Computation chain for multi-archetype scenarios

```
1. Split target_mt across production archetypes by share
2. For each production archetype:
   a. mt_share = target_mt * share
   b. units = mt_share / archetype.h2_output_mt_per_year
   c. compute_demand_for_units(units, archetype, occupations) → demand records
3. For each downstream archetype (ammonia):
   a. h2_consumed = target_mt * conversion_share
   b. units = h2_consumed / archetype.h2_input_mt_per_unit
   c. compute_demand_for_units(units, archetype, occupations) → demand records
4. For each upstream archetype (RE):
   a. total_electrolyser_mw = sum of production archetype (capacity_mw * units) from step 2
   b. re_mw = (total_electrolyser_mw / 1000) * re_ratio_gw_per_gw_electrolyser * 1000
      (convert to GW for ratio, back to MW for units)
   c. units = re_mw / re_archetype.capacity_mw
   d. compute_demand_for_units(units, archetype, occupations) → demand records
5. Merge all demand records across archetypes (each record has archetype_id)
6. Aggregate by occupation (sum demand from all sources)
```

All capacity values stay in MW throughout. The `re_ratio_gw_per_gw_electrolyser` field uses GW only because "2.5 GW RE per 1 GW electrolyser" is the standard industry phrasing; the engine converts internally.

### Preset scenarios for v1.3

| ID | Name | Target | Production Mix | Downstream | Upstream |
|----|------|--------|---------------|------------|----------|
| `nghm_1mt_2027_alk` | 1 MT Pilot (Alkaline) | 1 MT | 100% alkaline | 50% ammonia | 2.5x RE |
| `nghm_5mt_2030_mix` | 5 MT by 2030 (Mixed) | 5 MT | 60% alkaline + 40% PEM | 70% ammonia | 2.5x RE |
| `nghm_10mt_2035_mix` | 10 MT Ambitious (Mixed) | 10 MT | 50% alkaline + 50% PEM | 70% ammonia | 3.0x RE |
| `adani_kutch_ph1` | Adani Kutch Phase 1 | 1.3 MT | 100% alkaline | 100% ammonia | 2.5x RE |

**Note on Adani Kutch preset:** The target is 1.3 MT H2/year (matching ~9 GW electrolyser to feed a 1 MTPA ammonia plant, which consumes 0.18 MT H2/unit). The scenario engine does NOT enforce H2 balance constraints — demand is computed independently per archetype. The preset is illustrative of the project's announced scale, not a mass-balance simulation.

The existing 3 single-archetype scenarios remain for backwards compatibility.

## JS Engine Changes

The current JS engine (`web/main.js.template`) is hardcoded to single-archetype computation:
- `archetypeData[0]` is the only archetype loaded
- `scenarios.json` is not loaded at all
- `computeScenarioDemand()` takes `(targetMT, archetype, occupations)` directly

**Phase 2 changes required:**

1. **Load `scenarios.json`** alongside `archetypes.json` during init:
   ```js
   const scenarioData = await fetch('scenarios.json').then(r => r.json());
   ```

2. **Preserve `computeScenarioDemand()`** for backwards compat — it continues to work for single-archetype scenarios

3. **Add `computeMultiArchetypeDemand(scenario, archetypes, occupations)`** — same logic as Python `compute_multi_archetype_demand()`, dispatching by `archetype_type`

4. **Add `computeSupplyGap(demandByOccupation, supplyData)`** — same logic as Python `compute_gap()`

5. **Scenario selection flow:**
   - Preset dropdown populates from `scenarioData`
   - Selecting a preset calls `computeMultiArchetypeDemand(selectedScenario, archetypeData, occupations)`
   - Manual slider adjustments create an ephemeral scenario object (clone the preset, modify the changed field)
   - MT slider changes `target_mt`, split slider changes `production[].share`, etc.

6. **Gap mode activation:**
   - Requires `supplyData` to be loaded (from `plfs_supply.json` baked into `occupations.json`)
   - Gap toggle disabled with tooltip "Supply data not yet available" if supply fields are missing

## Frontend Changes

### Archetype picker (Scenario mode)

Replace the single archetype concept with a **preset scenario dropdown** that sets the full mix. Advanced users can manually adjust:
- MT target slider (existing, range extended)
- Production split slider (alkaline % vs PEM %)
- Ammonia conversion % slider
- RE ratio slider

### Gap mode

Third toggle position after Atlas and Scenario:
- Tiles: red (shortage) → white (balanced) → green (surplus)
- Legend: continuous gradient with headcount labels
- Summary bar: shortage count, total gap, largest shortage occupation
- Sidebar: per-occupation detail with supply source, demand breakdown by archetype, gap

### Sidebar enhancements

In Scenario and Gap modes, sidebar shows:
- Demand breakdown by archetype (e.g., "320 from alkaline construction + 45 from ammonia ops")
- Phase breakdown (construction / commissioning / operations)
- Supply source and confidence note (when in Gap mode)

## Files to Create/Modify

### New files
| File | Purpose |
|------|---------|
| `scrape/parse_plfs.py` | Parse PLFS PDF Statement 16/17 → `plfs_supply.json` |
| `model/supply.py` | Supply data loading and subdivision-to-occupation allocation |
| `tests/test_supply.py` | Tests for PLFS parsing, subdivision allocation, conservation checks |
| `tests/test_gap.py` | Tests for gap computation: positive/negative/zero/None gaps, aggregation |
| `tests/test_multi_archetype.py` | Tests for multi-archetype scenario computation, backwards compat |
| `tests/test_parity_v2.py` | Python/JS parity tests for new engine features |

### Modified files
| File | Change |
|------|--------|
| `model/archetypes.json` | Add `archetype_type` to existing; add `pem_500mw`, `ammonia_1mtpa`, `solar_wind_hybrid_2gw` |
| `model/scenarios.json` | Add multi-archetype scenarios + `adani_kutch_ph1` |
| `model/compute.py` | `compute_demand_for_units()`, `compute_multi_archetype_demand()`, `compute_gap()` |
| `web/main.js.template` | Load `scenarios.json`; `computeMultiArchetypeDemand()`, `computeSupplyGap()`, Gap mode UI |
| `web/style.css` | Gap mode colors, new legends, slider styles |
| `web/index.html` | Gap toggle button (3-way: Atlas/Scenario/Gap), archetype picker UI, new sidebar sections |
| `build/build.py` | Deprecate `compute_workforce_gap()`, merge PLFS supply into occupations, copy `plfs_supply.json` to output |
| `tests/test_compute.py` | Update `test_load_scenarios_contain_required_fields` to handle both single and multi-archetype formats |
| `README.md` | Update roadmap, architecture diagram, data source status |
| `CLAUDE.md` | Document new commands, files, testing expectations |

### Build pipeline changes

The PLFS supply merge happens **after** score merging, **before** summary metric computation:

```
1. Load occupations.csv + scores.json → merged occupation list  (existing)
2. Load plfs_supply.json → join supply_estimate by nco_code[:2]  (NEW)
3. Compute summary metrics (workforce_gap now uses compute_gap)  (UPDATED)
4. Write occupations.json, occupations-all.json                  (existing)
5. Copy model/*.json + plfs_supply.json to docs/ and web/        (UPDATED)
6. Template main.js from main.js.template                        (existing)
```

Supply fields (`supply_estimate`, `supply_source`, `supply_nco_subdivision`) are baked into `occupations.json` and `occupations-all.json`. The frontend reads supply data from occupation records directly — no separate JSON load needed for gap mode.

## Data Quality and Caveats

### PLFS supply estimates
- Based on 2-digit NCO subdivision allocation (modeled, not measured per-occupation)
- India total workforce from WPR applied to Census population estimates
- Supply numbers are point-in-time (2023-24) and do not project growth/decline
- Must display caveat in UI: "Supply estimates are modeled from PLFS 2023-24 subdivision data"

### Archetype coefficients
- Ammonia coefficients derived from conventional Indian plant benchmarks — no published green ammonia plant staffing data exists
- India labor intensity multiplier (1.3-1.5x IRENA global) from CEEW 2023
- PEM coefficients are directional — no per-occupation published data for PEM specifically
- RE coefficients are the highest-confidence numbers (IRENA/CEEW India-specific, multi-year data)

### Gap computation
- gap = supply - demand is a simplification (assumes all workers in an occupation are available for H2 work)
- Does not model geographic concentration, wage competition, or training pipeline
- Phase 3 will add geography and reskilling cost layers

## Testing Requirements

Per CLAUDE.md: 100% coverage is the goal.

- `test_supply.py`: PLFS parsing, subdivision allocation, conservation check (per-occ sums = subdivision total), edge cases (empty data, missing subdivisions, malformed PDF output)
- `test_gap.py`: gap computation — positive gap (surplus), negative gap (shortage), zero gap, `supply_estimate=None` returns `gap=None` and `gap_status="no_data"`, aggregation, `gap_pct` denominator correctness
- `test_multi_archetype.py`: single-archetype fallback, multi-archetype composition, backwards compatibility with old scenario format, edge cases (0% share, missing archetype_id, downstream without matching production)
- `test_parity_v2.py`: Python/JS parity for `computeMultiArchetypeDemand()` and `computeSupplyGap()` across multiple scenario types
- Update `test_compute.py`: existing 29 tests must continue to pass; update `test_load_scenarios_contain_required_fields` to accept both `archetype_id` (single) and `production` (multi) formats

## Success Criteria

1. All 480 H2-relevant occupations have `supply_estimate` values from PLFS
2. Scenario engine supports 4 archetypes across the full H2 value chain
3. Multi-archetype scenarios compose correctly (electrolyser + ammonia + RE)
4. Gap mode shows red/green treemap with shortage/surplus per occupation
5. All existing tests pass + new tests for every new function
6. Python/JS parity holds for multi-archetype and gap computations
7. Existing single-archetype scenarios continue to work unchanged
