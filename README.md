Goedkope Boodschappen: dagelijkse data voor https://goedkopeboodschappen.netlify.app/

- `ophalen/ophalen.mjs` haalt elke ochtend (GitHub Action "Prijzen ophalen") het Aldi-assortiment en de aanbiedingen van AH, Jumbo, Lidl, Dirk en Aldi op.
- Resultaat in `data/`: `aldi.json`, `aanbiedingen.json` en `status.json` (aantallen en fouten per winkel).
- Handmatig starten: tab Actions > Prijzen ophalen > Run workflow.

Bron van de site:
- `site/index.html` is de app (gebruikt `producten.json` uit de Checkjebon-dataset, plus `data/*.json` van deze repository).
- `scripts/seo_pages.py` en `scripts/build_netlify.py` maken de Netlify-map met SEO-pagina's; die wordt als zip naar Netlify geüpload.
