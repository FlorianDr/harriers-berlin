# Berlin Harriers

The website of **[Berlin Harriers e.V.](https://berlinharriers.de)** — a free, English-speaking
running club in Berlin with four runs a week, no fees, no registration and no set pace.

## The site

A single static page plus an Impressum. Hand-written HTML and modern CSS, one small script, no
framework, no build step, no dependencies.

- **No cookies, no storage, no third-party requests.** Fonts are self-hosted, maps are links rather
  than embeds, and there is no analytics — so the site needs no consent banner. Keeping it that way
  is the main constraint on any contribution.
- **Works without JavaScript.** The only script highlights the next run, computed in Berlin time.
  Every run is in the HTML regardless.
- **Modern CSS:** `oklch()` and `light-dark()` colour tokens, cascade layers, container queries,
  scroll-driven animations. Targets the latest version of each major browser.

### Run it locally

```bash
cd site
python3 -m http.server 8899
# open http://localhost:8899
```

### Deploy

Any static host works. The production setup is Cloudflare Pages with `site/` as the output
directory and no build command:

```bash
wrangler pages deploy site --project-name=berlinharriers
```

Keep Cloudflare's Bot Fight Mode and Rocket Loader off: the first sets a cookie, which would break
the privacy promise, and the second breaks the next-run script.

## Repository layout

| Path | Contents |
|---|---|
| `site/` | Everything that is deployed |
| `assets/` | Source material: master logo, route SVGs |


## Placeholder content

Some content is not real yet and is marked as such:

- **The season record** on the homepage is invented placeholder data.
- **The photographs and the hero video are placeholders.** They depict no real people, the site
  footer says so, and they will be replaced with real photos of club runs.
- **The route maps** are indicative shapes, not traced from GPS data.


## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Contributions from members are especially welcome — real
photos, accurate route data and race results most of all.

## Licence

- **Code** (HTML, CSS, JavaScript, scripts): [MIT](LICENSE).
- **Fonts:** [Alfa Slab One](site/fonts/OFL-AlfaSlabOne.txt) and
  [Archivo](site/fonts/OFL-Archivo.txt), both under the SIL Open Font License 1.1.
- **The Berlin Harriers name, crest and logo** are the club's and are **not** covered by the MIT
  licence. Please don't reuse them for anything that isn't Berlin Harriers.
- **Club documents** (the Satzung and Code of Conduct PDFs) are published by the club for
  information and are not open-licensed.
