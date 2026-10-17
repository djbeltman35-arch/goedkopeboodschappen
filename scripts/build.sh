#!/usr/bin/env bash
# Bouwt de complete site in één map (standaard public/): app, SEO-pagina's, aanbiedingenpagina's, sitemap.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=${1:-public}
rm -rf "$OUT"; mkdir -p "$OUT"
cp -r site/producten.json site/404.html site/netlify.toml site/manifest.webmanifest site/icons "$OUT"/
python3 scripts/seo_pages.py site/producten.json "$OUT" site/index.html data/aanbiedingen.json
python3 scripts/build_netlify.py site/index.html "$OUT/index.html"
echo "klaar: $(find "$OUT" -type f | wc -l) bestanden in $OUT"
