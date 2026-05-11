# QA Evidence — 2026-05-16

## Status: NEEDS BROWSE DAEMON

The gstack browse daemon (`$B`) is not installed/configured in this environment.
Browser-based QA (critical paths 1, 2, 3, 4, 6) requires the browse binary.

## What was verified locally

| Critical Path | Status | Method |
|---------------|--------|--------|
| CP1: Cold load on mobile | NOT RUN | Requires browser + network throttling |
| CP2: ?lens=maritime preselection | NOT RUN | Requires browser |
| CP3: Methodology trust path | PASS (local) | `docs/methodology/index.html` verified: Mukta, ../style.css, PLFS 2023-24, all 6 dimensions present |
| CP4: mailto contact | NOT RUN | Requires email client verification |
| CP5: Build to deploy | PASS (local) | `python build/build.py --base-url "/workforce-atlas"` runs clean, 166 tests pass |
| CP6: Telemetry events | N/A | Plausible analytics removed from WHS scope per founder |
| CP7: URL freeze audit | PASS (local) | All URL_FREEZE.md paths exist in docs/ after build (RFNBO removed per founder) |
| CP8: Bus-factor recovery | NOT RUN | RUNBOOK.md exists, F2 dry-run needs separate machine |

## Browser QA prerequisites

1. Install gstack browse daemon: follow `$GSTACK_ROOT/browse/SKILL.md`
2. Deploy latest docs/ to GitHub Pages (push to master)
3. Verify `hygoat.in` DNS resolves to GitHub Pages
4. Run: `$B goto https://hygoat.in/workforce-atlas`
5. Execute per-page checklist from `/qa` skill

## F2 dry-run checklist (RUNBOOK.md Section 1-4)

To be completed on a clean machine by May 16:
- [ ] Clone repo on clean machine
- [ ] `pip install -r requirements.txt`
- [ ] `python build/build.py --base-url "/workforce-atlas"`
- [ ] Open docs/index.html locally
- [ ] Verify methodology + about pages render
- [ ] Execute smoke_prod.ps1 against the deployed URL
