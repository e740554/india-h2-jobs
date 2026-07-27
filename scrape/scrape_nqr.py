"""Scrape NQR (nqr.gov.in) qualification data for H2-relevant sectors.

nqr.gov.in is a Laravel site (server-rendered HTML + jQuery AJAX). Listing a
sector's qualifications requires a session-scoped CSRF flow:

    1. GET  /qualifications-search/{sector_id}   -- sets a session cookie and
       embeds a CSRF token (<meta name="csrf-token">).
    2. POST /filter-duration                     -- with that token and
       sectorId; the response embeds every qualification id for the sector
       as hidden ``getQualificationIds`` inputs (not paginated -- one POST
       returns the full id list regardless of the ``limit``/``offset`` sent).
    3. GET  /qualifications/{id}                 -- detail page, plain GET,
       no session needed; server-rendered NOS table plus qualification-level
       metadata (title, NQR code, sector, NSQF level, notional/delivery
       hours).

No third-party HTTP or HTML-parsing library is used (stdlib urllib + regex),
matching scrape_ncs.py and repo convention (no heavyweight scraping
frameworks; requirements.txt has none installed).

Usage:
    python scrape/scrape_nqr.py --sectors 18,35,8,12,7,51
    python scrape/scrape_nqr.py --sectors 18 --limit 5
    python scrape/scrape_nqr.py --sectors 18,35,8,12,7,51 --resume
"""

import argparse
import html
import http.cookiejar
import json
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw", "ncvet")
DETAIL_DIR = os.path.join(RAW_DIR, "detail")
COMBINED_FILE = os.path.join(RAW_DIR, "qualifications.json")
DELAY = 1.5  # seconds between requests

BASE_URL = "https://nqr.gov.in"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

CSRF_RE = re.compile(r'<meta name="csrf-token" content="([^"]+)"')
QUAL_ID_RE = re.compile(r'class="getQualificationIds" value="(\d+)"')
GET_COUNT_RE = re.compile(r'class="get_count" value="(\d+)"')

TITLE_RE = re.compile(r"<h1>(.*?)</h1>", re.DOTALL)
NQR_CODE_RE = re.compile(r'NQR Code:<span class="ml-1">([^<]+)</span>')
SECTOR_RE = re.compile(r"<label>Sector</label>\s*<div>\s*([^<]+?)\s*</div>")
LEVEL_RE = re.compile(r'alt="Level (\d+(?:\.\d+)?)" src="[^"]*level-i\.svg"')
NOTIONAL_HOURS_RE = re.compile(
    r"<label>Notional Hours</label>\s*<div>\s*Maximum\s*:\s*(\d+)\s*</div>\s*"
    r"<div>\s*Minimum\s*:\s*(\d+)\s*</div>"
)
DELIVERY_HOURS_RE = re.compile(
    r"<label>Training Delivery Hours</label>\s*<div>\s*<div>\s*Theory\s*:\s*(\d+)\s*</div>\s*"
    r"<div>\s*Practical\s*:\s*(\d+)\s*</div>"
)
TABLE_RE = re.compile(r"<table.*?</table>", re.DOTALL)
ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.DOTALL)
CELL_RE = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.DOTALL)


def create_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def strip_tags(cell: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", cell).strip())


def build_opener(ssl_ctx: ssl.SSLContext):
    """A fresh cookie-jar opener, scoped to one sector's CSRF session."""
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
        urllib.request.HTTPSHandler(context=ssl_ctx),
    )


def fetch(url: str, opener, ssl_ctx: ssl.SSLContext, data: bytes | None = None,
          extra_headers: dict | None = None) -> str | None:
    """GET (or POST when ``data`` is given). Returns decoded text, or None on error."""
    headers = {"User-Agent": UA}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        if opener is not None:
            resp = opener.open(req, timeout=30)
        else:
            resp = urllib.request.urlopen(req, context=ssl_ctx, timeout=30)
        with resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, ssl.SSLError, TimeoutError) as e:
        print(f"  [ERROR] Failed to fetch {url}: {e}")
        return None


