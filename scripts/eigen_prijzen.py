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
json.dump(d, open(pad, "w"), ensure_ascii=False)
