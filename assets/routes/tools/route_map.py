#!/usr/bin/env python3
"""Draw a run's route on a street map, as a self-hosted SVG image.

    python3 assets/routes/tools/route_map.py assets/routes/thursday-swan.gpx \
        site/routes/thursday-swan-map.svg --title "Thursday Swan" --finish \
        --labels assets/routes/thursday-swan.labels.txt

Street, path, water and railway data comes from OpenStreetMap via the Overpass API,
fetched once here and drawn into the SVG — the published page never contacts
OpenStreetMap. Standard library only. See README.md next to this file.
"""
import argparse, json, math, os, re, sys, time, urllib.error, urllib.parse, urllib.request

W, H, PAD = 200, 150, 14   # viewBox, and the margin kept around the route
EDGE = 6                   # draw lines a little past the frame so they run off cleanly
TOL = 0.5                  # simplification tolerance for map lines, in viewBox units
ROUTE_TOL = 0.25           # ... and for the route itself
MIN_PATH = 5               # drop footpath pieces shorter than this (viewBox units)

MAJOR = {"motorway", "trunk", "primary", "secondary", "tertiary"}
MINOR = {"unclassified", "residential", "living_street", "pedestrian"}
PATHS = {"footway", "path", "cycleway", "track"}

OVERPASS = ["https://overpass-api.de/api/interpreter",
            "https://overpass.private.coffee/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"]
QUERY = """[out:json][timeout:90];(
way[highway~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|pedestrian|footway|path|cycleway|track|service)$"]({b});
way[natural=water]({b});relation[natural=water]({b});
way[waterway~"^(river|canal)$"]({b});way[railway=rail]({b}););out geom;"""

# Mirrors the colour tokens in site/styles.css: an <img> cannot see the page's CSS
# variables. If the palette changes there, change it here and regenerate the maps.
STYLE = """  <style>
    :root{color-scheme:light dark}
    path,text{fill:none;stroke-linecap:round;stroke-linejoin:round}
    .m-water{fill:light-dark(oklch(88% .040 240),oklch(33% .050 245))}
    .m-river{stroke:light-dark(oklch(88% .040 240),oklch(33% .050 245));stroke-width:3}
    .m-path{stroke:light-dark(oklch(89.8% .015 308),oklch(31% .030 302));stroke-width:.5}
    .m-minor{stroke:light-dark(oklch(83% .014 308),oklch(38% .028 302));stroke-width:.8}
    .m-rail{stroke:light-dark(oklch(83% .014 308),oklch(38% .028 302));stroke-width:.6;stroke-dasharray:2 1.2}
    .m-major{stroke:light-dark(oklch(83% .014 308),oklch(38% .028 302));stroke-width:1.6}
    .m-halo{stroke:light-dark(oklch(97.3% .006 308),oklch(22.7% .029 299));stroke-width:6.5}
    .m-bg{fill:light-dark(oklch(97.3% .006 308),oklch(22.7% .029 299))}
    .m-route{stroke:light-dark(oklch(40% .140 314.6),oklch(74% .070 316));stroke-width:3}
    .m-dot{fill:light-dark(oklch(40% .140 314.6),oklch(74% .070 316))}
    .m-ring{fill:light-dark(oklch(97.3% .006 308),oklch(22.7% .029 299));
      stroke:light-dark(oklch(40% .140 314.6),oklch(74% .070 316));stroke-width:2.5}
    .m-label{fill:light-dark(oklch(50.9% .033 308),oklch(70.4% .032 305));
      stroke:light-dark(oklch(97.3% .006 308),oklch(22.7% .029 299));stroke-width:1.6px;paint-order:stroke;
      font-family:ui-sans-serif,system-ui,-apple-system,sans-serif;font-size:5px;font-weight:700;
      letter-spacing:.12em;text-transform:uppercase}
    .m-label--water{fill:light-dark(oklch(58% .060 245),oklch(72% .050 240))}
  </style>"""


# ── GPX ────────────────────────────────────────────────────────────────────────

def load_gpx(path):
    text = open(path, encoding="utf-8").read()
    pts = [(float(a), float(b)) for a, b in
           re.findall(r'<(?:trk|rte)pt lat="([-\d.]+)" lon="([-\d.]+)"', text)]
    if len(pts) < 2:
        sys.exit(f"{path}: no track or route points found")
    return text, pts

def metres(p, q):
    la1, lo1, la2, lo2 = map(math.radians, (*p, *q))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


# ── projection: north up, route fitted into the viewBox ───────────────────────