def extract_csrf_token(page_html: str) -> str | None:
    match = CSRF_RE.search(page_html)
    return match.group(1) if match else None


def list_sector_qualification_ids(sector_id: int, ssl_ctx: ssl.SSLContext) -> tuple[list[str], int | None]:
    """Return (qualification ids, reported total) for a sector, or ([], None) on failure."""
    opener = build_opener(ssl_ctx)
    search_url = f"{BASE_URL}/qualifications-search/{sector_id}"
    html = fetch(search_url, opener, ssl_ctx)
    if html is None:
        return [], None

    token = extract_csrf_token(html)
    if not token:
        print(f"  [ERROR] No CSRF token found on {search_url}")
        return [], None

    time.sleep(DELAY)

    data = {
        "offset": "0", "educationId": "", "experienceId": "", "trainingId": "",
        "limit": "12", "duration_id": "", "sectorId": str(sector_id),
        "nsqf_level": "", "qualfType": "", "awarding_body": "",
        "qualificationidsArrayIds": "", "_token": token,
        "table_name": "", "currentroute": "",
    }
    body = urllib.parse.urlencode(data).encode("utf-8")
    filter_html = fetch(
        f"{BASE_URL}/filter-duration", opener, ssl_ctx, data=body,
        extra_headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": search_url,
        },
    )
    if filter_html is None:
        return [], None

    ids = QUAL_ID_RE.findall(filter_html)
    count_match = GET_COUNT_RE.search(filter_html)
    reported_total = int(count_match.group(1)) if count_match else None
    return ids, reported_total


def parse_qualification_detail(page_html: str, qual_id: str, sector_id: int) -> dict:
    """Parse a qualification detail page. Missing fields are None, never a crash."""
    title_match = TITLE_RE.search(page_html)
    title = strip_tags(title_match.group(1)) if title_match else None

    nqr_code_match = NQR_CODE_RE.search(page_html)
    nqr_code = html.unescape(nqr_code_match.group(1).strip()) if nqr_code_match else None

    sector_match = SECTOR_RE.search(page_html)
    sector = html.unescape(sector_match.group(1).strip()) if sector_match else None

    level_match = LEVEL_RE.search(page_html)
    nsqf_level = _parse_level(level_match.group(1)) if level_match else None

    hours_match = NOTIONAL_HOURS_RE.search(page_html)
    hours_max = int(hours_match.group(1)) if hours_match else None
    hours_min = int(hours_match.group(2)) if hours_match else None

    delivery_match = DELIVERY_HOURS_RE.search(page_html)
    theory_hours = int(delivery_match.group(1)) if delivery_match else None
    practical_hours = int(delivery_match.group(2)) if delivery_match else None

    nos_rows = []
    for table in TABLE_RE.findall(page_html):
        if "National Occupation Standards" not in table:
            continue
        rows = ROW_RE.findall(table)
        for row in rows[1:]:  # skip header row
            cells = [strip_tags(c) for c in CELL_RE.findall(row)]
            if len(cells) < 6:
                continue
            nos_title, nos_code, mandatory_optional, hours_str, credits_str, level_str = cells[:6]
            nos_rows.append({
                "nos_title": nos_title,
                "nos_code": nos_code,
                "mandatory_optional": mandatory_optional,
                "hours": int(hours_str) if hours_str.isdigit() else None,
                "credits": float(credits_str) if _is_number(credits_str) else None,
                "level": _parse_level(level_str),
            })
        break  # first matching table is the NOS table

    return {
        "id": qual_id,
        "sector_id": sector_id,
        "title": title,
        "nqr_code": nqr_code,
        "sector": sector,
        "nsqf_level": nsqf_level,
        "hours_min": hours_min,
        "hours_max": hours_max,
        "theory_hours": theory_hours,
        "practical_hours": practical_hours,
        "nos": nos_rows,
        "url": f"{BASE_URL}/qualifications/{qual_id}",
    }


