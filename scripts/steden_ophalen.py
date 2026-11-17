"""Welke supermarkten zitten er in welke stad? Uit OpenStreetMap (© OpenStreetMap-bijdragers, ODbL), via Overpass.

  python3 scripts/steden_ophalen.py      -> data/supermarkten-steden.json

Telt per plaats (addr:city) de vestigingen per keten die we vergelijken. AH to go telt niet mee (andere prijzen).
Wordt maandelijks gedraaid door .github/workflows/steden.yml; scripts/bouw_paginas.py maakt er de stadspagina's van.
"""
import json, os, re, sys, time, urllib.request, urllib.parse, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UIT = os.path.join(ROOT, "data", "supermarkten-steden.json")
Q = '[out:json][timeout:180];area["ISO3166-1"="NL"][admin_level=2]->.nl;nwr["shop"="supermarket"](area.nl);out tags center;'
SERVERS = ["https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]

KETENS = [  # (id, patroon op brand of name)
    ("ah", r"^albert heijn"), ("jumbo", r"^jumbo\b"), ("lidl", r"^lidl\b"), ("aldi", r"^aldi\b"), ("plus", r"^plus\b"),
    ("dirk", r"^dirk\b"), ("dekamarkt", r"^deka ?markt"), ("hoogvliet", r"^hoogvliet"), ("poiesz", r"^poiesz"),
    ("spar", r"^spar\b"), ("vomar", r"^vomar"),
]

def keten(tags):
    for veld in ("brand", "name"):
        v = (tags.get(veld) or "").strip().lower()
        if not v: continue
        if re.search(r"\bto go\b", v): return None
        for k, pat in KETENS:
            if re.search(pat, v): return k
    return None

def haal(q=Q):
    data = urllib.parse.urlencode({"data": q}).encode()
    fout = None
    for s in SERVERS * 2:
        try:
            req = urllib.request.Request(s, data=data, headers={"User-Agent": "boodschappenvergelijk.nl (stadspagina's; goedkopeboodschappen@proton.me)"})
            return json.load(urllib.request.urlopen(req, timeout=240))
        except Exception as e:
            fout = e; print("overpass:", s, e); time.sleep(20)
    raise SystemExit(f"Overpass niet bereikbaar: {fout}")

els = haal()["elements"]
steden, zonder, pos = {}, 0, {}
for e in els:
    t = e.get("tags", {}); k = keten(t)
    if not k: continue
    stad = (t.get("addr:city") or "").strip()
    if not stad: zonder += 1; continue
    steden.setdefault(stad, {}); steden[stad][k] = steden[stad].get(k, 0) + 1
    la, lo = e.get("lat") or (e.get("center") or {}).get("lat"), e.get("lon") or (e.get("center") or {}).get("lon")
    if la and lo: pos.setdefault(stad, []).append((la, lo))
print(f"{len(els)} supermarkten in OSM, {sum(sum(v.values()) for v in steden.values())} van onze ketens met plaats, {zonder} zonder plaats, {len(steden)} plaatsen")
if len(steden) < 500: raise SystemExit("te weinig plaatsen, niet opgeslagen")

# Voor de steden met een eigen pagina ook tellen binnen de grens van de plaats of gemeente: zo tellen ook winkels mee
# zonder adres in OpenStreetMap. Per keten nemen we het hoogste van beide tellingen.
for st in json.load(open(os.path.join(ROOT, "scripts", "steden.json"))):
    o = st["osm"]
    # Eerst de woonplaats (admin_level 10); bestaat die niet in OSM, dan de gemeente (8).
    res = None
    for lvl in ("10", "8"):
        q = (f'[out:json][timeout:90];area["name"="{o}"]["boundary"="administrative"]["admin_level"="{lvl}"]->.a;'
             f'(.a;)->.a;nwr["shop"="supermarket"](area.a);out tags;')
        try: res = haal(q)["elements"]
        except SystemExit as e: print("overgeslagen:", o, lvl, e); res = None
        if res: break
        time.sleep(2)
    if not res: continue
    tel = {}
    for e in res:
        k = keten(e.get("tags", {}))
        if k: tel[k] = tel.get(k, 0) + 1
    oud = steden.get(o, {})
    steden[o] = {k: max(oud.get(k, 0), tel.get(k, 0)) for k in set(oud) | set(tel)}
    if steden[o] != oud: print(f"{o}: {oud} -> {steden[o]}")
    time.sleep(3)
midden = {st: [round(sum(p[0] for p in ps) / len(ps), 4), round(sum(p[1] for p in ps) / len(ps), 4)] for st, ps in pos.items()}
json.dump({"updated": datetime.date.today().isoformat(), "bron": "© OpenStreetMap-bijdragers (ODbL)", "steden": steden, "midden": midden}, open(UIT, "w"), ensure_ascii=False, sort_keys=True)
