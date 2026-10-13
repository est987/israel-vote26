# Handover: Israel voting map (Knesset 25 by neighbourhood)

Last update: 2026-10-13, build `2026-10-13 22:15` (shown as "גרסה …" at the bottom of the national-results panel).

## Where things are

| What | Where |
|---|---|
| Live site | https://israel-vote26.netlify.app (custom domain israel-vote26.com) |
| Repository | https://github.com/est987/israel-vote26 (branch `main`) |
| Deploy | Netlify project `israel-vote26`, linked to the repo. Every push to `main` auto-deploys in about a minute. No build command, publish directory `.` |
| Claude artifact (preview) | Same page, published as the artifact "מפת הצבעה לפי שכונות". It cannot download files or load tiles, so it's a preview only. |
| Source template | `build/app.src.html` (+ `build/leaflet.css` inlined) → `python3 build/make.py` writes `index.html` |
| Data build | `build/build.py` (imports `match.py`, `match2.py`, `pseudo.py`), then `build/base.py` → `data/*.json` |

## Repo layout

- `index.html`: the whole app (Leaflet 1.9.4 from cdnjs, ExcelJS 4.4.0 lazy-loaded from cdnjs on export).
- `data/nbhd.json`: 2,966 neighbourhood polygons (MAPI layer) + 1,112 pseudo-areas, with vote vectors.
- `data/sites.json`: 4,175 polling sites (one per town + cluster code) with location, confidence, boxes and votes.
- `data/meta.json`: parties, blocs, towns (totals, unplaced votes), national totals and double envelopes.
- `data/base.json`: Natural Earth land and lakes, plus town outlines.
- Vote vector layout everywhere: `[eligible, voters, invalid, valid, party_0 … party_12]`.

## Data sources (raw inputs are not in the repo)

1. Neighbourhoods: MAPI "שכונות" layer via over.org.il (GeoJSON, WGS84, 2,966 features, 174 towns). Key = feature index (`nbr_id` is null for ~half).
2. Results: CEC Knesset 25 by ballot box, `expb.csv` (12,545 rows; totals match the official result exactly).
3. Locations: GovMap "קלפיות כנסת 26" via over.org.il (12,018 points), plus Knesset 24 geocoded boxes from GitHub `JacobWeinbren/Israel-Data` (`output/locations/24.tsv`). The 2012 `polling.xls` was not used.
4. Natural Earth (`nvkelso/natural-earth-vector`) for land and lakes.

## Method decisions (also in the app's "מקורות ושיטה")

- **Locating K25 boxes:** resolved per site (town + ריכוז). Evidence weights: exact K26 town+box = 4, K24 geocode = 2, K26 base number = 1, K26 cluster = 1. Pools within 80 m; heaviest wins; the official K26 point is preferred.
  - 99.3% of votes are placed; 0.7% (91 boxes) stay at town level.
  - The "ברזל" ID is NOT stable between elections, so it's not used.
- **Uncertainty:** an area is flagged (dashed orange) when more than 30% of its votes come from sites whose candidate locations disagree on the neighbourhood.
- **Pseudo-areas** for sites outside the layer:
  - Voronoi cells in ITM (EPSG:2039), capped at 600 m, minus real neighbourhoods, clipped to land.
  - A town with ≤4 sites becomes one area; bigger towns are split by k-means into groups of ~4, named "<town> — אזור N" (north to south).
- **Town names:** taken from the K26 list (the CEC file strips hyphens and brackets).
- **Parties:**
  - Labor + Meretz are merged as **הדמוקרטים**.
  - Blocs: coalition = Likud, RZ, Shas, UTJ; opposition = Yesh Atid, National Unity, Yisrael Beiteinu, Democrats, **Jewish Home**; Arab parties = Ra'am, Hadash-Ta'al, Balad; others = small lists.
- **"רוב גושים" (default colouring):** coalition − (opposition + Arab parties), in points. Red = coalition, blue = opposition (RdBu-like, steps 10/25/50).
- **Party colours** stay within their bloc's family (warm / blue / green / grey), with ΔE checked in both themes.
- **Turnout** = voters ÷ eligible at the box. Double envelopes (458,714 votes, 9.6%) have no location: they count in national totals only, so local turnout reads slightly low.
- **Totals check:** areas + unplaced + double envelopes = 4,764,742 valid votes.

## Features (all on the live site)

- **Colour by:** bloc majority (default), leading party, turnout, party share (multi-select sums), bloc share.
- **Map:** basemap switch (outlines / OpenStreetMap / Esri satellite; keyless, falls back to outlines if blocked). Polling sites off by default. Outlines hidden below zoom 10.5.
- **Filters (סינון):** a turnout range and a bloc-share range (dual sliders) plus leading-party chips. They apply only after **עדכן**.
- **List (רשימה) scope:** all / a town / **לפי התצוגה במפה** (areas in the current map view, updates on pan) / **לפי מרחק ממיקום** (radius around a map tap, geolocation or pasted coordinates).
- **List actions:**
  - **ייצוא לאקסל:** xlsx via ExcelJS; RTL; colour-coded margin and leading-party cells, data bars, info sheet. Falls back to CSV.
  - **העתקת ישובים ל-Word:** an HTML table on the clipboard.
- **שכונות קרובות:** N nearest, or all within a radius in km. Exact point-to-polygon distance; can respect filters; numbered on the map; **העתקה** copies readable lines.
- **Detail panel:** KPIs, bloc bar, party bars grouped by bloc with town and national markers, location-quality note, compare up to 4 places.
- Phone: three tabs (list / map / details).

## How to change and deploy

1. Edit `build/app.src.html` (keep `const BUILD='…'` updated) → `python3 build/make.py`.
2. Test headless (Playwright + Chromium). Route `cdnjs …/leaflet.min.js` and `…/exceljs.min.js` to npm copies, and abort tile, font and CDN hosts. Check at desktop and at 390×844.
3. `git commit` and `git push origin main` → Netlify deploys.
4. Verify live: a cached fetch can show an old page, so check a file added in that push or the "גרסה" line.
5. Data changes: re-run `build.py` then `base.py`; the raw inputs must be re-uploaded first.

## Open issues and ideas

- Pseudo-area radius (600 m) is a judgement call; clipping to municipal boundaries (גבולות שיפוט) would be better if that layer is provided.
- The location-confidence tiers are a best effort without an official K25 location list. The CEC's K25 list would make the match exact.
- Bloc definition for "רוב גושים" counts Arab parties with the opposition. Changing it is one line (`marginOf`).
- The artifact preview can't download files. Netlify is the real target, or add the artifact `downloads` capability if needed.
- Possible next steps: comparison with Knesset 26 results when available, a per-town summary table, shareable URL state (`#token` only in the artifact).