def frame(pts):
    k = math.cos(math.radians(sum(p[0] for p in pts) / len(pts)))
    xs = [lon * k for _, lon in pts]
    ys = [-lat for lat, _ in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    s = min((W - 2 * PAD) / (maxx - minx), (H - 2 * PAD) / (maxy - miny))
    ox, oy = (W - (maxx - minx) * s) / 2, (H - (maxy - miny) * s) / 2

    def proj(lat, lon):
        return ((lon * k - minx) * s + ox, (-lat - miny) * s + oy)

    def unproj(x, y):
        return (-((y - oy) / s + miny), ((x - ox) / s + minx) / k)

    south, west = unproj(0, H)
    north, east = unproj(W, 0)
    return proj, (south, west, north, east)


# ── OpenStreetMap ─────────────────────────────────────────────────────────────

def fetch_osm(bbox, cache):
    if cache and os.path.exists(cache):
        print(f"using cached OSM data {cache}", file=sys.stderr)
        return json.load(open(cache, encoding="utf-8"))
    body = urllib.parse.urlencode({"data": QUERY.format(b="%.5f,%.5f,%.5f,%.5f" % bbox)}).encode()
    wait = 8
    for attempt in range(6):
        for url in OVERPASS:
            req = urllib.request.Request(url, body, {"User-Agent": "berlinharriers route_map.py"})
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    raw = r.read()
                data = json.loads(raw)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
                print(f"  {url}: {getattr(e, 'code', '')} {e}"[:120], file=sys.stderr)
                continue
            if cache:
                open(cache, "wb").write(raw)
            return data
        print(f"Overpass busy; retrying in {wait}s", file=sys.stderr)
        time.sleep(wait)
        wait *= 2
    sys.exit("Overpass API unavailable; try again later")


# ── geometry helpers ──────────────────────────────────────────────────────────

def rdp(p, tol):
    """Douglas–Peucker line simplification."""
    if len(p) < 3:
        return p
    (x1, y1), (x2, y2) = p[0], p[-1]
    dx, dy = x2 - x1, y2 - y1
    n = math.hypot(dx, dy) or 1e-9
    i, dmax = 0, -1
    for j in range(1, len(p) - 1):
        d = abs(dy * p[j][0] - dx * p[j][1] + x2 * y1 - y2 * x1) / n
        if d > dmax:
            i, dmax = j, d
    if dmax > tol:
        return rdp(p[:i + 1], tol)[:-1] + rdp(p[i:], tol)
    return [p[0], p[-1]]

def inside(x, y):
    return -EDGE <= x <= W + EDGE and -EDGE <= y <= H + EDGE

def runs(coords):
    """Split a projected line into the stretches that touch the frame."""
    out, cur = [], []
    for i, (x, y) in enumerate(coords):
        near = inside(x, y) or (i and inside(*coords[i - 1])) or \
               (i + 1 < len(coords) and inside(*coords[i + 1]))
        if near:
            cur.append((x, y))
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out

def stitch(segs):
    """Join relation members into rings so water areas can be filled."""
    segs = [s[:] for s in segs if len(s) > 1]
    rings = []
    while segs:
        ring = segs.pop(0)
        changed = True
        while changed and math.dist(ring[0], ring[-1]) > 1e-6:
            changed = False
            for i, s in enumerate(segs):
                if math.dist(ring[-1], s[0]) < 1e-6:
                    ring += s[1:]; segs.pop(i); changed = True; break
                if math.dist(ring[-1], s[-1]) < 1e-6:
                    ring += s[::-1][1:]; segs.pop(i); changed = True; break
        rings.append(ring)
    return rings

def path_d(lines, close=False):
    parts = []
    for ln in lines:
        ln = rdp(ln, TOL)
        if len(ln) < 2:
            continue
        if not close and len(ln) == 2 and math.dist(ln[0], ln[-1]) < 0.8:
            continue  # stubs too short to see
        s = f"M{ln[0][0]:.1f} {ln[0][1]:.1f}" + "".join(f"L{x:.1f} {y:.1f}" for x, y in ln[1:])
        parts.append(s + ("Z" if close else ""))
    return "".join(parts).replace("L", " ").replace(" -", "-")


# ── drawing ───────────────────────────────────────────────────────────────────

def layers(data, proj):
    out = {k: [] for k in ("water", "river", "rail", "major", "minor", "path")}
    for el in data["elements"]:
        tags = el.get("tags", {})
        if el["type"] == "way" and "geometry" in el:
            geoms = [el["geometry"]]
        elif el["type"] == "relation":
            geoms = [m["geometry"] for m in el.get("members", [])
                     if m.get("role") == "outer" and "geometry" in m]
        else:
            continue
        hw = tags.get("highway")
        for g in geoms:
            c = [proj(p["lat"], p["lon"]) for p in g]
            if tags.get("natural") == "water":
                out["water"].append(c)
            elif tags.get("waterway") in ("river", "canal"):
                out["river"] += runs(c)
            elif tags.get("railway") == "rail":
                out["rail"] += runs(c)
            elif hw in MAJOR:
                out["major"] += runs(c)
            elif hw in MINOR:
                out["minor"] += runs(c)
            elif hw in PATHS and not (tags.get("footway") or tags.get("cycleway")):
                # skip pavements and crossings; keep only paths long enough to read
                for r in runs(c):
                    if sum(math.dist(r[i], r[i + 1]) for i in range(len(r) - 1)) >= MIN_PATH:
                        out["path"].append(r)
    water = [r for r in stitch(out["water"])
             if any(-60 <= x <= W + 60 and -60 <= y <= H + 60 for x, y in r)]
    return [f'<path class="m-water" d="{path_d(water, close=True)}"/>',
            f'<path class="m-river" d="{path_d(out["river"])}"/>',
            f'<path class="m-path" d="{path_d(out["path"])}"/>',
            f'<path class="m-minor" d="{path_d(out["minor"])}"/>',
            f'<path class="m-rail" d="{path_d(out["rail"])}"/>',
            f'<path class="m-major" d="{path_d(out["major"])}"/>']

def route_parts(pts, proj, finish):
    route = rdp([proj(*p) for p in pts], ROUTE_TOL)
    d = "M" + " ".join(f"{x:.1f} {y:.1f}" for x, y in route)
    sx, sy = proj(*pts[0])
    ex, ey = proj(*pts[-1])
    return d, (f"{sx:.1f}", f"{sy:.1f}"), (f"{ex:.1f}", f"{ey:.1f}") if finish else None

def map_svg(title, base, labels, d, start, end):
    body = [*base, *labels, f'<path class="m-halo" d="{d}"/>', f'<path class="m-route" d="{d}"/>']
    if end:
        body += [f'<circle cx="{end[0]}" cy="{end[1]}" r="6.5" class="m-bg"/>',
                 f'<circle cx="{end[0]}" cy="{end[1]}" r="3.6" class="m-ring"/>']
    body += [f'<circle cx="{start[0]}" cy="{start[1]}" r="6.5" class="m-bg"/>',
             f'<circle cx="{start[0]}" cy="{start[1]}" r="4.5" class="m-dot"/>']
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150" width="1200" height="900">\n'
            f'  <!-- {title} route on OpenStreetMap data. Map data © OpenStreetMap contributors (ODbL).\n'
            '       Background is transparent; the page supplies the surface colour. -->\n'
            + STYLE + "\n" + "\n".join("  " + l for l in body) + "\n</svg>\n")

