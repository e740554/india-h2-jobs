# Contributing

Thanks for contributing to the India H2 Workforce Atlas.

## Before You Start

- Use the GitHub issue templates for bugs and feature requests where possible.
- Read [README.md](README.md), [TESTING.md](TESTING.md), and [DATASOURCES.md](DATASOURCES.md) before changing model or pipeline behavior.
- Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) in issues, pull requests, and review threads.
- Report exploitable bugs privately per [SECURITY.md](SECURITY.md). Do not open public issues for security problems.

## Source Of Truth

- Edit pipeline code in `scrape/`, `parse/`, `tabulate/`, `score/`, `model/`, and `build/`.
- Edit frontend source in `web/`.
- Treat `docs/` as generated publish output for GitHub Pages.
- Do not edit generated JSON, CSV, or compiled JS in the repo root or `docs/` by hand.

## Local Workflow

Rebuild the site output and serve the published bundle:

```bash
python build/build.py --base-url ""
cd docs && python -m http.server 8080
```

If you are iterating on the frontend shell, the same build also refreshes ignored dev copies in `web/`:

```bash
cd web && python -m http.server 8080
```

Run the test suite before opening a PR:

```bash
python -m pytest
```

## Working Conventions

- Keep Python and browser runtime behavior aligned when changing shared model logic.
- Add or extend tests when you change archetypes, scenarios, rounding, cluster distribution, timeline behavior, pathways, exports, or build fields consumed by the UI.
- Update public-facing docs when shipped behavior changes. That usually means some combination of `README.md`, `TESTING.md`, `CHANGELOG.md`, `TODOS.md`, and the Phase specs under `docs/superpowers/specs/`.
- Commit regenerated `docs/` output when the GitHub Pages site changes.
- Do not commit ignored local-dev artifacts from `web/`.

## Pull Requests

Before opening a PR, make sure you have:

- run `python -m pytest` and confirmed it passes
- rebuilt with `python build/build.py --base-url ""` when publish output changed
- verified current dataset claims still match generated output
- included `docs/` changes when the published site changed
- kept methodology, README, testing notes, and changelog references aligned with actual behavior

Small, well-scoped PRs are easier to review than mixed pipeline, UI, and copy changes.

## Release Notes And Tags

- `CHANGELOG.md` is the release history source of truth.
- Taggable releases use the `vX.Y.Z.W` format.
- Historical public releases from `v1.0.0.0` onward are now backfilled and should stay immutable.

## Questions

If something is unclear, open an issue with reproduction steps, the scenario or dataset slice involved, and screenshots when the question is UI-specific.
