"""Rekent per complete maaltijd uit wat hij bij elke supermarkt kost (naar gebruikte hoeveelheid) en hoeveel calorieën hij heeft.
Wordt geïmporteerd door bouw_paginas.py na vergelijk.py."""
from vergelijk import *
from maaltijden import I, MAALTIJDEN, SOORTEN, NOTITIE, NIET_ALGEMEEN, BEREIK

def _toegestaan(p, termwoorden, niet):
    for x in p[7]:
        for f in NIET_ALGEMEEN + niet:
            if f in x and not any(f in t for t in termwoorden): return False
    return True

def eenheidsprijs(p):
    """(prijs per kg/l/stuk, eenheid). Producten die 'per stuk' verkocht worden zonder maat krijgen de stukprijs."""
    v = eff_unit(p)
    if v is not None and p[6]: return v, p[6]
    if re.search(r"(per|^1)\s*stuks?\b", (p[4] or "").lower()): return eff(p), "st"
    return None, None

def ingredient_prijzen(sleutel, q):
    """Per winkel: (kosten voor hoeveelheid q, product) van het voordeligste passende product."""
    termen, _, stuk, niet = I[sleutel]
    niet = [norm(n)[0] if " " not in n else n for n in niet]
    best = {}
    for term in termen:
        tw = norm(term)
        lo, hi = BEREIK.get(sleutel, (0, 200))
        def ok(p):
            v, u = eenheidsprijs(p)
            if v is None or not _toegestaan(p, tw, niet): return False
            return lo <= v <= hi if u in ("kg", "l") else (not stuk or lo <= v / stuk <= hi)
        kand = [p for p in matches(term) if ok(p)]
        for si, p in per_store(kand).items():
            v, u = eenheidsprijs(p)
            if id(p) in BAD: continue
            if u in ("kg", "l"): kost = v * q
            elif u == "st" and stuk: kost = v * q / stuk
            else: continue
            if si not in best or kost < best[si][0] - 1e-9: best[si] = (kost, p)
    return best

def bereken(m):
    regels, kcal, winkels = [], 0, {}
    for r in m["ing"]:
        sleutel, q, naam = r[0], r[1], r[2]
        extra = r[3] if len(r) > 3 else ""
        k100 = r[4] if extra == "v" else I[sleutel][1]
        kcal += q * 1000 * k100 / 100
        regels.append({"sleutel": sleutel, "q": q, "naam": naam, "voorraad": extra == "v", "optioneel": extra == "o",
                       "prijzen": {} if extra == "v" else ingredient_prijzen(sleutel, q)})
    nodig = [g for g in regels if not g["voorraad"] and not g["optioneel"]]
    for si, s in enumerate(stores):
        if not s["count"]: continue
        if not all(si in g["prijzen"] for g in nodig): continue
        tot = 0; lijst = []
        for g in regels:
            if g["voorraad"]: continue
            if si in g["prijzen"]:
                k, p = g["prijzen"][si]; tot += k; lijst.append((g["naam"], k, p))
            else: lijst.append((g["naam"], None, None))
        winkels[si] = {"tot": tot, "regels": lijst}
    por = m.get("porties", 4)
    for w in winkels.values(): w["tot"] = w["tot"] * 4 / por
    rang = sorted(winkels.items(), key=lambda kv: kv[1]["tot"])
    return {"kcal": round(kcal / por / 5) * 5, "rang": rang, "regels": regels}

MAAL = []
for m in MAALTIJDEN:
    b = bereken(m)
    if len(b["rang"]) >= 3: MAAL.append({**m, **b})

if __name__ == "__main__":
    for m in MAAL:
        print(f"\n{m['naam']} ({m['kcal']} kcal) – {len(m['rang'])} winkels: " + ", ".join(f"{stores[si]['id']} {r['tot']:.2f}" for si, r in m['rang']))
        for si, r in m["rang"][:3]:
            print("  ", stores[si]["id"], " | ".join(f"{n}: {p[1][:26] if p else '-'} {k:.2f}" if p else f"{n}: -" for n, k, p in r["regels"]))
    for m in MAALTIJDEN:
        if m["slug"] in {x["slug"] for x in MAAL}: continue
        b = bereken(m); print("\nTE WEINIG:", m["naam"], {g["naam"]: sorted(stores[si]["id"] for si in g["prijzen"]) for g in b["regels"] if not g["voorraad"]})
    weg = [m["naam"] for m in MAALTIJDEN if m["slug"] not in {x["slug"] for x in MAAL}]
    print("\nTe weinig winkels:", weg)
