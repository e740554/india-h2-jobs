# Contributing

## Source Of Truth

- Edit pipeline code in `scrape/`, `parse/`, `tabulate/`, `score/`, and `build/`
- Edit frontend source in `web/`
- Treat `docs/` as generated publish output for GitHub Pages
- Do not edit generated JSON, CSV, or compiled JS in the repo root or `docs/` by hand

## Local Workflow

```bash
python build/build.py --base-url ""
cd docs && python -m http.server 8080
```

If you are iterating on the frontend shell, the same build also refreshes ignored dev copies in `web/`:

```bash
cd web && python -m http.server 8080
```

## Before Opening A PR

- Rebuild with `python build/build.py --base-url ""`
- Verify the current checked-in dataset claims still match the generated output
- Commit `docs/` changes when the published site changes
- Do not commit ignored local-dev artifacts from `web/`
- Keep methodology and README copy aligned with actual data coverage
