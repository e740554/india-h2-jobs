# Design note: a true state layer for the India H2 Workforce Atlas

Companion to Plan 012 (state views: honest labeling, state summary export).
This note scopes the follow-up: a state view that is a genuine statewide
estimate rather than a cluster rollup.

## Problem

The atlas's "By State" filter and the new state summary export (Plan 012,
Steps 1-3) both sum the hydrogen clusters mapped to a state
(`model/clusters.json`). That is not a statewide employment estimate: a
state's number is only as complete as the clusters `model/clusters.json`
happens to map to it, and a state with zero mapped clusters is invisible in
the dropdown entirely (by design -- showing it would display a false zero).
Plan 012 makes this honest at the point of use. It does not fix the
underlying gap: a planner in a state with real H₂-adjacent industrial
activity but no mapped cluster (or partial cluster coverage) still cannot
get a number for their state from this tool.

## Option A: status quo + honest labeling (Plan 012)

Keep the cluster-rollup model. Label it as such everywhere it surfaces
(UI caveat, CSV note row). Do not add non-cluster states to the dropdown.

- **Cost:** none beyond Plan 012's build.
- **Benefit:** removes the over-trust risk without new modeling. A planner
  who reads the caveat knows exactly what they are looking at.
- **Limit:** does not solve the "invisible state" problem. A state with no
  mapped cluster still gets nothing.

## Option B: state allocation model (distribute national demand by affinity + residual share)

Distribute the national demand total to every state (not just cluster
states) using each cluster's existing `archetype_affinity` weights for
cluster-mapped states, plus a new residual-share coefficient for states with
H₂-adjacent industrial base but no mapped cluster (e.g. existing refining,
fertiliser, or steel capacity that could host future H₂ demand without
being a named cluster today).

**New coefficients required:**
- A residual-share weight per non-cluster state (what fraction of
  "un-clustered" national demand plausibly lands there).
- A decision rule for which states qualify for a residual share at all
  (an H₂-adjacency threshold on existing industrial base, most likely
  derived from the same NCS/NCO occupation scores already in
  `occupations.csv`, aggregated to state level -- state-level occupation
  location data does not currently exist in this repo and would itself
  need sourcing).

**Cost/benefit:** every new coefficient is a claim about the future
geographic distribution of unbuilt H₂ capacity, which is inherently
judgment-laden and disputable in a way the current cluster list (tied to
announced/planned projects) is not. Per Plan 011 (assumptions register),
any such coefficient must ship with a source in the register the day it
lands, or it undermines the "inspectable, disputable" claim the atlas is
built on. This is buildable without waiting on the PLFS rebuild, but it is
a modeling decision, not just an engineering one -- it should not be built
until a defensible source for residual shares exists (state industrial
policy documents, NITI Aayog state H₂ mission filings, or similar).

## Option C: supply-anchored state layer (wait for the PLFS unit-level rebuild)

`TODOS.md:59-69` already carries this dependency, verbatim:

> **Unit-level PLFS microdata pipeline (post-WHS rebuild)**
>
> **What:** Rebuild T0.2 from subdivision-level (Annual Report Statement
> 16/17) to unit-level (MoSPI microdata portal) PLFS pipeline. Cut from WHS
> sprint via ER-10 to free capacity for methodology hardening.
>
> **Why:** Subdivision-level is sufficient for WHS demo narrative but
> unit-level is the correct long-term architecture -- it enables
> state-level supply analysis, occupation-code granularity, and meaningful
> integration of future PLFS waves. Captured from /plan-eng-review on
> 2026-05-11 (DeepSeek peer review reversal of ER-1).
>
> **Context:** Existing ~1,802 legacy occupations are the only
> beneficiaries until NCO-2015 extension is codified (separate TODO). Pair
> with the "Automate MoSPI PLFS portal download" TODO so the rebuild ships
> with scripted refresh from day one.
>
> **Effort:** L (4-8 person-days)
> **Priority:** P2
> **Depends on:** "Automate MoSPI PLFS portal download" preferred but not
> blocking

Once unit-level PLFS microdata is in the pipeline, state becomes a real
dimension of the *supply* side (workers observed, by state, by NCO code) --
not just an allocation assumption on the demand side. A state layer built on
top of that is a supply-anchored estimate: demand still comes from the
scenario/archetype model (state-allocated per Option B or narrower), but it
can be checked against, and bounded by, an actual observed state-level labor
force. That is the only version of "statewide employment estimate" this
project can defend without new speculative coefficients.

**Cost/benefit:** highest quality, but blocked on the PLFS rebuild (P2, L
effort, not yet scheduled). No new work should start here before that
dependency lands.

## Recommendation

Sequencing:

1. **Now: Option A.** Plan 012 ships the honest label and the state summary
   export. No new coefficients, no new modeling risk.
2. **When the PLFS unit-level rebuild lands: Option C.** This is the
   correct long-term architecture and should be the target state layer.
   Re-scope a follow-up plan once that rebuild's actual data shape is known
   (state-level supply granularity depends on what the MoSPI microdata
   portal actually exposes).
3. **Option B only if a defensible source for residual shares surfaces
   independently** (e.g. a state industrial policy document naming H₂
   ambitions for a state with no mapped cluster) -- and even then, gate it
   on Plan 011's assumptions register landing first, since every residual
   coefficient needs a citable source from day one.

Do not build B or C speculatively. The honest-labeling slice (A) already
removes the credibility risk that motivated this design note; the two
richer options both cost real modeling risk or wait on external
dependencies, and neither is worth pre-building against a hypothetical.