def route_svg(aria, d, start, end):
    """Route-only drawing in currentColor, as used on the home page schedule cards."""
    ring = (f'  <circle cx="{end[0]}" cy="{end[1]}" r="4" fill="none" stroke="currentColor" stroke-width="2.5"/>\n'
            if end else "")
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150" role="img"\n'
            f'     aria-label="{aria}">\n'
            f'  <path d="{d}" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>\n'
            + ring +
            f'  <circle cx="{start[0]}" cy="{start[1]}" r="5" fill="currentColor"/>\n'
            '</svg>\n')

def clean_gpx(text):
    """Remove what can identify a person: author, timestamps, sensor extensions."""
    text = re.sub(r"\s*<author>.*?</author>", "", text, flags=re.S)
    text = re.sub(r"\s*<time>.*?</time>", "", text, flags=re.S)
    text = re.sub(r"\s*<extensions>.*?</extensions>", "", text, flags=re.S)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gpx", help="route GPX (exported from Strava)")
    ap.add_argument("out", help="map SVG to write, e.g. site/routes/<run>-map.svg")
    ap.add_argument("--title", required=True, help='run name for the SVG comment, e.g. "Monday Duck"')
    ap.add_argument("--finish", action="store_true", help="mark the finish with a ring (point-to-point routes)")
    ap.add_argument("--labels", help="file of <text class=\"m-label\" ...> lines to place on the map")
    ap.add_argument("--osm-cache", help="save/reuse the Overpass response here (keep it out of git)")
    ap.add_argument("--route-svg", nargs=2, metavar=("OUT", "ARIA_LABEL"),
                    help="also write the route-only drawing used on the schedule cards")
    ap.add_argument("--clean-gpx", metavar="OUT", help="also write a copy with author/times/sensors removed")
    a = ap.parse_args()

    text, pts = load_gpx(a.gpx)
    length = sum(metres(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    print(f"{len(pts)} points, {length / 1000:.2f} km, start–finish gap {metres(pts[0], pts[-1]):.0f} m",
          file=sys.stderr)
    if "<author>" in text or "<time>" in text:
        print("note: this GPX has author details or timestamps — use --clean-gpx before committing it",
              file=sys.stderr)

    proj, bbox = frame(pts)
    data = fetch_osm(bbox, a.osm_cache)
    labels = [l.strip() for l in open(a.labels, encoding="utf-8")] if a.labels else []
    d, start, end = route_parts(pts, proj, a.finish)

    svg = map_svg(a.title, layers(data, proj), [l for l in labels if l], d, start, end)
    open(a.out, "w", encoding="utf-8").write(svg)
    print(f"wrote {a.out} ({len(svg) / 1024:.0f} KB)", file=sys.stderr)

    if a.route_svg:
        open(a.route_svg[0], "w", encoding="utf-8").write(route_svg(a.route_svg[1], d, start, end))
        print(f"wrote {a.route_svg[0]}", file=sys.stderr)
    if a.clean_gpx:
        open(a.clean_gpx, "w", encoding="utf-8").write(clean_gpx(text))
        print(f"wrote {a.clean_gpx}", file=sys.stderr)


if __name__ == "__main__":
    main()
