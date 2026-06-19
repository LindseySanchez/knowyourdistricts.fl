"""
scrape_offices_up.py
====================
Scraper for official "Offices Up for Election" pages for Sarasota and Manatee counties.

SAFETY FEATURES (modeled after clean_tracker.py):
- Never blindly overwrites without review.
- Writes to timestamped output files.
- Prints detailed report of parsed offices.
- Flags items needing review (e.g. complex parsing).
- All data tied to source URLs.

Usage:
    python scripts/scrape_offices_up.py

Outputs:
    data/offices_up_sarasota_YYYY-MM-DD.json
    data/offices_up_manatee_YYYY-MM-DD.json
    (Also prints human-readable summary)

Requires:
    pip install -r scripts/requirements.txt
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
import os
import sys

# URLs (official sources - update if changed)
SARASOTA_URL = "https://www.sarasotavotes.gov/181/Offices-up-for-Election"
MANATEE_URL = "https://www.votemanatee.gov/offices-up-for-election/"

def fetch_page(url):
    """Fetch page content with basic error handling."""
    headers = {
        "User-Agent": "knowyourdistricts.fl/0.1 (educational transparency tool; contact via repo)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"ERROR fetching {url}: {e}")
        return None

def parse_sarasota_offices(html):
    """Refined parser for Sarasota offices up page.
    Better structure detection, extracts office type + specific seats/districts where possible.
    Outputs structured dicts for easier use in site data.
    """
    soup = BeautifulSoup(html, "html.parser")
    offices = []
    current_section = "General"

    # More precise: use headings and list items
    for tag in soup.find_all(["h2", "h3", "strong"]):
        text = tag.get_text(strip=True)
        if any(kw.lower() in text.lower() for kw in ["county", "school board", "municipal", "special", "federal", "state"]):
            current_section = text.strip()

    # Collect ONLY specific office entries (strict to avoid nav/footer noise)
    known_office_patterns = ["commissioner districts", "school board districts", "city of", "town of", "district seats", "ward", "at large"]
    for item in soup.find_all(["li", "p"]):
        text = item.get_text(strip=True).lower()
        if not text or len(text) < 10:
            continue
        if any(pat in text for pat in known_office_patterns):
            clean = item.get_text(strip=True)
            if clean.startswith(("-", "•", "–")):
                clean = clean[1:].strip()
            if "judge" in clean.lower() or "retention" in clean.lower():
                continue
            office_type = "Other"
            if "commissioner" in clean.lower():
                office_type = "County Commissioner"
            elif "school board" in clean.lower():
                office_type = "School Board"
            elif "city of" in clean.lower() or "town of" in clean.lower():
                office_type = "Municipal"
            elif "special" in clean.lower() or "cdd" in clean.lower():
                office_type = "Special District"
            offices.append({
                "jurisdiction": "Sarasota County",
                "section": current_section,
                "office_type": office_type,
                "description": clean,
                "seats_or_districts": clean,
                "source": SARASOTA_URL
            })

    # Dedup
    seen = set()
    cleaned = [o for o in offices if (o["description"], o["office_type"]) not in seen and not seen.add((o["description"], o["office_type"]))]
    return cleaned

def parse_manatee_offices(html):
    """Refined parser for Manatee offices up page.
    Improved extraction of office_type and specific seats.
    Filters noise better, structures output for funding/scandal tracking.
    """
    soup = BeautifulSoup(html, "html.parser")
    offices = []
    current_section = "General"

    for tag in soup.find_all(["h2", "h3", "strong"]):
        text = tag.get_text(strip=True)
        if any(kw.lower() in text.lower() for kw in ["commissioner", "school board", "municipal", "special", "fire", "stewardship"]):
            current_section = text.strip()

    # Strict collection for Manatee
    known_office_patterns = ["commissioner", "school board", "city of", "ward", "district seats", "mayor", "fire district", "cdd"]
    for item in soup.find_all(["li", "p"]):
        text = item.get_text(strip=True)
        if not text or len(text) < 10:
            continue
        if text.startswith(("-", "•", "–")):
            text = text[1:].strip()
        lower_text = text.lower()
        if any(x in lower_text for x in ["judge", "retention", "circuit", "maps", "contact"]):
            continue
        if any(pat in lower_text for pat in known_office_patterns):
            office_type = "Other"
            if "commissioner" in lower_text:
                office_type = "County Commissioner"
            elif "school board" in lower_text:
                office_type = "School Board"
            elif "city of" in lower_text or "ward" in lower_text:
                office_type = "Municipal"
            elif "special" in lower_text or "cdd" in lower_text or "fire" in lower_text:
                office_type = "Special / Fire District"
            offices.append({
                "jurisdiction": "Manatee County",
                "section": current_section,
                "office_type": office_type,
                "description": text,
                "seats_or_districts": text,
                "source": MANATEE_URL
            })

    seen = set()
    cleaned = [o for o in offices if (o["description"], o["office_type"]) not in seen and not seen.add((o["description"], o["office_type"]))]
    return cleaned

def write_output(jurisdiction, offices, date_str):
    """Write JSON output safely."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    filename = f"offices_up_{jurisdiction.lower().replace(' ', '_')}_{date_str}.json"
    filepath = os.path.join(data_dir, filename)

    payload = {
        "meta": {
            "jurisdiction": jurisdiction,
            "scraped_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "source": offices[0]["source"] if offices else "unknown",
            "note": "Parsed from official SOE page. Review for completeness. This is bootstrap data for knowyourdistricts.fl."
        },
        "offices": offices
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return filepath

def print_report(jurisdiction, offices, filepath):
    """Print human readable report like clean_tracker.py."""
    print("\n" + "=" * 70)
    print(f"SCRAPE REPORT: {jurisdiction}")
    print("=" * 70)
    print(f"Total offices parsed: {len(offices)}")
    print(f"Output file: {filepath}")

    # Group by section for summary
    sections = {}
    for o in offices:
        sec = o.get("section", "Unknown")
        sections.setdefault(sec, []).append(o["description"])

    print("\n--- By Section ---")
    for sec, items in list(sections.items())[:6]:  # limit for readability
        print(f"  {sec}: {len(items)} items")
        for item in items[:2]:
            print(f"    - {item[:80]}")

    if len(offices) == 0:
        print("  [WARNING] No offices parsed - page structure may have changed. Needs manual review.")

    print("\n" + "=" * 70)
    print("REVIEW: Open the JSON and cross-check against the live page.")
    print("=" * 70)

def main():
    date_str = datetime.now().strftime("%Y-%m-%d")

    print("Starting scrape for Offices Up for Election 2026...")

    # Sarasota
    print("\nFetching Sarasota...")
    sarasota_html = fetch_page(SARASOTA_URL)
    sarasota_offices = parse_sarasota_offices(sarasota_html) if sarasota_html else []
    sarasota_file = write_output("Sarasota", sarasota_offices, date_str)
    print_report("Sarasota County", sarasota_offices, sarasota_file)

    # Manatee
    print("\nFetching Manatee...")
    manatee_html = fetch_page(MANATEE_URL)
    manatee_offices = parse_manatee_offices(manatee_html) if manatee_html else []
    manatee_file = write_output("Manatee", manatee_offices, date_str)
    print_report("Manatee County", manatee_offices, manatee_file)

    print("\n✅ Scrape complete. Review the generated JSON files in data/ before using in the site.")
    print("Next: Run `python scripts/scrape_offices_up.py` again after any page updates.")

if __name__ == "__main__":
    main()
