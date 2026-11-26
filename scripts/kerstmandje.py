"""Prijsverloop van het kerstmandje (KERSTPAKKET in vergelijk.py): elke dag de totaalprijs per supermarkt, aanbiedingen meegerekend.

  python3 scripts/kerstmandje.py dag <map-met-producten.json>   -> drukt de meting van vandaag af (JSON)
  python3 scripts/kerstmandje.py bijwerken <supermarkets.json>   -> voegt de meting van vandaag toe aan data/kerstmandje.json

data/kerstmandje.json: {"dagen": {"2026-11-26": {"aldi": 61.23, ...}, ...}}
Alleen in november en december; daarna doet "bijwerken" niets.
"""
import json, os, sys, subprocess, tempfile, datetime
from zoneinfo import ZoneInfo
HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HIER)
PAD = os.path.join(ROOT, "data", "kerstmandje.json")

def dag(map_):
    sys.argv = [sys.argv[0], map_]
    sys.path.insert(0, HIER)
    import vergelijk as v
    return {v.stores[r["si"]]["id"]: round(r["tot"], 2) for r in v.KERST}

def bijwerken(supermarkets_json):
    nu = datetime.datetime.now(ZoneInfo("Europe/Amsterdam")).date()
    if nu.month not in (11, 12): return
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, os.path.join(HIER, "prep.py"), supermarkets_json, os.path.join(tmp, "producten.json")], check=True, stdout=subprocess.DEVNULL)
        r = subprocess.run([sys.executable, __file__, "dag", tmp], check=True, capture_output=True, text=True)
        m = json.loads(r.stdout.strip().splitlines()[-1])
    if len(m) < 3: return
    try: h = json.load(open(PAD))
    except Exception: h = {"dagen": {}}
    # Alleen dit seizoen bewaren (vorig jaar is met een ander mandje niet te vergelijken).
    h["dagen"] = {d: w for d, w in h["dagen"].items() if d[:4] == str(nu.year)}
    h["dagen"][nu.isoformat()] = m
    json.dump(h, open(PAD, "w"), ensure_ascii=False, separators=(",", ":"), sort_keys=True)

if __name__ == "__main__":
    if sys.argv[1] == "dag": print(json.dumps(dag(sys.argv[2])))
    elif sys.argv[1] == "bijwerken": bijwerken(sys.argv[2])
