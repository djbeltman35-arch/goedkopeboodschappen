"""Welke supermarkten zitten er in welke stad? Uit OpenStreetMap (© OpenStreetMap-bijdragers, ODbL), via Overpass.

  python3 scripts/steden_ophalen.py      -> data/supermarkten-steden.json

Telt per plaats (addr:city) de vestigingen per keten die we vergelijken. AH to go telt niet mee (andere prijzen).
Wordt maandelijks gedraaid door .github/workflows/steden.yml; scripts/bouw_paginas.py maakt er de stadspagina's van.
"""
import json, os, re, sys, time, urllib.request, urllib.parse, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UIT = os.path.join(ROOT, "data", "supermarkten-steden.json")
Q = '[out:json][timeout:180];area["ISO3166-1"="NL"][admin_level=2]->.nl;nwr["shop"="supermarket"](area.nl);out tags;'
SERVERS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]

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

def haal():
    data = urllib.parse.urlencode({"data": Q}).encode()
    fout = None
    for s in SERVERS * 2:
        try:
            req = urllib.request.Request(s, data=data, headers={"User-Agent": "boodschappenvergelijk.nl (stadspagina's; goedkopeboodschappen@proton.me)"})
            return json.load(urllib.request.urlopen(req, timeout=240))
        except Exception as e:
            fout = e; print("overpass:", s, e); time.sleep(20)
    raise SystemExit(f"Overpass niet bereikbaar: {fout}")

els = haal()["elements"]
steden, zonder = {}, 0
for e in els:
    t = e.get("tags", {}); k = keten(t)
    if not k: continue
    stad = (t.get("addr:city") or "").strip()
    if not stad: zonder += 1; continue
    steden.setdefault(stad, {}); steden[stad][k] = steden[stad].get(k, 0) + 1
print(f"{len(els)} supermarkten in OSM, {sum(sum(v.values()) for v in steden.values())} van onze ketens met plaats, {zonder} zonder plaats, {len(steden)} plaatsen")
if len(steden) < 500: raise SystemExit("te weinig plaatsen, niet opgeslagen")
json.dump({"updated": datetime.date.today().isoformat(), "bron": "© OpenStreetMap-bijdragers (ODbL)", "steden": steden}, open(UIT, "w"), ensure_ascii=False, sort_keys=True)
