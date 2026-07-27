# RUNBOOK — India H2 Workforce Atlas

**Purpose:** Bus-factor recovery. Any operator (even non-F1) can execute this
end-to-end on a clean machine during WHS Rotterdam 2026 (May 15–19).

---

## 1. Clone & Setup

```powershell
git clone https://github.com/e740554/india-h2-jobs.git
cd india-h2-jobs
```

**Requirements:**
- Python 3.12+ (CI target: 3.12)
- Node.js 22+ (for the test harness and generated-JS validation)
- Git

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 2. Build for Production

Generates the canonical `hygoat.in/workforce-atlas` publish bundle. Runtime
assets resolve relative to the current page, so this same artifact also works
on the GitHub Pages mirror at `e740554.github.io/india-h2-jobs/`.

```powershell
python build/build.py --base-url "/workforce-atlas"
```

> **This is the only build that may be committed.** CI re-runs it and then
> asserts `git diff --exit-code -- docs web`, so committing the output of any
> other `--base-url` value turns the Tests workflow red on every subsequent
> push until it is rebuilt. See section 3 for local preview.
>
> On Git Bash for Windows, MSYS rewrites `/workforce-atlas` into a Windows path.
> Use PowerShell, or prefix with `MSYS_NO_PATHCONV=1`.

**Expected output paths:**
| File | Purpose |
|------|---------|
| `docs/index.html` | Atlas root page |
| `docs/methodology/index.html` | Methodology page |
| `docs/about/index.html` | About page |
| `docs/style.css` | Shared stylesheet |
| `docs/main.js` | Client-side JS (portable canonical/mirror asset loading) |
| `docs/occupations.json` | H2-relevant occupations (~480) |
| `docs/occupations-all.json` | All 1,802 occupations |
| `docs/score-details.json` | Per-occupation score breakdown, fetched on click |
| `docs/h2-ready-occupations.csv` | H2-ready CSV export |
| `docs/assumptions-register.csv` | Every model coefficient with source, source type, and confidence |
| `docs/archetypes.json`, `scenarios.json`, `clusters.json`, `pathways.json`, `plfs_supply.json` | Published copies of the `model/` inputs |

---

## 2b. Release Checklist (version bump)

Run this before building a release. `tests/test_citation.py` fails until every
step is done, which is intentional -- it stops citation metadata from drifting
away from the shipped build.

1. Update `VERSION` to the new `vX.Y.Z.W` value.
2. Add a `## [X.Y.Z.W] - YYYY-MM-DD` heading and entry to `CHANGELOG.md`. The
   build reads the release date from this heading, so the format is load-bearing.
3. Update `CITATION.cff`: both the top-level `version` / `date-released` and the
   same two fields under `preferred-citation`. They must match `VERSION` and the
   changelog date exactly.
4. Update the suggested citation line and the release history table in `README.md`.
5. Rebuild with the production base URL, then run the full gate:

   ```powershell
   python build/build.py --base-url "/workforce-atlas"
   python -m pytest
   node --check web/main.js
   node --check docs/main.js
   git diff --exit-code -- docs web   # must be clean once docs/ is staged
   ```

   The last command is the exact assertion CI makes. Run it before pushing.

Note: the QR assets are not part of a version bump. They are regenerated only
when the Atlas root URL in `URL_FREEZE.md` changes:

```powershell
python scripts/generate_qr.py
```

`tests/test_qr.py` fails if the committed QR stops matching the frozen URL, so
a forgotten regeneration cannot reach print. The test suite itself generates
into a temporary directory and never rewrites `assets/`.

---

## 3. Build for Local Preview

Use an HTTP server: the app fetches JSON data and will not load correctly from a
`file://` URL.

No `--base-url` flag keeps local asset paths relative.

```powershell
python build/build.py
python -m http.server 8080 --directory docs
```

**Do not commit this build.** It writes `BASE_URL = ""` into `docs/main.js`,
which fails CI's publish-output check. Before staging anything in `docs/`,
re-run the production build from section 2.

---

## 4. Deploy

The site is hosted via **GitHub Pages** from the `docs/` directory on the `master` branch.

```powershell
# After build, commit and push:
git add docs/
git commit -m "build: regenerate docs/ for deploy"
git push origin master
```

Do not call the release deployed merely because the push succeeds. Confirm the
matching GitHub Actions test and Pages runs are successful, then smoke both
published surfaces and their JSON/JS assets:

```powershell
gh run list --repo e740554/india-h2-jobs --branch master --limit 2
.\scripts\smoke_prod.ps1
.\scripts\smoke_prod.ps1 -BaseUrl "https://e740554.github.io/india-h2-jobs"
```

The custom domain `hygoat.in` points to GitHub Pages infrastructure.

---

## 5. Hotfix Path (Conference Emergency)

If a typo is spotted on /methodology/ or /about/ during the conference:

1. Edit the source file directly in `docs/` (e.g., `docs/methodology/index.html`)
2. Commit and push:
   ```powershell
   git add docs/methodology/index.html
   git commit -m "hotfix: typo fix on methodology page"
   git push origin master
   ```
3. Confirm the matching Actions and Pages runs succeed, then run both smoke commands from the deploy section.
4. **Also edit the corresponding source in `web/`** (e.g., `web/methodology/index.html`)
   so the next build doesn't overwrite the fix.

---

## 6. Rollback

**Last-known-good commit hash** (pre-WHS baseline): `b8848b8` (v1.4.1.0)

### Quick rollback (revert to last-known-good):
```powershell
git revert <bad-commit-hash>
git push origin master
```

### Full reset to last-known-good:
```powershell
git reset --hard b8848b8
git push --force-with-lease origin master
```

**Caution:** `git push --force` rewrites remote history. Only use if revert is
not feasible. Coordinate with any ongoing conference edits.

---

## 7. Domain

| Item | Detail |
|------|--------|
| Canonical URL | https://hygoat.in/workforce-atlas |
| Mirror (fallback) | https://e740554.github.io/india-h2-jobs/ |
| DNS host | Cloudflare (hygoat.in) |
| Pages platform | GitHub Pages, `docs/` directory on `master` branch |
| Domain access | Founder (F1) — Ekansh |

The `workforce-atlas` path is served from the `docs/` directory of the repo.
The DNS CNAME record points `hygoat.in` → GitHub Pages IPs.

---

## 8. Troubleshooting

### Build fails
1. Check Python version: `python --version` (must be 3.12+)
2. Check all dependencies installed: `pip install -r requirements.txt`
3. Check `occupations.csv` exists in repo root (the data source)
4. Check `scores.json` exists in repo root (the scoring data)
5. If `build.py` errors with module imports, ensure you're running from repo root

### Page shows 404 or an empty atlas
1. Verify GitHub Pages is serving from `docs/` directory on `master` branch:
   GitHub repo → Settings → Pages → Source: Deploy from a branch → `master` / `docs/`
2. Confirm the deployed `main.js`, `occupations.json`, and `score-details.json` return HTTP 200 on both URLs with the smoke commands above.
3. Check custom domain is configured: Settings → Pages → Custom domain: `hygoat.in`
4. Verify DNS CNAME: `dig hygoat.in` should return GitHub Pages IPs
5. Check `docs/.nojekyll` exists (prevents Jekyll processing)

### Lens parameter ignored (`?lens=maritime` does nothing)
1. Verify the built `docs/main.js` contains the `LENS_WHITELIST` mapping:
   `{ maritime: 'Shipping' }`
2. Check that `docs/occupations.json` contains occupations in the Shipping sector
3. Verify the sector filter is in the sidebar (`<select id="sectorFilter">` inside `<aside class="sidebar">`)
