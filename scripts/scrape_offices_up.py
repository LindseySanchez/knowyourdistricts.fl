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
    """Improved parser for Sarasota offices up page.
    Uses document-order traversal to correctly track sections.
    Captures exact lists from Federal/State/County/Municipalities/Special Districts.
    Filters judicial noise but keeps relevant offices. Better office_type and section assignment.
    """
    soup = BeautifulSoup(html, "html.parser")
    offices = []
    current_section = "General"

    # Known top-level section headers (from live page)
    section_headers = {
        "federal": "Federal",
        "state": "State",
        "county": "County",
        "judicial": "Judicial",
        "municipalities": "Municipalities",
        "special districts": "Special Districts"
    }

    # Junk patterns to skip (addresses, phones, nav, footers, voter services, external)
    junk_patterns = [
        "register to vote", "my voter record", "vote by mail", "early voting",
        "find my precinct", "coming elections", "site map", "contact us",
        "accessibility", "copyright", "phone:", "fax:", "building", "sarasota office",
        "venice office", "north port office", "site links", "subscribe",
        "learn more", "stay connected", "terrace building", "robert l. anderson",
        "biscayne plaza", "address", "mailing", "hours", "external link"
    ]

    # Process in document order
    for tag in soup.find_all(["h2", "h3", "strong", "li", "p"]):
        text = tag.get_text(strip=True)
        if not text or len(text) < 5:
            continue
        ltext = text.lower()

        # Update current section on headings
        if tag.name in ["h2", "h3", "strong"]:
            for key, val in section_headers.items():
                if key in ltext:
                    current_section = val
                    break
            continue

        # STRICT: only true office <li> bullets (prevents p-header leakage like "Judicial", "Special Districts")
        if tag.name != "li":
            continue

        # Skip exact section headers that leak as items
        if text.strip() in ["Federal", "State", "County", "Judicial", "Municipalities", "Special Districts"]:
            continue

        # Only collect from desired sections (skip Judicial, Federal for now to focus on local)
        if current_section in ["Judicial", "Federal"]:
            continue
        if "judge" in ltext or "retention" in ltext:
            continue

        # Skip junk
        if any(jp in ltext for jp in junk_patterns):
            continue

        # Collect offices that match patterns (stricter: no permissive current_section fallback)
        is_office = any(pat in ltext for pat in [
            "commissioner districts", "charter review board", "hospital board",
            "school board districts", "city of", "town of", "district seats", "district seat",
            "at large", "cdd", "improvement district", "fire control", "water district",
            "park and recreation district", "stewardship", "community development"
        ])

        if not is_office:
            continue

        clean = text
        if clean.startswith(("-", "•", "–")):
            clean = clean[1:].strip()

        # Classify office_type using section + text
        office_type = "Other"
        lt = clean.lower()
        if "commissioner districts" in lt or "county commissioner" in lt:
            office_type = "County Commissioner"
        elif "charter review" in lt:
            office_type = "Charter Review Board"
        elif "hospital board" in lt:
            office_type = "Hospital Board"
        elif "school board" in lt:
            office_type = "School Board"
        elif current_section == "Municipalities" or "city of" in lt or "town of" in lt or "at large" in lt:
            office_type = "Municipal"
        elif current_section == "Special Districts" or "cdd" in lt or "district" in lt or "fire" in lt or "water" in lt:
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
    cleaned = [o for o in offices if (o["description"], o["section"]) not in seen and not seen.add((o["description"], o["section"]))]
    return cleaned

