"""Download PLFS 2023-24 Annual Report PDF from mospi.gov.in.

For v1, we extract occupation-level employment data from the Annual Report PDF tables
(Statement 16/17 — % distribution by NCO-2015 division/subdivision).

Usage:
    python scrape/download_plfs.py
"""

import os
import urllib.request

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw", "plfs")

DOWNLOADS = {
    "AnnualReport_PLFS2023-24L2.pdf": "https://www.mospi.gov.in/sites/default/files/publication_reports/AnnualReport_PLFS2023-24L2.pdf",
    "Press_note_AR_PLFS_2023_24.pdf": "https://www.mospi.gov.in/sites/default/files/press_release/Press_note_AR_PLFS_2023_24_22092024.pdf",
}


def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    for filename, url in DOWNLOADS.items():
        filepath = os.path.join(RAW_DIR, filename)
        if os.path.exists(filepath):
            print(f"Already downloaded: {filename}")
            continue

        print(f"Downloading: {filename}...")
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            with open(filepath, "wb") as f:
                f.write(data)
            print(f"  Saved: {filepath} ({len(data):,} bytes)")
        except Exception as e:
            print(f"  [ERROR] Failed to download {filename}: {e}")

    print("\nDone. Files saved to:", RAW_DIR)
    print("\nNext step: Extract Statement 16/17 tables from the PDF.")
    print("Consider using tabula-py or camelot for PDF table extraction.")


if __name__ == "__main__":
    main()
