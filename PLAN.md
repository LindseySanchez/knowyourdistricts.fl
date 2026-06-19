# knowyourdistricts.fl — Execution Plan (First 3 Recommendations)

**Status**: Execution in progress / partially complete (exit plan + first 3 recs tackled: Arch/Tech data move primary, Data sync, UI polish). See updates in index.html + data/*.json + README.
**Context**: User approved proceeding with the first 3 categorized recommendations after plan mode review. Minor polish + commit already done (see last git commit). No changes without prior explicit approval; now executing.

## The First 3 Recommendations (categorized)

### 1. Arch/Tech
- **Primary**: Move the large inline `districts` const (full enriched data for local + statewide Gov/Ag with donors, keyIssues, pollingSources, funding details) out of index.html JS into a proper maintainable JSON file under `data/` (e.g. `districts_enriched_2026-06-19.json` or update `districts_seed_expanded_2026-06-19.json`).
- Load districts data asynchronously via fetch (parallel to scraper JSONs).
- Improve scraper JSON integration: better tie `offices_up_*.json` into the districts model (e.g. augment or show relevant offices per district when available; currently only raw demo list).
- Groundwork for future real GeoJSON: add support in data model and renderDistrict for optional geojson paths or external load (don't break current approx polys yet).
- Keep single-file static-friendly for now; no Node required yet.
- Update load/init logic and any comments.

### 2. Data/Accuracy
- Sync the complete rich statewide + local district data (including Jeff Yass/Club for Growth/Seminole Tribe/Steve Wynn for Donalds; Farm Bureau etc for Simpson; specific voting excerpts; Olle and other challengers; Fishback crowds/GenZ/energy notes + heavy poll skepticism) fully into the new JSON file.
- Expand/enrich a few more candidate entries and funding where consistent with prior verifications (keep non-partisan, sourced).
- Ensure scraper output (Sarasota/Manatee offices) is referenced/usable; consider a light merge helper or notes in panel.
- Re-verify key facts against sources via process (use sub-agent review where appropriate). Maintain disclaimers.
- Update meta dates, README, last-updated text.
- Add more explicit candidate entries for key races if gaps (e.g. additional known challengers in seeded races) without fabricating.

### 3. UI/UX
- Enhance sidebar/panel rendering: ensure all fields (keyIssues, pollingSources, full topContributors, limitFlags, fundingNotes) render cleanly for both local districts and the special statewide combined panel.
- Improve filter behavior and scraper button (perhaps allow filtering the map or searching offices).
- Add minor responsive polish (sidebar/grid on narrow screens) and visual tweaks for heavy-focus statewide (keep prominent).
- Better empty/loading states for JSON fetches.
- Keep heavy skepticism messaging and "HEAVY FOCUS" banners.
- Ensure clicking map + "Statewide (Gov + Ag)" button both produce rich candidate/funding views.
- Optional: make scraper list items clickable to populate details where possible.

## Execution Approach
- Use todo tracking for steps.
- Implement Arch/Tech data extraction + load first (highest leverage).
- Then data sync + accuracy pass.
- Then UI tweaks.
- After changes: run local server test, git status + diff review (per user Git rules: status/review before any commit/push).
- Use verification sub-agents / review skill for accuracy/bias checks on data/UI.
- Do not push until user explicitly approves.
- Preserve all existing functionality; site must remain runnable via python -m http.server or simple open.
- Update README "Next" section and note plan execution in progress.

## Verification & Safety
- All data remains tied to cited sources.
- No invention of donors, numbers, or positions.
- Heavy emphasis on "verify at source".
- Post-edit: sub-agent check for correctness, then human (user) review.

Built with Grok. User: "exit plan mode and execute". Let's implement the first 3.

Date: 2026-06-19
