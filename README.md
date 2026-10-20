# Goedkope Boodschappen

Gratis boodschappenvergelijker zonder reclame: https://boodschappenvergelijk.nl/

## Hoe het werkt

- **Elke ochtend** (GitHub Action "Prijzen ophalen", `ophalen/ophalen.mjs`) worden de aanbiedingen opgehaald van
  Albert Heijn, Jumbo, Lidl, Aldi, PLUS, Dirk, DekaMarkt, Hoogvliet en Poiesz, plus het Aldi-assortiment.
  Resultaat in `data/`: `aanbiedingen.json`, `aldi.json` en `status.json` (aantallen en fouten per winkel).
  Faalt een winkel, dan blijven de vorige acties van die winkel staan.
- **Netlify bouwt de site** bij elke wijziging op `main` (dus ook na de dagelijkse prijzen-commit) met `scripts/build.sh`:
  1. de nieuwste gewone prijzen uit de open dataset van [Checkjebon](https://github.com/supermarkt/checkjebon) (`scripts/prep.py`),
  2. alle pagina's (`scripts/bouw_paginas.py`): de app, productvergelijkingen, categorieën, aanbiedingen per winkel,
     supermarktpagina's, "AH of Jumbo?"-vergelijkingen, de goedkoopste supermarkt, over, privacy, sitemap en robots.txt.
- De app zelf staat in `site/index.html`, de gedeelde stijl in `site/stijl.css`. Productlijst per categorie: `scripts/cats.json`.

Handmatig prijzen ophalen: tab Actions > Prijzen ophalen > Run workflow. Lokaal bouwen: `bash scripts/build.sh`.

## Bezoekersstatistieken

Via [GoatCounter](https://goedkopeboodschappen.goatcounter.com/), zonder cookies. Naast paginabezoeken worden deze
gebeurtenissen geteld: `zoek/…` (zoekopdrachten), `lijst/…` (op de lijst gezet), `naar/<winkel>` (doorklik naar een
supermarkt), `aanbiedingen/<winkel>`, `weergave/…`, `deel`, `print` en `winkels/<aantal>`.

## Geen verdienmodel

Geen reclame, geen affiliatelinks, geen betaalde plekken. Links naar supermarkten zijn gewone links.
