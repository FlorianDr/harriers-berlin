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

# Deploy: merge to main. .github/workflows/deploy.yml uploads site/ over FTPS to the
# Hetzner webhosting (www325.your-server.de). Run it by hand from the Actions tab with
# "dry run" ticked to see what would change.
```

Route maps on the run pages are static SVGs drawn from a GPX plus OpenStreetMap data by
`assets/routes/tools/route_map.py` — an optional helper run by hand, not a build step. Its README
covers the GPX privacy check, the required OpenStreetMap credit and renaming on change.

Social cards (`site/og/*.jpg`, 1200×630) are rendered from `assets/og/card.html` by
`assets/og/render.sh`, another hand-run helper (headless Chrome + `sips`). Every page sets
`og:image` to its card with width, height and alt text. When a run's day, time, distance, pace or
meeting point changes, update the `RUNS` table in `card.html` and re-render; check them all with
`assets/og/preview.html` (serve the repo root, not `site/`).

`site/sitemap.xml` carries a `lastmod` per page; bump it to the commit date when that page's
content changes (Google only trusts `lastmod` while it stays accurate).

`site/llms.txt` repeats the weekly schedule as plain text for AI crawlers, so update it too when a
run changes or a page is added. Keep its "Information scope" note: the runs are informal, not
organised club events, which matches the disclaimer on the run pages.

Photos are JPEG at widths 640/1024/1600, served with `srcset`. The hero video is a muted H.264 MP4
(`-an -vf scale=960:372 -c:v libx264 -crf 34 -movflags +faststart`); it sits behind a heavy purple
overlay, so it tolerates hard compression.

## Architecture of `site/`

Three hand-written files, no framework:

- **`index.html`** — single page. The five weekly runs are `<article class="fix">` elements whose
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
  It also places the "Upcoming races" marker in the season record (`#season`): races are listed
  oldest first in the HTML, each with `data-race="YYYY-MM-DD"` (the race's last day), and the
  script inserts the marker before the first race on or after today in Berlin, then sets the
  list's `scrollTop` so it opens at the bottom. Without JS the list is complete, just unmarked.
  To add a race, insert its row in date order; when a race is over, add its result (`<span class="rs">N ran</span>`).
- **`impressum.html`** — German legal page (Impressum + Datenschutzerklärung), shares `styles.css`.
- `.htaccess` is the live server config (Apache on Hetzner): one-step redirect to
  `https://berlinharriers.de` (no `www`), security headers including the CSP, `no-cache`, MIME
  types, `Options -Indexes`, blocked dotfiles, the `/mail` shortcut to Hetzner webmail and
  redirects for every URL of the previous site (`/index.htm`, `/impressum.htm`, `/runs.htm`,
  `/membership/index.htm`, `/documents/*.pdf`). Keep the empty `#KONSOLEH AREA` block at the top:
  Hetzner's panel writes its own settings there. `_headers` / `_redirects` are the Cloudflare Pages
  equivalents, kept in sync but not uploaded. Change both together.

## Constraints that are easy to break

- **Privacy promise is load-bearing.** The Datenschutzerklärung states: no cookies, no
  local/session storage, no third-party fonts, maps, embeds or analytics, and that the only script
  reads the clock and sends nothing. That is why no consent banner is needed. Any change that adds a
  CDN, embed (Instagram, YouTube, maps), analytics or storage breaks the legal text. Link out
  instead. If hosting changes, §3 of `impressum.html` (currently names Hetzner) must change too.
- **No inline CSS or JS — the Content-Security-Policy forbids it.** The CSP (in `.htaccess` and
  `_headers`) allows only files from this site: `script-src 'self'; style-src 'self'`, with no
  `'unsafe-inline'`, ever. So no `<style>` blocks, no `style=""` attributes, no inline `<script>`,
  no `on*=""` handlers and no `javascript:` URLs, and `app.js` must not set `style` attributes
  (`element.style.x = …` is fine). Page-specific CSS goes in `styles.css` as a class at the **end
  of the `components` layer** (e.g. `.masthead--compact`, `.notfound`, `.prose--sections`), where it
  wins over the general rules the way an inline style did; scope it with a modifier class rather
  than restyling a shared class such as `.prose`. A new kind of resource needs its CSP directive
  in both files (e.g. a web manifest needs `manifest-src 'self'`).
- **Check visual refactors with before/after screenshots.** When moving CSS or touching headers,
  render each affected page at 390px and 1280px with headless Chrome before and after the change,
  served the same way (both from Apache, or both from `python3 -m http.server`; mixing servers
  changes the render), and compare the PNGs byte for byte. Open any pair that differs. Re-render
  it a few times first: the 404 page's `ch`-based width can flip with font-load timing. Run Chrome
  with `--enable-logging=stderr --v=1` and grep the log for "violates the following Content
  Security Policy" to catch CSP breakage.
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
- **Permissions-Policy must not contain `autoplay=()`** — it would stop the muted hero video.
- **External and PDF links open in a new tab.** Every link to another site (Discord, Strava, maps,
  parkrun, OpenStreetMap, …) or to a PDF, including our own, gets `target="_blank" rel="noopener"`
  plus a visually hidden `<span class="vh"> (opens in a new tab)</span>` inside the link text, so
  screen-reader users are told. Internal pages (`index.html`, `runs/*.html`, `impressum.html`) and
  `mailto:` links stay in the same tab.
- **No AVIF.** It loaded but painted blank in testing; images are JPEG with `srcset`.
- **Voice rules**: composed body copy, warmer headings, exactly two
  jokes on the page (the bakery line and the asparagus line), no emoji in prose — run emoji are
  `aria-hidden` fixture labels only, sentence case, 24-hour times.

## Placeholder content that must not ship as real

- Route SVG shapes are indicative; real geometry should come from Strava GPX.

## Deployment notes

- Hosting is Hetzner webhosting. Deploys run from GitHub Actions with `lftp` from Ubuntu's archive
  over FTPS (TLS forced, certificate and hostname verified; never plain FTP), with `FTP_USERNAME` /
  `FTP_PASSWORD` stored as secrets of the `production` environment. No third-party actions: the
  only one is GitHub's `actions/checkout`. Actions are referenced by version tag and pinned to
  commits in `.github/workflows/actions.lock`. After changing any `uses:` line, run `gh actions-lock`
  (extension `github/gh-actions-lock`) and commit the lockfile; never edit it by hand. The
  `Lockfile` workflow fails when it is stale.
- The deploy is a mirror: anything in the web root that is not in `site/` is **deleted**. Files that
  must live only on the server need an `--exclude-glob` in `deploy.yml`. Manual runs default to a
  dry run that lists the changes.
- After deploying, `curl -sI https://berlinharriers.de | grep -i set-cookie` must print nothing;
  the workflow checks this.
- If the site moves back to Cloudflare, keep **Bot Fight Mode** off (it sets a `__cf_bm` cookie) and **Rocket Loader** off
  (it breaks `app.js`).
