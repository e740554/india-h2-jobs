# URL Freeze -- WHS Rotterdam 2026
Frozen: 2026-05-15
Print deadline: 2026-05-15 EOD (Fri)
Live deadline: 2026-05-19 17:30 CEST (Tue)

## Canonical URLs (do NOT change without adding a redirect)
| URL | Purpose | Appears in |
|-----|---------|------------|
| https://hygoat.in/workforce-atlas | Atlas root | One-pager QR, business cards |
| https://hygoat.in/workforce-atlas/methodology/ | Methodology page | Footer link, sidebar inline link |
| https://hygoat.in/workforce-atlas/about/ | About page | Footer link |
| https://hygoat.in/workforce-atlas/?lens=maritime | Maritime workshop share | Workshop speaker emails |
| mailto:ekansh@ekavikalp.com | Contact | Footer, /about/ |

## Build-time guarantee
After 2026-05-15 EOD, `python build/build.py --base-url "/workforce-atlas"` must produce all paths above unchanged. Any path change requires a redirect entry below.

## Redirects (post-freeze)
None.

## Pre-launch content decisions
- **2026-05-11 (Task 5):** Advisory Circle section removed from `/about/` per founder decision. Empty state ("We're building a panel…") signaled incompleteness; better to ship a clean /about/ with just Contact. Advisory Circle content (HTML, CSS, commented-out template) preserved in git history and can be restored post-WHS when advisors are confirmed.
- **2026-05-11:** RFNBO lens (`?lens=rfnbo`) removed from URL freeze and lens whitelist per founder. No sector mapping for RFNBO at WHS.
- **2026-05-11:** Plausible analytics snippet stripped from all pages per founder — telemetry out of WHS scope.
- **2026-05-11:** hygoat.in canonical URL confirmed resolving.

## Print-proof scan log
<!-- populated after manual print-proof scan -->