def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def _parse_level(s: str) -> int | float | None:
    """NSQF levels are usually whole numbers but half-levels (e.g. 5.5) occur."""
    if not _is_number(s):
        return None
    value = float(s)
    return int(value) if value.is_integer() else value


def fetch_qualification_detail(qual_id: str, sector_id: int, ssl_ctx: ssl.SSLContext,
                                 resume: bool) -> tuple[dict | None, bool]:
    """Returns (record, fetched_live). fetched_live is False for a cache hit --
    callers should only apply the politeness delay when it's True."""
    detail_path = os.path.join(DETAIL_DIR, f"{qual_id}.html")
    if resume and os.path.exists(detail_path):
        with open(detail_path, "r", encoding="utf-8") as f:
            page_html = f.read()
        return parse_qualification_detail(page_html, qual_id, sector_id), False

    page_html = fetch(f"{BASE_URL}/qualifications/{qual_id}", None, ssl_ctx)
    if page_html is None:
        return None, True
    os.makedirs(DETAIL_DIR, exist_ok=True)
    with open(detail_path, "w", encoding="utf-8") as f:
        f.write(page_html)

    return parse_qualification_detail(page_html, qual_id, sector_id), True


def main():
    parser = argparse.ArgumentParser(description="Scrape NQR qualification data")
    parser.add_argument("--sectors", required=True, help="Comma-separated NQR sector ids, e.g. 18,35,8,12,7,51")
    parser.add_argument("--limit", type=int, default=None, help="Cap total detail pages fetched this run (testing)")
    parser.add_argument("--resume", action="store_true", help="Reuse already-saved detail HTML instead of refetching")
    args = parser.parse_args()

    os.makedirs(RAW_DIR, exist_ok=True)
    sector_ids = [int(s.strip()) for s in args.sectors.split(",") if s.strip()]
    ssl_ctx = create_ssl_context()

    all_qualifications = []
    fetched_this_run = 0

    for sector_id in sector_ids:
        print(f"Listing sector {sector_id}...")
        qual_ids, reported_total = list_sector_qualification_ids(sector_id, ssl_ctx)
        if reported_total is None:
            print(f"  [ERROR] Could not list sector {sector_id}, skipping")
            continue
        print(f"  {len(qual_ids)} qualification ids (site reports {reported_total})")

        sector_qualifications = []
        for qual_id in qual_ids:
            if args.limit is not None and fetched_this_run >= args.limit:
                print(f"  [LIMIT] Reached --limit {args.limit}, stopping")
                break

            record, fetched_live = fetch_qualification_detail(qual_id, sector_id, ssl_ctx, args.resume)
            fetched_this_run += 1
            if record is None:
                print(f"  [WARN] Failed to fetch/parse qualification {qual_id}")
                if fetched_live:
                    time.sleep(DELAY)
                continue
            sector_qualifications.append(record)
            print(f"  [{fetched_this_run}] {qual_id}: {record['title']} (NSQF {record['nsqf_level']}, {len(record['nos'])} NOS)")
            if fetched_live:
                time.sleep(DELAY)

        sector_file = os.path.join(RAW_DIR, f"sector_{sector_id}.json")
        with open(sector_file, "w", encoding="utf-8") as f:
            json.dump(sector_qualifications, f, indent=2, ensure_ascii=False)
        all_qualifications.extend(sector_qualifications)

        if args.limit is not None and fetched_this_run >= args.limit:
            break

    # Dedup by id when combining (a qualification could appear in more than one sector list).
    combined = {}
    for record in all_qualifications:
        combined[record["id"]] = record
    with open(COMBINED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(combined.values()), f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(combined)} unique qualifications across {len(sector_ids)} sectors.")
    print(f"Saved to: {COMBINED_FILE}")


if __name__ == "__main__":
    main()
