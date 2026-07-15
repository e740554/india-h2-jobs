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
| `docs/h2-ready-occupations.csv` | H2-ready CSV export |

---

## 3. Build for Local Preview

Use an HTTP server: the app fetches JSON data and will not load correctly from a
`file://` URL.

No `--base-url` flag keeps local asset paths relative.

```powershell
python build/build.py
python -m http.server 8080 --directory docs
```

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
