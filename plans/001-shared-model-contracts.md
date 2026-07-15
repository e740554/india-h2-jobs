# Plan 001: Characterize shared model contracts before changing outcomes

> **Executor instructions**: Run the drift check first. Add failing tests before
> production changes. Do not change numerical behavior in this plan.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: tests
- **Planned at**: commit `273a4c1`, 2026-07-15

## Why this matters

The Python validation/export engine and browser runtime deliberately duplicate
demand, geography, timeline, gap, and reskilling logic. Existing parity checks
only cover two simple demand targets and one mixed scenario. Conservation fixes
must be characterized in both runtimes first so a green suite cannot conceal a
shared regression.

## Current state

- `model/compute.py` owns demand records and gap helpers.
- `model/timeline.py` creates Python annual snapshots.
- `web/main.js.template` contains the browser runtime and DOM controller.
- `tests/parity_check.js` loads the browser runtime under Node.
- `tests/test_parity.py` currently compares only demand, cluster, and timeline.

~~~python
# model/compute.py:113-120
occ_demand = raw_demand * norm_weight
records.append({"demand": round(occ_demand),
                "allocation_weight": round(norm_weight, 6)})
~~~

## Commands

| Purpose | Command | Expected result |
|---|---|---|
| Drift check | `git diff --stat 273a4c1..HEAD -- model tests web/main.js.template` | Review any in-scope drift before editing |
| Focused tests | `python -m pytest tests/test_parity.py tests/test_compute.py tests/test_timeline.py tests/test_pathways.py tests/test_gap.py` | All pass |
| Full suite | `python -m pytest` | All pass |

## Scope

In scope: `tests/test_parity.py`, `tests/parity_check.js`, and new focused
fixtures under `tests/`. Out of scope: changing model behavior, schemas, build
output, `docs/`, and `web/main.js` generated output.

## Steps

1. Add language-neutral fixture inputs for multi-occupation weighted demand,
   timeline aggregation, gap records, pathway ordering, and reskillable supply.
   Include exact .5 rounding and deterministic tie-break cases.
2. Expose only the pure browser runtime helpers needed to process those fixtures
   through `tests/parity_check.js`; do not load or test the DOM controller.
3. Add Python assertions that run the same fixtures and compare normalised JSON
   output with the Node result.
4. Add explicit conservation assertions that currently fail: allocated demand
   must sum to the rounded coefficient total, and all-cluster timeline totals
   must equal the unclustered timeline total for every year and phase.

## Test plan

- Demand allocation across two unequal weights and equal fractional remainders.
- Cluster and state timeline totals for every year of the 1 MT 2027 preset.
- Gap status, pathway sort order, and capped reskillable supply parity.

## Done criteria

- New conservation tests fail before Plan 002 changes production code.
- Existing parity tests remain green.
- The fixture protocol has no browser DOM dependency.

## STOP conditions

Stop if Python and browser use materially different published rounding rules;
that requires a product/model decision, not a test-only patch.
