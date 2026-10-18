#!/usr/bin/env bash
# Bouwt de complete site in één map (standaard public/). Draait op Netlify bij elke wijziging op GitHub
# (ook de dagelijkse prijzen-commit), en lokaal met: bash scripts/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=${1:-public}
rm -rf "$OUT"; mkdir -p "$OUT/data"

# 1. Gewone prijzen: de nieuwste open dataset van Checkjebon. Lukt downloaden niet, dan de vorige versie uit site/.
if curl -fsSL --max-time 120 -o /tmp/supermarkets.json https://raw.githubusercontent.com/supermarkt/checkjebon/main/data/supermarkets.json \
   && python3 scripts/prep.py /tmp/supermarkets.json "$OUT/producten.json"; then
  echo "Checkjebon-prijzen van vandaag gebruikt"
else
  echo "Checkjebon niet bereikbaar, vorige prijzen gebruikt"; cp site/producten.json "$OUT/producten.json"
fi

# 2. Vaste bestanden en de dagelijkse data (aanbiedingen, Aldi, status)
cp -r site/icons site/manifest.webmanifest site/stijl.css site/sw.js site/google2c5158ed8322f460.html "$OUT"/
cp data/aanbiedingen.json data/aldi.json data/status.json "$OUT/data/"
[ -d data/social ] && cp -r data/social "$OUT/data/"

# 3. Alle pagina's
python3 scripts/bouw_paginas.py "$OUT"
echo "klaar: $(find "$OUT" -type f | wc -l) bestanden in $OUT"
