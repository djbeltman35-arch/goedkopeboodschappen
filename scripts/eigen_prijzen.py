"""Zet eigen, actuele gewone prijzen in de plaats van verouderde gegevens uit het open prijzenbestand, en geeft
elke winkel de datum mee van wanneer zijn prijzen zijn.

  python3 scripts/eigen_prijzen.py <supermarkets.json>     (past het bestand ter plekke aan)

- data/assortiment-<winkel>.json (ophalen/assortiment.mjs, dagelijks) vervangt de gegevens van die winkel als het
  minder dan 4 dagen oud is.
- data/bronstatus.json zegt sinds wanneer de prijzen van een winkel in het open bestand niet meer zijn veranderd.
- Elke winkel krijgt "dt": de datum van zijn prijzen. prep.py neemt die over; de site toont oude prijzen als
  "prijs van <maand>" en laat ze niet meer als goedkoopste meetellen.
"""
import json, os, re, sys, glob, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
pad = sys.argv[1]
d = json.load(open(pad))
vandaag = datetime.date.today()
try: bron = json.load(open(os.path.join(DATA, "bronstatus.json")))
except Exception: bron = {}
eigen = {}
for f in glob.glob(os.path.join(DATA, "assortiment-*.json")):
    try:
        a = json.load(open(f))
        dag = datetime.date.fromisoformat(a["updated"][:10])
        if (vandaag - dag).days <= 3 and (len(a.get("d", [])) > 1000 or "bekeken" in a or (a.get("klein") and len(a.get("d", [])) > 300)): eigen[a["n"]] = (a, dag.isoformat())
    except Exception as e: print("eigen prijzen: overgeslagen", f, e)
gezien = set()
for s in d:
    gezien.add(s["n"])
    if s["n"] in eigen:
        a, dag = eigen[s["n"]]
        if "bekeken" in a:
            # Wordt verdeeld over de week opgehaald: eigen prijzen waar die er al zijn, de rest nog even uit het open bestand.
            pid = lambda l: (re.search(r"(\d+)/?$", str(l)) or [None, None])[1]
            eig = {pid(x["l"]) for x in a["d"]}
            namen = {x["n"].strip().lower() for x in a["d"]}
            rest = [x for x in s.get("d", []) if pid(x.get("l")) not in eig and x["n"].strip().lower() not in namen]
            # Is (bijna) het hele assortiment al eens langs geweest? Dan is wat alleen nog in het open bestand staat oud of uit het assortiment.
            if a.get("t") and len(a["bekeken"]) >= 0.95 * a["t"]: rest = []
            print(f"{s['n']:10} eigen prijzen van {dag}: {len(a['d'])} producten, nog {len(rest)} uit het open bestand")
            s["d"] = [dict(x, l=x["l"]) for x in a["d"]] + [dict(x, l=s["u"] + x["l"]) for x in rest]
            s["u"] = ""
            s["dt"] = dag if len(rest) < len(a["d"]) * 0.25 else (bron.get(s["n"]) or {}).get("sinds")
        else:
            if s["n"] == "ah":  # bundels ("12-pack", maat "2 stuks") zijn meerdere verpakkingen van een los product
                a["d"] = [x for x in a["d"] if not (re.search(r"\d+\s*-?\s*(?:pack|pck)\b", x["n"], re.I) and re.match(r"^\d+ stuks?$", x.get("s") or "", re.I))]
            print(f"{s['n']:10} eigen prijzen van {dag}: {len(a['d'])} producten (open bestand: {len(s.get('d', []))})")
            s["d"], s["u"], s["dt"] = a["d"], a.get("u", s["u"]), dag
    elif s["n"] == "aldi":
        try: s["dt"] = json.load(open(os.path.join(DATA, "aldi.json")))["updated"][:10]
        except Exception: pass
    else:
        s["dt"] = (bron.get(s["n"]) or {}).get("sinds")
        print(f"{s['n']:10} open bestand, prijzen veranderd tot {s['dt']}")
for n, (a, dag) in eigen.items():
    if n not in gezien: d.append({"n": n, "c": a.get("c", n), "u": a["u"], "d": a["d"], "dt": dag})
# Lidl: alleen de aanbiedingen van deze week (Erik, nov 2026). Lidl zet maar van een deel van de boodschappen een gewone
# prijs online, en een deel daarvan is eigenlijk een actieprijs; dat gaf een scheef beeld. Elke Lidl-prijs heet daarom
# "(aanbieding t/m ...)", zodat bezoekers zien dat het een actie is. Acties die pas later beginnen, tellen nog niet mee.
try:
    acties = [o for o in json.load(open(os.path.join(DATA, "aanbiedingen.json")))["offers"] if o.get("s") == "lidl" and o.get("p")]
    def _dm(t): return f"{t[8:10]}-{t[5:7]}"
    lidl_d = []
    for o in acties:
        if o.get("v") and o["v"] > vandaag.isoformat(): continue
        if o.get("t") and o["t"] < vandaag.isoformat(): continue
        # Artikelen uit de webshop (servies, tuinspullen; artikelnummer van 9+ cijfers) zijn geen boodschappen.
        if re.search(r"/p\d{9,}/?$", o.get("u") or ""): continue
        plus = " met Lidl Plus" if "lidl plus" in (o.get("lbl") or "").lower() else ""
        label = f"aanbieding{plus}" + (f" t/m {_dm(o['t'])}" if o.get("t") else "")
        u = o.get("u") or ""
        lidl_d.append({"n": f"{o['n']} ({label})", "l": re.sub(r"^https://www\.lidl\.nl", "", u) or "/c/aanbiedingen/a10008785", "p": o["p"], "s": o.get("sz") or ""})
    lidl = next((s for s in d if s["n"] == "lidl"), None)
    if lidl is None:
        lidl = {"n": "lidl", "c": "Lidl"}; d.append(lidl)
    lidl.update({"u": "https://www.lidl.nl", "d": lidl_d, "dt": vandaag.isoformat()})
    print(f"lidl       alleen aanbiedingen: {len(lidl_d)}")
except Exception as e: print("lidl-aanbiedingen overgeslagen:", e)
# Lidl-prijzen van kassabonnen van bezoekers: alleen voor producten waar Lidl online geen prijs voor toont.
try:
    bonnen = json.load(open(os.path.join(DATA, "lidl-bonnen.json"))).get("producten", [])
    lidl = next((s for s in d if s["n"] == "lidl"), None)
    if lidl is not None and bonnen:
        namen = {x["n"].strip().lower() for x in lidl.get("d", [])}
        pre = lidl.get("u") or "https://www.lidl.nl"
        extra = [{"n": f'{b["n"]} (Lidl-kassabon {b["datum"][8:10]}-{b["datum"][5:7]})', "l": ("" if lidl.get("u") else pre) + "/q/search?q=" + re.sub(r"\s+", "+", b["n"].lower()), "p": b["p"], "s": b.get("s") or ""}
                 for b in bonnen if b["n"].strip().lower() not in namen and (vandaag - datetime.date.fromisoformat(b["datum"])).days <= 60]
        lidl["d"] = lidl.get("d", []) + extra
        print(f"lidl       {len(extra)} prijzen van kassabonnen van bezoekers")
except FileNotFoundError: pass
except Exception as e: print("lidl-bonnen overgeslagen:", e)
json.dump(d, open(pad, "w"), ensure_ascii=False)
