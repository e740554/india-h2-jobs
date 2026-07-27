# Design note: user-supplied coefficient overrides

Follow-up to Plan 011 (assumptions register). Design only -- not built here.

## Goal

A skeptical reviewer (labour economist, NSDC research staff, a competing
consultancy) reads a row in `assumptions-register.csv`, disagrees with the
value, and wants to see the effect of their own number on a live scenario
without forking the repo or filing a PR first. The goal is a fast, honest
"what if this coefficient were different" loop that never contaminates the
published dataset.

## Proposed mechanism

URL-encoded overrides, one `override` query parameter per changed row, using
the same `(component, item_id, parameter[, phase])` identity that the
assumptions register already publishes:

```
?override=staffing_coefficient:alkaline_1gw:7212:construction=520
&override=cluster_affinity:kutch:pem_500mw=0.25
&override=scenario_composition:nghm_5mt_2030_mix:ammonia_1mtpa=0.8
```

The frontend (`web/main.js.template`) parses `override` params on load,
validates each against the loaded `archetypes.json` / `clusters.json` /
`pathways.json` / `scenarios.json` (unknown component/item_id/parameter is
rejected with a console warning, not silently applied), substitutes the
value into an in-memory copy of the coefficient before running the existing
demand/timeline math, and never writes the override back to any file.

## Required safeguards

1. **Always-visible "user-modified assumptions" banner.** Any time one or
   more `override` params are active, an unmissable banner (not a toast,
   not a tooltip) stays pinned above the mode toggle for the entire session,
   listing which rows are overridden and their original vs. substituted
   values. There is no way to dismiss it while an override is active.
2. **Watermarking on every export.** The Plan 010 briefing-pack PDF/print
   view and both CSV downloads (current-view snapshot, full scenario
   snapshot) must stamp a visible "user-modified assumptions -- not the
   published dataset" watermark whenever any override is active for that
   run. An overridden export that looks identical to a canonical export is
   the failure mode this exists to prevent.
3. **Overrides never persist.** No override is written to `localStorage`,
   `sessionStorage`, a cookie, or any backend. Reloading the page without the
   query string returns to the canonical dataset. There is no "save my
   override" feature.

These three are non-negotiable for the feature to ship; an override system
without the user-modified banner and export watermark is worse than not
having the feature, because it lets a modified run masquerade as the
published atlas.

## Open questions

- **Should overrides be shareable links?** A colleague-facing "look what
  happens if `re_ratio_gw_per_gw_electrolyser` were 2.0 instead of 2.5" link
  is the main legitimate use case, which argues for shareability. But a
  shareable override link is also a shareable *misleading* link if screenshotted
  or forwarded without the banner surviving (e.g. a cropped screenshot). No
  resolution yet; leaning toward shareable-but-banner-is-part-of-any-screenshot-friendly
  layout (pin it where a normal viewport screenshot cannot crop it out).
- **Cap on how many parameters can be overridden at once?** Unbounded
  overrides let a user reconstruct an entirely different model under the
  atlas's name. A cap (e.g. 5 active overrides) keeps the feature to "test a
  disagreement," not "publish a shadow model." Needs a product call, not an
  engineering one.
- **Does an override change the URL length/shareability in ways that break
  existing URL_FREEZE.md canonical-path guarantees?** Query params are
  additive and shouldn't affect the frozen paths, but this needs a check
  against `URL_FREEZE.md` before implementation.

## Recommendation

Build this **after** the NQR/NCVET qualification-layer integration (Plan
009), not now. Reasoning: Plan 009 is a spike into whether a new data axis
(qualification framework alignment) gets bolted onto the same archetype/
scenario model this override feature would target. Building the override UI
first means either re-doing the override grammar once Plan 009 lands new
coefficient types, or scoping overrides to freeze out NQR fields on day one
and having to widen the grammar later under time pressure. The assumptions
register itself (this plan) is the higher-value, lower-risk piece to ship
now: it makes every number inspectable today. The override feature is a
richer but riskier interaction surface, and its safeguards (banner,
watermark, no-persistence) deserve their own focused review pass rather than
being squeezed in alongside an unrelated data-model change.
