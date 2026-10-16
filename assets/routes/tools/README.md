# Route maps

`route_map.py` turns a run's GPX into the street-map image shown on its run page
(`site/routes/<run>-map.svg`), and optionally the route-only drawing used on the home page
schedule card. It is a helper you run by hand when a route changes — not a build step. It needs
only Python 3 (standard library) and a network connection to fetch OpenStreetMap data.

## Adding or updating a route

1. **Export the GPX from Strava.** Open the route, click **⋯ → Export GPX**. Use a *route*
   export where you can; a recorded *activity* also works but see the privacy check below.

2. **Privacy check — this repository is public.**
   - Route exports name the route's author and link their Strava profile. Never commit that:
     pass `--clean-gpx` to write a copy with the author block, timestamps and sensor data removed.
   - A recorded activity can start or end at someone's home. Make sure both ends are public
     places (the meeting point, the café) before drawing or committing it.

3. **Generate the map** (from the repository root):

   ```bash
   python3 assets/routes/tools/route_map.py ~/Downloads/route.gpx site/routes/tuesday-track-map.svg \
     --title "Tuesday Track" \
     --clean-gpx assets/routes/tuesday-track.gpx \
     --route-svg site/routes/tuesday-track.svg "Tuesday Track: …"
   ```

   Options:
   - `--finish` — mark the finish with a ring, for routes that don't end where they start.
   - `--labels FILE` — place labels such as rivers or parks; see `../*.labels.txt` for the format.
     Coordinates are in the 200×150 viewBox. Run once without labels, look, then place them.
   - `--osm-cache FILE` — keep the Overpass response for re-runs. It is several MB; keep it out of
     git (a scratch folder is fine).

   The Overpass API is often busy; the script retries with backoff and falls back to mirrors.

4. **Use it on the run page.** Copy the `<figure class="route route--map">` block from
   `site/runs/monday-duck.html` and change the `src`, `alt` and caption. Keep the
   `© OpenStreetMap contributors` link in the map corner — the ODbL licence requires visible
   attribution next to the map. Paste the route-only `<path>` and `<circle>`s into the run's
   `<svg class="rt">` on `site/index.html` (stroke width 3.5 there).

## Things to know

- **Renaming on change.** `_headers` caches `/routes/*` for a year as immutable. When a map
  changes after it has been deployed, give it a new filename (e.g. `monday-duck-map-v2.svg`) and
  update the `src`.
- **Colours are copied.** An `<img>` can't see the page's CSS variables, so `STYLE` in the script
  mirrors the tokens in `site/styles.css`. If the palette changes, change both and regenerate.
- **No third-party requests.** The map is drawn once into a static file. The published page never
  contacts OpenStreetMap, which keeps the privacy statement in `impressum.html` true. Don't swap
  this for embedded tiles or a map widget.
- **Reproducing the current maps:** the committed Monday and Thursday maps come out byte-for-byte
  from the commands below, given the same OpenStreetMap data (it changes over time, so a fresh
  fetch will differ slightly).

  ```bash
  python3 assets/routes/tools/route_map.py assets/routes/monday-duck.gpx site/routes/monday-duck-map.svg \
    --title "Monday Duck" --labels assets/routes/monday-duck.labels.txt \
    --route-svg site/routes/monday-duck.svg "Monday Duck: an 8.4 km loop through the Tiergarten and along the Spree"
  python3 assets/routes/tools/route_map.py assets/routes/thursday-swan.gpx site/routes/thursday-swan-map.svg \
    --title "Thursday Swan" --finish --labels assets/routes/thursday-swan.labels.txt \
    --route-svg site/routes/thursday-swan.svg "Thursday Swan: a 7.1 km run along the Landwehrkanal, finishing at La Maison"
  ```
