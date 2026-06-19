# knowyourdistricts.fl

Interactive map + transparent tracker for upcoming local elections in Sarasota, Manatee, Lakewood Ranch, Myakka and surrounding areas.

**Goal**: Give people clear, sourced information on:
- Which districts are up
- Incumbents vs challengers
- Detailed funding sources (especially development money)
- Policy positions and public record
- Signs of influence or contribution limit games

## Current Status
- Early starter (June 19, 2026) — going wild on seeding + funding + scraper
- Browser-native (Leaflet via CDN) — open `index.html` directly
- Seeded districts: Sarasota Co Comm D2/D4, Manatee Co Comm D2/D6 (open), City of Sarasota At-Large, Manatee School Board D2/D4/D5, Sarasota School Board, additional city examples
- **Funding deep-dive** started on county commission races (structured topContributors, categories, financeLinks, limitFlags)
- Scraper further refined: stricter keyword filtering, better office_type/seats extraction, less nav noise. Re-ran multiple times. Still recommend manual review of JSON vs pages (pages are dynamic).
- **More depth added**: Specific scandals/lobbyist/dev money - Neunder PAC $95k from Neal/Culverhouse/Benderson/Jensen + post-vote Siesta Key Brown LLCs (refunded some); Smith dev history $53k+ + budget votes + Siesta Key hotel opposition vs past funding. Siesta Key D2 focus expanded (community plan, Village ties, hotel fights).
- Governor: Added Fishback emphasis - crowds/Gen Z energy vs Byron; note that his polls/internal data disagree with mainstream AIF/Emerson (which favor Donalds heavily). Project skepticism on "mainstream GOP" polls.
- Ag Comm: Policy depth on marshlands/dev vs Simpson record.
- **Minor polish applied**: Olle in narrative, outdated comment fixed, financeLinks consistent, name formatting, extended showDistrictDetails for keyIssues/pollingSources, load comment fixed, statewide rich data synced to seed JSON. All core fixes + re-verified with subagents.
- Heavy disclaimers + source links on everything (polls especially treated with skepticism)

## How to run (today)
1. Open `index.html` in any browser
2. Click the colored districts on the map
3. Sidebar shows incumbents, candidates, funding notes

## Next (following approved plan)
- Improve scraper parsing (reduce noise) + add candidate/ finance scraping
- Real GeoJSON from county portals
- Python + GH Actions automation
- More funding depth + agent verification passes
- Governor + Ag Comm sections
- Full site framework when Node available

## Running the scraper (new!)
1. cd knowyourdistricts.fl
2. python -m pip install -r scripts/requirements.txt
3. python scripts/scrape_offices_up.py
4. Review generated data/offices_up_*.json against the live pages
5. (Optional) Use the data to update index.html districts list

See scripts/scrape_offices_up.py for safety patterns (modeled after clean_tracker.py).

## Principles
- Primary sources first
- No poll worship
- Aggressive but factual funding transparency
- Check our work with agents + human review
- Shine light on all influence, no matter the side

Data is for informational purposes only. Always verify at official county and state election sites.

---

Built with Grok. Plan approved. Let's get wild (and accurate).
