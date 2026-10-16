# AGENTS.md

Guidance for AI coding agents working in this repository.

## What this is

The website for **Berlin Harriers e.V.**, a free, English-speaking running club in Berlin.

- `site/` — the deployable static site. Everything served lives here.
- `assets/` — source material (master logo, route SVGs). `site/` holds the optimised copies
  actually served.

This is a public repository. Everything committed is world-readable: never commit `.wrangler/` or anything identifying club members beyond what the legally required Impressum
already publishes.

## Commands

There is no build step, no package manager, no tests and no linter.

```bash
# Preview locally
cd site && python3 -m http.server 8899

# Syntax-check the only script
node --check site/app.js

# Deploy (Cloudflare Pages project "berlinharriers", output dir = site/)
wrangler pages deploy site --project-name=berlinharriers
```

Route maps on the run pages are static SVGs drawn from a GPX plus OpenStreetMap data by
`assets/routes/tools/route_map.py` — an optional helper run by hand, not a build step. Its README
covers the GPX privacy check, the required OpenStreetMap credit and renaming on change.

Photos are JPEG at widths 640/1024/1600, served with `srcset`. The hero video is a muted H.264 MP4
(`-an -vf scale=960:540 -c:v libx264 -crf 34 -movflags +faststart`); it sits behind a heavy purple
overlay, so it tolerates hard compression.

## Architecture of `site/`

Three hand-written files, no framework:

- **`index.html`** — single page. The four weekly runs are `<article class="fix">` elements whose
  `data-day` / `data-time` / `data-label` / `data-where` attributes are the data source for the
  script. The schedule must stay complete in the HTML — the page has to work with JS disabled.
  Structured data is **microdata attributes, not JSON-LD**, deliberately (no `<script>` beyond
  `app.js`).
- **`styles.css`** — organised as `@layer tokens, base, layout, devices, components, motion`. All
  colour is `oklch()` tokens defined once via `light-dark()` in `:root`; never add a colour that
  only exists inside a media query or `[data-theme]` block. Layout switches use **container
  queries** at `46rem` on `.fixtures` (wide table vs. scroll-snap carousel), not viewport queries.
- **`app.js`** — the only JavaScript. Computes the next run in **Europe/Berlin** via `Intl` (not the
  visitor's clock), highlights that row, fills the sticky band and `[data-next-day]` spans, and sets
  the carousel's `scrollLeft` directly. Never use `scrollIntoView` there — it scrolls the page.
- **`impressum.html`** — German legal page (Impressum + Datenschutzerklärung), shares `styles.css`.
- `_headers` / `_redirects` are Cloudflare Pages config; `.htaccess` is the Apache equivalent.

## Constraints that are easy to break

- **Privacy promise is load-bearing.** The Datenschutzerklärung states: no cookies, no
  local/session storage, no third-party fonts, maps, embeds or analytics, and that the only script
  reads the clock and sends nothing. That is why no consent banner is needed. Any change that adds a
  CDN, embed (Instagram, YouTube, maps), analytics or storage breaks the legal text. Link out
  instead. If hosting changes, §3 of `impressum.html` (currently names Hetzner) must change too.
- **Fixture-row hover**: the purple wipe is a `background-size` transition on the row itself.
  Don't move it to a pseudo-element — text colour and fill must live on the same element or the
  row turns white-on-white. Links inside a hovered row must switch to volt.
- **Volt (`--volt`) fails on white (1.61:1).** It only appears on purple, on ink, or as a fill with
  dark ink text. Use `--volt-ink` for volt-coloured text on light grounds.
- **Alfa Slab One has one weight** — `font-synthesis: none`, never below ~24px, hierarchy via size
  and case, not weight.
- **Never subset or modify `AlfaSlabOne-Regular.woff2`.** Its OFL licence reserves the name
  "Alfa Slab", and subsetting makes it a Modified Version that may not use that name (OFL FAQ 2.6,
  3.8). It is the upstream Google Fonts TTF compressed to WOFF2 and nothing else. Archivo has no
  reserved name, so its subset is fine.
- **External links open in a new tab.** Every link to another site (Discord, Strava, maps,
  parkrun, OpenStreetMap, …) gets `target="_blank" rel="noopener"` plus a visually hidden
  `<span class="vh"> (opens in a new tab)</span>` inside the link text, so screen-reader users are
  told. Internal links (`index.html`, `runs/*.html`, `impressum.html`, the PDFs) and `mailto:`
  links stay in the same tab.
- **No AVIF.** It loaded but painted blank in testing; images are JPEG with `srcset`.
- **Voice rules**: composed body copy, warmer headings, exactly two
  jokes on the page (the bakery line and the asparagus line), no emoji in prose — run emoji are
  `aria-hidden` fixture labels only, sentence case, 24-hour times.

## Placeholder content that must not ship as real

- The **season record** (`#season`) is invented and marked "PLACEHOLDER DATA — REPLACE BEFORE
  LAUNCH" in the source.
- The photos and hero video are placeholders, to be replaced with real club photography; the footer
  says so.
- Route SVG shapes are indicative; real geometry should come from Strava GPX.

## Deployment notes

- On Cloudflare, keep **Bot Fight Mode** off (it sets a `__cf_bm` cookie) and **Rocket Loader** off
  (it breaks `app.js`). After deploying, `curl -sI <url> | grep -i set-cookie` must print nothing.
- Don't open crawlers on the production domain until the season record holds real fixtures.
