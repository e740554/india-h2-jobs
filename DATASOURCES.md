# Data Sources — India H2 Workforce Atlas

## 1. NCS Portal (National Career Service)

- **URL:** https://www.ncs.gov.in
- **Platform:** Microsoft SharePoint 2013/2016, ASP.NET WebForms
- **What:** 4,000+ occupation profiles with Title, NCO-2015 Code, Sector
- **Access method:** HTTP GET (no Playwright needed) — inline JSON (`WPQ2ListData`) on ViewNcos pages
- **robots.txt:** `/content-repository/` is NOT disallowed. Occupation pages are in sitemap. ✅ Scraping permitted.
- **SSL note:** Requires TLS 1.2 (`--tlsv1.2`) and `--compressed` flags. Intermittent TLS failures.

### URL Structure

| Pattern | Purpose |
|---------|---------|
| `/content-repository/Pages/BrowseBySectors.aspx` | Sector listing (52 sectors) |
| `/content-repository/Pages/ViewNcos.aspx?FilterField1=Industry_x002F_Sector_x0028_s_x0&FilterValue1={SECTOR}` | Occupations filtered by sector |

### Data Extraction

The ViewNcos page embeds occupation data as inline JSON:
```
var WPQ2ListData = {...};var WPQ2SchemaData
```
Parse with regex. Each record contains:
- `Title` — occupation name
- `NCO_x0020_Code` — lookup with `lookupValue` (e.g., `"3113.0202"`)
- `Industry_x002F_Sector_x0028_s_x0` — sector lookup

### Pagination

No server-side pagination observed (Power sector: 35 records in one page). Large sectors may use SharePoint `Paged=TRUE&p_ID={lastID}` pattern.

### Auth-Gated (NOT accessible)

- `DispForm.aspx?ID={id}` — individual detail pages (401)
- `_api/web/lists/...` — SharePoint REST API (403)
- Detail fields (skills, education, wages) are NOT available from list view

### 52 Sectors Available

Agriculture, Aerospace/Aviation, Apparel, Automotive, Beauty/Wellness, BFSI, Capital Goods/Manufacturing, Chemical/Petrochemicals, Construction, Education/Training, Electronics, Environmental Science, Food Industry, Gem/Jewellery, Glass/Ceramics, Handicrafts, Healthcare, Hydrocarbon, Infrastructure Equipment, Iron/Steel, IT-ITeS, Judiciary, Leather, Legal, Legislators, Life Sciences, Logistics, Media/Entertainment, Mining, Musical Instruments, Office Admin, Optical Products, Organised Retail, Paper, Plumbing, Postal, **Power**, Printing, Private Security, Public Admin, Railways, Real Estate, Religious, Rubber, Shipping, Sports/Fitness, Telecom, Textile/Handloom, Tobacco, Tourism/Hospitality, Water Supply/Sewerage/Waste, Wood/Carpentry

- **Rate limit:** 1.5s between requests (self-imposed politeness)
- **Raw data saved to:** `scrape/raw/ncs/`

---

## 2. PLFS (Periodic Labour Force Survey 2023–24)

- **URL:** https://mospi.gov.in
- **What:** Employment headcount, wages, formal/informal split by NCO-2015 occupation code

### Data Access Options (ranked by ease)

**Option A — Annual Report PDF (quickest for v1):**
- URL: `https://www.mospi.gov.in/sites/default/files/publication_reports/AnnualReport_PLFS2023-24L2.pdf`
- Statement 16/17: % distribution of workers by NCO-2015 occupation division/subdivision
- Parse tables with `tabula-py` or `camelot`
- WHS checked-in artifact: `model/plfs_supply.json` uses PLFS 2023-24 Annual Report Table 25, rural+urban person column, NCO-2015 2-digit subdivisions. Headcounts are indicative subdivision-allocated estimates, not occupation-observed PLFS unit-level estimates.

**Option B — eSankhyiki API (programmatic):**
- URL: `https://esankhyiki.mospi.gov.in/macroindicators?product=plfs`
- Supports CSV/Excel/JSON downloads
- 492 PLFS datasets in catalogue

**Option C — Unit-level microdata (most granular, requires registration):**
- URL: `https://microdata.gov.in/NADA/index.php/catalog/213/related-materials`
- Fixed-width .txt files (not CSV) — need data dictionary for byte positions
- NCO-2015 is a 3-digit field in person-level records
- Reference parser: `github.com/12janhavi/PLFS_Data`

### Expected Fields (unit-level)

`HHID | Person_Sl_No | Age | Sex | General_Education | Technical_Education | Status_Code | NIC_2008_Code | NCO_2015_Code | Sector | State | District | Weight`

### Other Resources

- Press note: `mospi.gov.in/sites/default/files/press_release/Press_note_AR_PLFS_2023_24_22092024.pdf`
- MoSPI download tables: `mospi.gov.in/download-tables-data`
- PIB release: `pib.gov.in/PressReleasePage.aspx?PRID=2057970`

- **Raw data saved to:** `scrape/raw/plfs/`

---

## 3. NCVET / National Qualifications Register

**Primary source: nqr.gov.in** (NOT skillindiadigital.gov.in which is an Angular SPA with `Disallow: /`)

