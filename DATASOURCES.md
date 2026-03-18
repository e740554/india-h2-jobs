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
- **robots.txt:** `User-agent: * allow: /` — ✅ Fully open to crawling
- **What:** Qualification profiles with NOS tables (code, title, NSQF level, mandatory/optional, hours, credits)

### URL Structure

| Pattern | Purpose | Method |
|---------|---------|--------|
| `nqr.gov.in/qualificationfile` | Qualification search (sector grid + filters) | GET |
| `nqr.gov.in/qualifications/{id}` | **Detail page** — NOS table (server-rendered HTML) | GET |
| `nqr.gov.in/filter-duration` | AJAX — filtered qualification listings | POST (needs CSRF `_token`) |

### Qualification Detail Page Fields

| Column | Description |
|--------|-------------|
| NOS/Module | NOS title |
| NOS Code | e.g., `MSRVVP/AVK01` |
| Mandatory/Optional | Whether NOS is required |
| Estimated Hours | Duration |
| NOS Credit | Credit value |
| Level | NSQF level |

### Key Sectors for H2 (sector IDs)

| ID | Sector |
|----|--------|
| 18 | Hydrocarbon |
| 35 | Power |
| 8 | Chemicals & Petrochemicals |
| 12 | Environmental Science |
| 7 | Capital Goods & Manufacturing |
| 51 | Water Supply/Sewerage/Waste |

Total: 59 sectors

### Bonus: Pre-built NCO Mapping

`ncvet.gov.in/wp-content/uploads/2025/05/Report-on-Mapping-of-Qualifications-with-NCO-Codes.pdf` — official NCO-2015 → qualification mapping. Could replace or validate hand-built crosswalk.

### Scraping Strategy

1. GET sector page → extract CSRF `_token`
2. POST to `/filter-duration` with `sectorId` → get qualification IDs
3. GET `/qualifications/{id}` → parse NOS table from server-rendered HTML

- **Raw data saved to:** `scrape/raw/ncvet/`

---

## Crosswalk

- PLFS uses NCO-2015 4-digit codes
- NCS uses NCO-2015 codes (available as lookup values in list data)
- NCVET uses its own NOS codes, linked to qualifications
- Hand-built crosswalk: `build/nco_ncs_crosswalk.csv`
- Official NCO mapping PDF from NCVET may reduce manual crosswalk work

## Data Licensing

All three sources are Government of India public resources. Data is used for open research and credited explicitly in the UI, README, and footer.
