#!/usr/bin/env bash
# Render the Open Graph cards in card.html to site/og/<card>.jpg (1200×630).
# An optional helper run by hand, like assets/routes/tools/route_map.py — not a
# build step. Needs Google Chrome and macOS sips. Usage: assets/og/render.sh [card…]
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
chrome="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
port="${PORT:-8897}"
cards=("$@")
[ ${#cards[@]} -gt 0 ] || cards=(home monday-duck tuesday-track thursday-swan friday-dachshund saturday-parkrun)

tmp="$(mktemp -d)"
python3 -m http.server "$port" --bind 127.0.0.1 --directory "$root" >/dev/null 2>&1 &
server=$!
trap 'kill $server 2>/dev/null; rm -rf "$tmp"' EXIT
sleep 1

mkdir -p "$root/site/og"
for card in "${cards[@]}"; do
  # The virtual-time budget lets fonts, the crest and the inlined maps load first.
  "$chrome" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --window-size=1200,630 --virtual-time-budget=5000 --user-data-dir="$tmp/profile" \
    --screenshot="$tmp/$card.png" "http://127.0.0.1:$port/assets/og/card.html?card=$card" \
    >/dev/null 2>&1
  sips -s format jpeg -s formatOptions 82 "$tmp/$card.png" --out "$root/site/og/$card.jpg" >/dev/null
  echo "site/og/$card.jpg  $(sips -g pixelWidth -g pixelHeight "$root/site/og/$card.jpg" | awk '/pixel/{printf "%s ", $2}')$(du -k "$root/site/og/$card.jpg" | cut -f1) KB"
done
