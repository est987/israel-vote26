# israel-vote26

Knesset 25 (1.11.2022) results by neighbourhood: an interactive Hebrew map (Leaflet), served as a static site.

- `index.html` – the app (single file)
- `data/` – nbhd.json (neighbourhood + estimated-area polygons with vote totals), sites.json (polling sites), meta.json (parties, blocs, towns, national), base.json (outlines)
- `netlify.toml` – Netlify settings (no build step; publish the repo root)
- `build/` – Python scripts that produced `data/` and the page template (for reference)

Deploy: Netlify → Site configuration → Build & deploy → Link repository → this repo, branch `main`, build command empty, publish directory `.`.
Every push to `main` then redeploys the site.
