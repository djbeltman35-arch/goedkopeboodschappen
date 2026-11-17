"""Houdt per winkel bij wanneer de gewone prijzen in het open prijzenbestand van Checkjebon voor het laatst zijn veranderd.

  python3 scripts/bronstatus.py <supermarkets.json>

data/bronstatus.json: {winkel: {"hash": ..., "sinds": "JJJJ-MM-DD"}}. "sinds" is de laatste dag waarop er iets aan de
prijzen van die winkel veranderde. Staat dat lang stil, dan zijn de prijzen verouderd (de build toont dat en vervangt ze
waar mogelijk door eigen gegevens, zie scripts/eigen_prijzen.py).
"""
import hashlib, json, os, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAD = os.path.join(ROOT, "data", "bronstatus.json")
vandaag = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).date().isoformat()
d = json.load(open(sys.argv[1]))
try: st = json.load(open(PAD))
except Exception: st = {}
for s in d:
    h = hashlib.md5(json.dumps(s.get("d", []), sort_keys=True).encode()).hexdigest()
    oud = st.get(s["n"])
    if not oud or oud.get("hash") != h:
        st[s["n"]] = {"hash": h, "sinds": vandaag}
json.dump(st, open(PAD, "w"), indent=0, sort_keys=True)
print({k: v["sinds"] for k, v in st.items()})
