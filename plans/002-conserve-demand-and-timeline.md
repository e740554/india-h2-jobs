# Plan 002: Conserve modeled workforce totals at every allocation boundary

> **Executor instructions**: Complete Plan 001 first. Write the focused failing
> regression test before altering Python or JavaScript production code.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: `plans/001-shared-model-contracts.md`
- **Category**: bug
- **Planned at**: commit `273a4c1`, 2026-07-15

## Why this matters

Independent rounding loses or creates people. The checked-in 1 MT 2027 preset
produces 4,990 workers in an unclustered timeline but 4,860 after clustered
rounding. Current coefficient allocation also has scenario drift from -28 to
+17 workers. This is a release gate because the UI, gap results, and exports
inherit the totals.

## Current state

~~~python
# model/compute.py:106-120
for occ, w in zip(group_occs, weights):
    norm_weight = w / total_weight if total_weight > 0 else 1.0 / len(group_occs)
    occ_demand = raw_demand * norm_weight
    records.append({"occupation_id": occ["id"], "demand": round(occ_demand)})
~~~

~~~python
# model/timeline.py:88-99
rounded_phases = {phase: int(round(phases.get(phase, 0.0))) for phase in PHASES}
~~~

`web/main.js.template:151-199` and `:528-675` mirror these behaviors. The
existing `model/clusters.py:_largest_remainder_allocation` is the deterministic
integer-allocation exemplar to reuse.

## Commands

| Purpose | Command | Expected result |
|---|---|---|
| Focused tests | `python -m pytest tests/test_compute.py tests/test_supply.py tests/test_timeline.py tests/test_parity.py` | All pass |
| Full suite | `python -m pytest` | All pass |
| Runtime syntax | `node --check web/main.js.template` | Exit 0 |
| Build | `python build/build.py --base-url ""` | Regenerates expected local publish artifacts |

## Scope

In scope: `model/compute.py`, `model/supply.py`, `model/timeline.py`,
`web/main.js.template`, required tests, and regenerated tracked `docs/` output.
Out of scope: changes to staffing coefficients, PLFS source figures, scenario
definitions, cluster affinities, or public caveat language.

## Steps

1. Extract a deterministic largest-remainder helper suitable for weighted
   occupation allocation. It must allocate `round(raw_demand)` exactly and use
   a documented stable tie-breaker.
2. Apply the helper to Python demand allocation and mirror the exact algorithm
   in the browser runtime. Keep `allocation_weight` as rounded metadata, not
   the source of allocation.
3. Apply the same conservation policy to subdivision supply allocation, while
   retaining its indicative caveat and existing source fields.
4. Change timeline rounding so national, state, and cluster totals all preserve
   the same rounded year/phase total. Use deterministic remainder allocation;
   do not sum independently rounded cluster cells for All India.
5. Rebuild only after all model/parity tests are green; inspect generated
   scenario values and commit generated output only if it is an intentional
   consequence of the correction.

## Test plan

- Exact integer-total allocation with uneven and equal weights.
- Zero-weight equal split.
- Sum of every allocated coefficient equals rounded raw demand.
- Supply totals retain the represented subdivision total exactly.
- Every year/phase of clustered timeline equals its unclustered counterpart.
- Python/browser parity for all new cases.

## Done criteria

- All conservation assertions from Plan 001 pass in both runtimes.
- No scenario result is silently dropped or double counted.
- `python -m pytest` passes and generated JS syntax checks cleanly.

## STOP conditions

Stop if preserving totals requires changing the definition of a scenario,
cluster affinity, or PLFS methodology. Those are founder/model decisions.