- **URL:** https://nqr.gov.in
- **Platform:** Laravel (server-rendered HTML + jQuery AJAX)
- **robots.txt:** `User-agent: * allow: /` — ✅ Fully open to crawling (confirmed live, 2026-07-27)
- **What:** Qualification profiles with NOS tables (code, title, NSQF level, mandatory/optional, hours, credits)
- **Does NOT carry an NCO-2015 code anywhere.** Confirmed by grepping all 295
  scraped detail pages for the whole-word token `NCO`: zero matches. NQR
  identifies qualifications by its own NQR code (e.g. `2022/HYC/HSSCI/06782`)
  and NOS codes (e.g. `HYC/N6401`) only. See
  `plans/009-spike-report.md` for the full join-coverage analysis.

### URL Structure (observed reality — corrects the pattern below)

Actual scraping flow found by the 2026-07-27 spike (`scrape/scrape_nqr.py`):

| Pattern | Purpose | Method |
|---------|---------|--------|
| `nqr.gov.in/qualifications-search/{sector_id}` | Sector listing page — sets session cookie, embeds `<meta name="csrf-token">` | GET |
| `nqr.gov.in/filter-duration` | AJAX — returns **every** qualification id for the sector as hidden `getQualificationIds` inputs (tagged with a `get_count` total), regardless of the `limit`/`offset` sent — no pagination needed to build the id list | POST (needs CSRF `_token` + the session cookie from the GET above) |
| `nqr.gov.in/qualifications/{id}` | Detail page — NOS table + qualification metadata (server-rendered HTML), plain GET, no session needed | GET |

(`nqr.gov.in/qualificationfile` from the original spec is a search-UI page;
it does not carry the CSRF token used by the sector page's AJAX flow.)

### Qualification Detail Page Fields (as scraped)

| Field | Description | Quirk observed |
|-------|--------------|-----------------|
| Title | `<h1>` | — |
| NQR Code | e.g. `2022/HYC/HSSCI/06782` | — |
| Sector | e.g. `Hydrocarbon` | — |
| NSQF level (qualification + per-NOS-row) | e.g. `3`, or `5.5` | **Half-levels are real** (96/295 scraped qualifications, 33%) — do not parse as integer-only |
| Notional Hours (min/max), Theory/Practical delivery hours | e.g. `330`/`330`, `90`/`150` | — |
| NOS/Module, NOS Code, Mandatory/Optional, Estimated Hours, NOS Credit, Level | one row per module | 2/295 qualifications render no NOS table at all (genuine gap, not a parse failure) |

### Key Sectors for H2 (sector IDs) — all 6 confirmed live, 2026-07-27

| ID | Sector | Qualifications scraped |
|----|--------|------------------------|
| 18 | Hydrocarbon | 76 |
| 35 | Power | 22 |
| 8 | Chemicals & Petrochemicals | 20 |
| 12 | Environmental Science | 64 |
| 7 | Capital Goods & Manufacturing | 107 |
| 51 | Water Supply, Sewerage, Waste Management & Remediation activities | 6 |

Total: 59 sectors (confirmed). 295 unique qualifications across these 6, no
id overlap between sectors.

### Official NCO Mapping PDF — NOT a per-qualification crosswalk

`ncvet.gov.in/wp-content/uploads/2025/05/Report-on-Mapping-of-Qualifications-with-NCO-Codes.pdf`
downloads fine (58 pages) but, despite its title, is a **policy/process
report** about the 2023 NCO-mapping committee's work (methodology, findings,
recommendations) — not a queryable qualification→NCO-code table. A full-text
search for NCO-2015-shaped strings across all 58 pages found exactly 2
unique codes, both illustrative examples in prose. The one real table it
contains (Annexure VII) is an awarding-body-level aggregate (45 bodies,
e.g. "DGT: 463 total qualifications, 0 without an NCO code"), not a
per-qualification lookup. See `plans/009-spike-report.md` §2.

### Scraping Strategy (as implemented)

1. GET `qualifications-search/{sector_id}` → extract CSRF `_token`, keep the session cookie
2. POST to `/filter-duration` with `sectorId` (+ empty filter fields + the token) → response embeds every qualification id for the sector
3. GET `/qualifications/{id}` → parse title/sector/NSQF level/hours + NOS table from server-rendered HTML (plain GET, new cookie jar not required)

1.5s delay between requests; resume-tolerant (cached detail pages under
`scrape/raw/ncvet/detail/` are reused, not refetched).

- **Raw data saved to:** `scrape/raw/ncvet/` (gitignored, same as `scrape/raw/ncs/` and `scrape/raw/plfs/`)

---

## Crosswalk

- PLFS uses NCO-2015 4-digit codes
- NCS uses NCO-2015 codes (available as lookup values in list data)
- NCVET uses its own NOS codes, linked to qualifications, with **no NCO-2015
  code anywhere** in the qualification data or the official mapping PDF
  (confirmed 2026-07-27; see `plans/009-spike-report.md`)
- There is no hand-built NCO/NCS crosswalk file in this repo. (An earlier
  version of this document referenced `build/nco_ncs_crosswalk.csv`; `git
  log` shows that path was never committed. Corrected here.)

## Data Licensing

All three sources are Government of India public resources. Data is used for open research and credited explicitly in the UI, README, and footer.
