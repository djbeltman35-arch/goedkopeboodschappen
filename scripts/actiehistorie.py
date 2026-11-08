"""Actiegeschiedenis: hoe vaak is een product in de aanbieding? (zoals "zeldzaam / af en toe / vaak" bij andere vergelijkers,
maar eerlijk: we noemen altijd over hoeveel weken we het weten).

  python3 scripts/actiehistorie.py bijwerken            -> voegt de acties uit data/aanbiedingen.json toe aan data/actiehistorie.json
  python3 scripts/actiehistorie.py opbouwen             -> bouwt het bestand opnieuw op uit alle versies van data/aanbiedingen.json in git

data/actiehistorie.json: {"sinds": {winkel: eerste datum}, "p": {"winkel|sleutel": [einddag van elke actie, ...]}}
(einddag = aantal dagen na 1 januari 2026, zodat het bestand klein blijft; dag() en datum() rekenen om)
Eén actie = één einddatum: een actie van woensdag t/m dinsdag telt zo maar één keer, ook al loopt hij over twee kalenderweken.
"""
import json, os, re, sys, subprocess, unicodedata, datetime
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAD = os.path.join(ROOT, "data", "actiehistorie.json")
BRON = "data/aanbiedingen.json"
BEWAAR = 400  # dagen

NUL = datetime.date(2026, 1, 1)
def dag(t): return (datetime.date.fromisoformat(t) - NUL).days
def datum(n): return (NUL + datetime.timedelta(days=n)).isoformat()

def sleutel(o):
    """Vaste sleutel per product: het productnummer van de winkel, anders de genormaliseerde naam (zonder maat)."""
    if o.get("k"): return f'{o["s"]}|{o["k"]}'
    n = unicodedata.normalize("NFD", str(o.get("n", "")).lower())
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return f'{o["s"]}|' + re.sub(r"[^a-z0-9]+", " ", n).strip()

def laad():
    try: return json.load(open(PAD))
    except Exception: return {"sinds": {}, "p": {}}

def voeg_toe(h, offers, op):
    """Acties die op dag 'op' liepen toevoegen."""
    for o in offers:
        t = o.get("t")
        if not t or not o.get("s"): continue
        if o.get("v") and o["v"] > op: continue  # nog niet begonnen: telt pas als hij loopt
        h["sinds"].setdefault(o["s"], op)
        if h["sinds"][o["s"]] > op: h["sinds"][o["s"]] = op
        r = h["p"].setdefault(sleutel(o), []); t = dag(t)
        if t not in r: r.append(t); r.sort()

def opruimen(h, vandaag):
    grens = dag(vandaag) - BEWAAR
    h["p"] = {k: [t for t in v if t >= grens] for k, v in h["p"].items()}
    h["p"] = {k: v for k, v in sorted(h["p"].items()) if v}

def schrijf(h):
    json.dump(h, open(PAD, "w"), ensure_ascii=False, separators=(",", ":"))

def vandaag(): return datetime.datetime.now(ZoneInfo("Europe/Amsterdam")).date().isoformat()

if __name__ == "__main__":
    taak = sys.argv[1] if len(sys.argv) > 1 else "bijwerken"
    if taak == "bijwerken":
        h = laad(); d = json.load(open(os.path.join(ROOT, BRON)))
        voeg_toe(h, d.get("offers", []), vandaag()); opruimen(h, vandaag()); schrijf(h)
        print(len(h["p"]), "producten in de actiegeschiedenis")
    elif taak == "opbouwen":
        h = {"sinds": {}, "p": {}}
        log = subprocess.run(["git", "log", "--reverse", "--format=%H %ad", "--date=short", "--", BRON], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
        for regel in filter(None, log):
            sha, op = regel.split()
            try: d = json.loads(subprocess.run(["git", "show", f"{sha}:{BRON}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
            except Exception: continue
            voeg_toe(h, d.get("offers", []), op)
        d = json.load(open(os.path.join(ROOT, BRON))); voeg_toe(h, d.get("offers", []), vandaag())
        opruimen(h, vandaag()); schrijf(h)
        print(len(h["p"]), "producten,", h["sinds"])
