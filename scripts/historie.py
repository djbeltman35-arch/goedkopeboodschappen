"""Prijsgeschiedenis: per product (zoekterm uit cats.json) en per supermarkt de laagste gewone prijs per kilo/liter/stuk.

  python3 scripts/historie.py dag <map-met-producten.json>       -> drukt de meting van die dag af (JSON)
  python3 scripts/historie.py bijwerken <supermarkets.json>       -> voegt de meting van vandaag toe aan data/historie.json
  python3 scripts/historie.py terugvullen <checkjebon-repo> [n]   -> vult de geschiedenis aan uit de laatste n versies van Checkjebon

data/historie.json: {"dagen": [datum, ...], "termen": {term: {winkel: [prijs per eenheid of null, ...]}}, "eenheid": {term: "kg"|"l"|"st"}}
Bewaart maximaal 400 dagen.
"""
import json, os, sys, subprocess, tempfile, datetime
HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HIER)
PAD = os.path.join(ROOT, "data", "historie.json")
MAX = 400

def dag(map_):
    sys.argv = [sys.argv[0], map_]
    os.environ["ZONDER_AANBIEDINGEN"] = "1"
    sys.path.insert(0, HIER)
    import vergelijk as v
    uit, eh = {}, {}
    for t in v.TERMS:
        rows = v.per_store(v.matches(t))
        for si, p in rows.items():
            u = v.eff_unit(p)
            if u is None or id(p) in v.BAD or not 0 < u < 1000: continue
            uit.setdefault(t, {})[v.stores[si]["id"]] = round(u, 2)
            eh.setdefault(t, {}).setdefault(p[6], 0); eh[t][p[6]] += 1
    return {"termen": uit, "eenheid": {t: max(c, key=c.get) for t, c in eh.items()}}

def meet(supermarkets_json, zonder_aldi=False):
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, os.path.join(HIER, "prep.py"), supermarkets_json, os.path.join(tmp, "producten.json")], check=True, stdout=subprocess.DEVNULL)
        env = dict(os.environ, **({"ZONDER_ALDI": "1"} if zonder_aldi else {}))
        r = subprocess.run([sys.executable, __file__, "dag", tmp], check=True, capture_output=True, text=True, env=env)
        return json.loads(r.stdout.strip().splitlines()[-1])

def laad():
    try: return json.load(open(PAD))
    except Exception: return {"dagen": [], "termen": {}, "eenheid": {}}

def voeg_toe(h, datum, m):
    # Meting als kolom toevoegen (of een bestaande datum vervangen), alles op datum gesorteerd.
    reeksen = {(t, w): dict(zip(h["dagen"], vals)) for t, ws in h["termen"].items() for w, vals in ws.items()}
    for t, ws in m["termen"].items():
        for w, val in ws.items(): reeksen.setdefault((t, w), {})[datum] = val
    for (t, w), r in reeksen.items():
        if datum in r and (t not in m["termen"] or w not in m["termen"][t]): r.pop(datum)
    dagen = sorted(set(h["dagen"]) | {datum})[-MAX:]
    termen = {}
    for (t, w), r in reeksen.items():
        vals = [r.get(d) for d in dagen]
        if any(x is not None for x in vals): termen.setdefault(t, {})[w] = vals
    h["dagen"], h["termen"] = dagen, termen
    h["eenheid"].update(m["eenheid"])
    return h

def schrijf(h):
    json.dump(h, open(PAD, "w"), separators=(",", ":"), ensure_ascii=False)

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "dag":
        print(json.dumps(dag(sys.argv[2]), ensure_ascii=False))
    elif cmd == "bijwerken":
        vandaag = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).date().isoformat()
        h = voeg_toe(laad(), vandaag, meet(sys.argv[2])); schrijf(h)
        print("historie:", len(h["dagen"]), "dagen,", len(h["termen"]), "producten")
    elif cmd == "terugvullen":
        repo, n = sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 90
        log = subprocess.run(["git", "-C", repo, "log", "--format=%H %cd", "--date=short", f"-{n}", "origin/main", "--", "data/supermarkets.json"], capture_output=True, text=True, check=True).stdout.split("\n")
        h = laad(); gezien = set(h["dagen"])
        for regel in reversed([l for l in log if l.strip()]):
            sha, datum = regel.split()
            if datum in gezien: continue
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
                subprocess.run(["git", "-C", repo, "show", f"{sha}:data/supermarkets.json"], stdout=f, check=True)
            try:
                h = voeg_toe(h, datum, meet(f.name, zonder_aldi=True)); gezien.add(datum); print(datum, "ok", flush=True)
            except Exception as e: print(datum, "mislukt", e, flush=True)
            finally: os.unlink(f.name)
        schrijf(h); print("historie:", len(h["dagen"]), "dagen")
