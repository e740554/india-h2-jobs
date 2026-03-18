"""Scrape NCS Portal (ncs.gov.in) occupation data.

The NCS Portal is a SharePoint site that embeds occupation list data as inline JSON
(WPQ2ListData) on ViewNcos.aspx pages. We iterate over all 52 sectors, fetch each
page via HTTP, and extract Title + NCO Code + Sector from the JSON payload.

No Playwright needed — the data is in the HTML source as inline JS.
Detail pages (DispForm) are auth-gated, so we only get list-level fields.

Usage:
    python scrape/scrape_ncs.py
    python scrape/scrape_ncs.py --resume    # Skip already-scraped sectors
"""

import argparse
import json
import os
import re
import ssl
import time
import urllib.request
import urllib.error

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw", "ncs")
OUTPUT_FILE = os.path.join(RAW_DIR, "ncs_occupations.json")
SECTORS_FILE = os.path.join(RAW_DIR, "scraped_sectors.json")
DELAY = 1.5  # seconds between requests

BASE_URL = "https://www.ncs.gov.in/content-repository/Pages/ViewNcos.aspx"
FILTER_PARAM = "FilterField1=Industry_x002F_Sector_x0028_s_x0&FilterValue1="

# All 52 NCS sectors (from sitemap)
SECTORS = [
    "Agriculture", "Aerospace and Aviation", "Apparel", "Automotive",
    "Beauty and Wellness", "BFSI", "Capital Goods and Manufacturing",
    "Chemical and Petrochemicals", "Construction", "Education/Training/Research",
    "Electronics and HW", "Environmental Science", "Food Industry",
    "Gem and Jewellery", "Glass and Ceramics", "Handicrafts and Carpets",
    "Healthcare", "Hydrocarbon", "Infrastructure Equipment", "Iron and Steel",
    "IT-ITeS", "Judiciary", "Leather", "Legal Activities", "Legislators",
    "Life Sciences", "Logistics", "Media and Entertainment", "Mining",
    "Musical Instruments", "Office Administration and Facility Management",
    "Optical Products", "Organised Retail", "Paper and Paper Products",
    "Plumbing", "Postal Services", "Power", "Printing", "Private Security",
    "Public Administration", "Railways", "Real Estate", "Religious Professionals",
    "Rubber Industry", "Shipping", "Sports/Physical Education/Fitness/Leisure",
    "Telecom", "Textile and Handloom", "Tobacco Industry",
    "Tourism and Hospitality", "Water Supply/Sewerage/Waste Management",
    "Wood and Carpentry",
]

# Regex to extract WPQ2ListData JSON from the page HTML
LIST_DATA_RE = re.compile(r"var WPQ2ListData\s*=\s*(\{.+?\})\s*;\s*var WPQ2SchemaData", re.DOTALL)


def create_ssl_context():
    """Create SSL context that works with NCS Portal's TLS setup."""
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def fetch_sector(sector: str, ssl_ctx: ssl.SSLContext) -> list[dict]:
    """Fetch all occupations for a given sector from NCS Portal."""
    url = f"{BASE_URL}?{FILTER_PARAM}{urllib.request.quote(sector)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
    })

    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            # Handle gzip encoding
            data = resp.read()
            encoding = resp.headers.get("Content-Encoding", "")
            if encoding == "gzip":
                import gzip
                data = gzip.decompress(data)
            elif encoding == "br":
                import brotli
                data = brotli.decompress(data)
            html = data.decode("utf-8", errors="replace")
    except (urllib.error.URLError, ssl.SSLError, TimeoutError) as e:
        print(f"  [ERROR] Failed to fetch {sector}: {e}")
        return []

    # Extract inline JSON
    match = LIST_DATA_RE.search(html)
    if not match:
        print(f"  [WARN] No WPQ2ListData found for sector: {sector}")
        # Save HTML for debugging
        debug_path = os.path.join(RAW_DIR, f"debug_{sector.replace('/', '_')}.html")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(html)
        return []

    try:
        list_data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"  [ERROR] JSON parse failed for {sector}: {e}")
        return []

    rows = list_data.get("Row", [])
    occupations = []
    for row in rows:
        # Extract NCO code from lookup field
        nco_raw = row.get("NCO_x0020_Code", "")
        # Could be a string, a lookup dict, or a list of lookup dicts
        if isinstance(nco_raw, list) and nco_raw:
            nco_code = nco_raw[0].get("lookupValue", "")
        elif isinstance(nco_raw, dict):
            nco_code = nco_raw.get("lookupValue", "")
        else:
            nco_code = str(nco_raw).strip()

        # Extract sector from lookup field
        sector_raw = row.get("Industry_x002F_Sector_x0028_s_x0", sector)
        if isinstance(sector_raw, list) and sector_raw:
            sector_name = sector_raw[0].get("lookupValue", sector)
        elif isinstance(sector_raw, dict):
            sector_name = sector_raw.get("lookupValue", sector)
        else:
            sector_name = str(sector_raw).strip() or sector

        title = row.get("Title", "").strip()
        sp_id = row.get("ID", "")

        if title:
            occupations.append({
                "title": title,
                "nco_code": nco_code,
                "sector": sector_name,
                "sp_id": sp_id,
            })

    return occupations


def main():
    parser = argparse.ArgumentParser(description="Scrape NCS Portal occupation data")
    parser.add_argument("--resume", action="store_true", help="Skip already-scraped sectors")
    args = parser.parse_args()

    os.makedirs(RAW_DIR, exist_ok=True)

    # Load existing data if resuming
    all_occupations = []
    scraped_sectors = set()
    if args.resume and os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            all_occupations = json.load(f)
        if os.path.exists(SECTORS_FILE):
            with open(SECTORS_FILE, "r", encoding="utf-8") as f:
                scraped_sectors = set(json.load(f))
        print(f"Resuming: {len(scraped_sectors)} sectors already scraped, {len(all_occupations)} occupations loaded")

    ssl_ctx = create_ssl_context()
    total_new = 0

    max_retries = 3

    for i, sector in enumerate(SECTORS):
        if sector in scraped_sectors:
            print(f"[{i+1}/{len(SECTORS)}] Skipping {sector} (already scraped)")
            continue

        occupations = []
        for attempt in range(max_retries):
            if attempt > 0:
                wait = DELAY * (attempt + 1)
                print(f"  Retry {attempt}/{max_retries} after {wait}s...")
                time.sleep(wait)
            print(f"[{i+1}/{len(SECTORS)}] Fetching: {sector}..." + (f" (attempt {attempt+1})" if attempt else ""))
            occupations = fetch_sector(sector, ssl_ctx)
            if occupations or attempt == max_retries - 1:
                break

        print(f"  Found {len(occupations)} occupations")

        if occupations:
            all_occupations.extend(occupations)
            total_new += len(occupations)
            scraped_sectors.add(sector)

            # Save after each sector (resume-safe)
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(all_occupations, f, indent=2, ensure_ascii=False)
            with open(SECTORS_FILE, "w", encoding="utf-8") as f:
                json.dump(sorted(scraped_sectors), f)

        if i < len(SECTORS) - 1:
            time.sleep(DELAY)

    print(f"\nDone. Total: {len(all_occupations)} occupations ({total_new} new)")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
