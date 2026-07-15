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

Generates `docs/` with the `/workforce-atlas` base URL so all asset paths resolve
correctly under the `hygoat.in/workforce-atlas` custom domain.

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
| `docs/main.js` | Client-side JS (with base URL injected) |
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

**Propagation time:** GitHub Pages typically deploys within 1–2 minutes. The
custom domain `hygoat.in` points to the GitHub Pages IPs via DNS CNAME/A record.

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
3. GitHub Pages auto-deploys within ~2 minutes.
4. **Also edit the corresponding source in `web/`** (e.g., `web/methodology/index.html`)
   so the next build doesn't overwrite the fix.

**Minute-by-minute:** 1 min edit → 1 min commit+push → ~2 min deploy = ~4 minutes total.

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

### Page shows 404
1. Verify GitHub Pages is serving from `docs/` directory on `master` branch:
   GitHub repo → Settings → Pages → Source: Deploy from a branch → `master` / `docs/`
2. Check custom domain is configured: Settings → Pages → Custom domain: `hygoat.in`
3. Verify DNS CNAME: `dig hygoat.in` should return GitHub Pages IPs
4. Check `docs/.nojekyll` exists (prevents Jekyll processing)

### Lens parameter ignored (`?lens=maritime` does nothing)
1. Verify the built `docs/main.js` contains the `LENS_WHITELIST` mapping:
   `{ maritime: 'Shipping' }`
2. Check that `docs/occupations.json` contains occupations in the Shipping sector
3. Verify the sector filter is in the sidebar (`<select id="sectorFilter">` inside `<aside class="sidebar">`)