def parse_manatee_offices(html):
    """Improved parser for Manatee offices up page.
    Uses document-order traversal for correct sections.
    Handles top-level sections and sub (Fire, CDD, Municipal cities).
    Accurate classification, better filtering, preserves context.
    """
    soup = BeautifulSoup(html, "html.parser")
    offices = []
    current_section = "General"
    current_sub = None

    # Known sections from live page
    section_map = {
        "federal": "Federal",
        "state": "State",
        "county": "County",
        "judicial": "Judicial",
        "special districts": "Special Districts",
        "municipalities": "Municipalities"
    }
    sub_map = {
        "fire districts": "Fire Districts",
        "community development districts": "Community Development Districts (CDD)",
        "stewardship": "Stewardship Districts",
        "special districts": "Special Districts"
    }

    for tag in soup.find_all(["h2", "h3", "h4", "li", "p"]):
        text = tag.get_text(strip=True).replace('\xa0', ' ').strip()
        if not text or len(text) < 4:
            continue
        ltext = text.lower()

        # Update section on h2/h3/h4 + reset sub properly (for footer Address etc after last city)
        if tag.name in ["h2", "h3", "h4"]:
            for key, val in section_map.items():
                if key in ltext:
                    current_section = val
                    current_sub = None
                    break
            for key, val in sub_map.items():
                if key in ltext:
                    current_sub = val
                    break
            # City headers under Municipalities
            if "city of" in ltext or "town of" in ltext:
                current_sub = text
            elif tag.name in ("h2", "h4") and current_sub:
                # reset sub on non-city/non-sub h4/h2 (e.g. Address, Mailing, Stay Connected)
                if not any(x in ltext for x in ["city of", "town of", "fire district", "community development", "stewardship", "special district"]):
                    current_sub = None
            continue

        # STRICT: only true office <li> bullets (prevents collecting nav/footer p/li junk)
        if tag.name != "li":
            continue

        # Skip judicial and low priority
        if current_section in ["Judicial", "Federal"]:
            continue
        if "judge" in ltext or "retention" in ltext or "contact" in ltext or "search" in ltext:
            continue

        # Junk filter for nav, footers, external, subscribe, enenhtes, addresses, phones etc.
        junk_patterns = [
            "register to vote", "my voter record", "vote by mail", "early voting", "find my precinct",
            "site map", "contact us", "accessibility", "copyright", "phone:", "fax:", "subscribe",
            "stay connected", "learn more", "external link", "enenhtes", "©", "address", "mailing",
            "hours", "supervisor", "employment", "election worker", "public records", "for voters",
            "for candidates", "political parties", "voter resources", "elections data", "become a candidate",
            "calendar of reporting", "florida elections commission", "florida commission on ethics"
        ]
        if any(jp in ltext for jp in junk_patterns):
            continue
        if any(x in text for x in [" Blvd", "Suite 108", "PO Box", "FL 342", "T:", "F:", "(941)"]) or text.count(":") > 2:
            continue

        # Collect relevant offices (stricter: keywords only, no or current_section fallback)
        # For Municipalities, require actual office keywords under a city sub
        if current_section == "Municipalities":
            is_relevant = current_sub and any(p in ltext for p in ["mayor", "commissioner", "city council", "ward"])
        else:
            is_relevant = any(p in ltext for p in ["u.s. senate", "u.s. house", "governor", "attorney general", "chief financial", "commissioner of agriculture",
                "state senate", "state house", "board of county", "school board", "mayor", "city council", "commissioner", "ward",
                "mosquito", "soil & water", "fire district", "cdd", "stewardship", "trailer estates", "park & recreation"])

        if not is_relevant:
            continue

        # Classify
        office_type = "Other"
        lt = ltext
        if "u.s. senate" in lt or "u.s. house" in lt:
            office_type = "Federal"
        elif any(k in lt for k in ["governor", "attorney general", "chief financial officer", "commissioner of agriculture", "state senate", "state house"]):
            office_type = "State"
        elif "board of county commissioners" in lt or ("county commissioner" in lt and "ward" not in lt):
            office_type = "County Commissioner"
        elif "school board" in lt:
            office_type = "School Board"
        elif "supreme" in lt or "district court" in lt or "circuit" in lt or "county judge" in lt:
            office_type = "Judicial"
        elif "fire district" in lt:
            office_type = "Fire District"
        elif "cdd" in lt or "community development" in lt:
            office_type = "Community Development District (CDD)"
        elif "stewardship" in lt:
            office_type = "Stewardship District"
        elif "mosquito" in lt or "soil & water" in lt:
            office_type = "Special District"
        elif current_section == "Municipalities" or "mayor" in lt or "city council" in lt or ("ward" in lt and "commissioner" in lt):
            office_type = "Municipal"
        elif "commissioner" in lt and current_section == "Municipalities":
            office_type = "Municipal"

        desc = text
        if current_sub and current_section == "Municipalities":
            desc = f"{current_sub}: {text}"

        offices.append({
            "jurisdiction": "Manatee County",
            "section": current_section,
            "subsection": current_sub,
            "office_type": office_type,
            "description": desc,
            "seats_or_districts": text,
            "source": MANATEE_URL
        })

    # Dedup
    seen = set()
    cleaned = [o for o in offices if (o["description"], o["section"]) not in seen and not seen.add((o["description"], o["section"]))]
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
