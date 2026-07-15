# Plan 004: Fail closed on data ingestion and safe CSV export

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: LOW
- **Depends on**: `plans/001-shared-model-contracts.md`
- **Category**: security
- **Planned at**: commit `273a4c1`, 2026-07-15

## Why this matters

NCS pagination currently represents partial data after a failed later page as a
completed sector. Separately, browser and Python CSV writers quote delimiters
but do not neutralize spreadsheet-formula-leading text from upstream data.
Earlier parse/tabulate stages are the main untested pipeline boundary.

## Current state

~~~python
# scrape/scrape_ncs.py:169-176
html = fetch_html(url, ssl_ctx)
if html is None:
    return all_occupations
~~~

~~~javascript
// web/main.js.template:2822-2827
const text = String(value);
return /[",\\n\\r]/.test(text) ? '"' + text.replace(/"/g, '""') + '"' : text;
~~~

## Scope

In scope: `scrape/scrape_ncs.py`, `parse/parse_occupations.py`,
`tabulate/tabulate.py`, `build/build.py`, `model/compute.py`,
`web/main.js.template`, and tests. Out of scope: live scraping, external data
refresh, editing checked-in source data, and changing public CSV headers.

## Steps

1. Write a scraper test where page one succeeds and page two fetch/parse fails;
   it must fail until incomplete sector results cannot be marked as scraped.
2. Return explicit completion/failure state from pagination, retry incomplete
   sectors, and persist only a verified terminal page result.
3. Add one shared Python cell-sanitization policy and a mirrored browser policy:
   prefix nonempty text beginning with `=`, `+`, `-`, or `@` before normal CSV
   quoting. Do not alter numeric values.
4. Add fixture tests for missing titles, duplicate NCO IDs, Unicode text, fixed
   CSV schema ordering, and formula-leading strings in every Python/browser
   export route.

## Verification

- `python -m pytest tests/test_build.py tests/test_csv_export.py tests/test_compute.py` passes.
- New scraper/parse/tabulate tests fail before implementation and pass after.
- Existing ordinary exports retain their headers and values; formula-leading
  text receives only the documented neutralizing prefix.

## STOP conditions

Stop if a required parser policy would drop valid records rather than preserving
them with an explicit incomplete/failed status.
