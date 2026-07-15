# Plan 007: Make high-frequency dashboard motion crisp and reduced-motion safe

- **Status**: TODO
- **Commit**: `273a4c1`
- **Severity**: HIGH
- **Category**: accessibility, performance, cohesion
- **Estimated scope**: 3 files, focused CSS and event-handler changes

## Problem

The institutional dashboard contains a three-cycle SVG selection pulse and
unconditional smooth scroll, `transition: all` on frequent controls, and
expensive per-event tooltip/year-slider work. Motion is therefore least
restrained on keyboard and pointer interactions users repeat often.

~~~css
/* web/style.css:927-962 -- current */
@keyframes pulse-outline { /* changes stroke-width from 2 to 4 */ }
.highlight-cell { animation: pulse-outline 0.8s ease-in-out 3; }
.mode-btn { transition: all 0.2s; }
~~~

~~~javascript
// web/main.js.template:2237-2245 -- current
rect.classed("highlight-cell", true);
node.scrollIntoView({ behavior: "smooth", block: "center" });
~~~

## Target

- Use existing `--ease-out: cubic-bezier(0.16, 1, 0.3, 1)` and declared
  150 ms / 250 ms durations. Add no bouncy or decorative motion.
- Replace `transition: all` with property-specific `color`, `background-color`,
  `border-color`, `box-shadow`, and `opacity` transitions.
- Use `transform: scale(0.97)` press feedback with a 150 ms ease-out transition
  only for pointer-pressable reusable controls.
- Under `prefers-reduced-motion: reduce`, use static high-contrast selection
  feedback, no keyframe pulse, and `scrollIntoView({ behavior: "auto" })`.
- Cache tooltip bounds, render it with `transform: translate(...)`, and
  coalesce pointer coordinates to one `requestAnimationFrame`.
- Update the visible year value synchronously but coalesce/redraw the treemap
  at most once per animation frame, flushing on the `change` event.
- For CSV progress, retain semantic progress values but use a fixed-size inner
  fill with `transform: scaleX(...)` and `transform-origin: left` rather than
  repeatedly animating width.

## Repo conventions to follow

- `web/style.css:56-57` is the sole motion-token surface.
- `web/main.js.template:2555-2561` already detects reduced motion before
  pathway scrolling; reuse that behavior.
- Treemap keyboard behavior at `web/main.js.template:2135-2183` must remain
  immediate and fully usable.

## Steps

1. Add failing JS/UI-helper tests for reduced-motion cell highlighting, one
   coalesced year redraw per frame, and tooltip transform positioning.
2. Make highlight scroll and CSS feedback honor reduced-motion policy. Remove
   repeated stroke-width keyframes rather than adding a new entrance animation.
3. Replace every frequent-control `transition: all` with explicit property
   transitions and add minimal pointer-only press feedback.
4. Coalesce tooltip/year-slider work without changing scenario math, selected
   occupation, aria announcements, or keyboard focus behavior.
5. Convert CSV progress rendering to transform-based visual progress while
   preserving `aria-valuenow`, text, and current chunking.
6. Optionally add a 150 ms opacity-only sidebar-content reveal on first
   pointer selection; it must be immediate under reduced motion and never run
   for keyboard roving focus.

## Boundaries

- Do not add a motion library, framework, global animation, or marketing-style
  stagger.
- Do not animate mode, filter, or keyboard-driven treemap state transitions.
- Do not alter D3 data/layout calculations except redraw scheduling.
- If performance traces show no measured tooltip/slider issue, retain the
  reduced-motion and token fixes but stop before an incremental-D3 rewrite.

## Verification

- **Mechanical**: `python -m pytest tests/test_ui_logic.py tests/test_parity.py`; `node --check web/main.js.template`.
- **Feel check**: In a local HTTP preview, repeatedly select pathway targets,
  drag the year slider, and move across treemap cells. Motion must feel
  immediate, never restart from zero, and retain selection clarity.
- **Reduced-motion check**: Emulate `prefers-reduced-motion: reduce`; verify
  scrolling is instant, no pulse runs, and visible static selection feedback
  remains.
- **Done when**: no `transition: all` remains in `web/style.css`; controls have
  subtle 150 ms press feedback; tooltip/progress motion uses transforms.
