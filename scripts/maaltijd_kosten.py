"""Rekent per complete maaltijd uit wat hij bij elke supermarkt kost (hele verpakkingen, zoals aan de kassa; plus wat je ervan gebruikt) en hoeveel calorieën hij heeft.
Wordt geïmporteerd door bouw_paginas.py na vergelijk.py."""
from vergelijk import *
import math
from maaltijden import I, MAALTIJDEN, SOORTEN, NOTITIE, NIET_ALGEMEEN, BEREIK, GLUTEN, LET_OP, GLUTEN_WOORDEN, LET_OP_WOORDEN

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
    """Per winkel: (kassaprijs, product, aantal verpakkingen, kosten van wat je gebruikt).
    Kassaprijs = hele verpakkingen die je moet kopen om genoeg te hebben; per winkel de goedkoopste verpakking die volstaat."""
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
        if not kand: continue
        # Uitschieters weghalen op prijs per kilo/liter (stukprijzen omgerekend met het gewicht per stuk).
        def pkg(p):
            v, u = eenheidsprijs(p)
            return v if u in ("kg", "l") else (v / stuk if stuk else None)
        np_ = sorted(x for x in (pkg(p) for p in kand) if x)
        if len(np_) >= 3:
            med = np_[len(np_) // 2]
            kand = [p for p in kand if pkg(p) is None or med / 4 <= pkg(p) <= med * 4]
        gmin = min(words(p) for p in kand)
        per = {}
        for p in kand:
            if words(p) <= gmin + 4: per.setdefault(p[0], []).append(p)
        for si, arr in per.items():
            mn = min(words(p) for p in arr)
            for p in arr:
                if words(p) > mn + 1: continue
                v, u = eenheidsprijs(p)
                if u in ("kg", "l"): nodig = q
                elif u == "st" and stuk: nodig = q / stuk
                else: continue
                inhoud = eff(p) / v if v else 0          # hoeveelheid in één verpakking (kg, l of stuks)
                if inhoud <= 0: continue
                n = max(1, math.ceil(nodig / inhoud - 0.05))  # 5% speling: 480 g in een pak van 500 g telt als 1 pak
                kassa, gebruik = n * eff(p), v * nodig
                if si not in best or kassa < best[si][0] - 1e-9 or (abs(kassa - best[si][0]) < 1e-9 and gebruik < best[si][3]):
                    best[si] = (kassa, p, n, gebruik)
    return best

def bereken(m):
    regels, kcal, winkels = [], 0, {}
    schaal = 4 / m.get("porties", 4)   # recepten voor meer personen omrekenen naar 4
    for r in m["ing"]:
        sleutel, q, naam = r[0], r[1] * schaal, r[2]
        extra = r[3] if len(r) > 3 else ""
        k100 = r[4] if extra == "v" else I[sleutel][1]
        kcal += q * 1000 * k100 / 100
        regels.append({"sleutel": sleutel, "q": q, "naam": naam, "voorraad": extra == "v", "optioneel": extra == "o",
                       "prijzen": {} if extra == "v" else ingredient_prijzen(sleutel, q)})
    nodig = [g for g in regels if not g["voorraad"] and not g["optioneel"]]
    for si, s in enumerate(stores):
        if not s["count"]: continue
        if not all(si in g["prijzen"] for g in nodig): continue
        tot = gebruik = 0; lijst = []
        for g in regels:
            if g["voorraad"]: continue
            if si in g["prijzen"]:
                k, p, n, gb = g["prijzen"][si]; tot += k; gebruik += gb; lijst.append((g["naam"], k, p, n, gb))
            else: lijst.append((g["naam"], None, None, 0, 0))
        winkels[si] = {"tot": tot, "gebruik": gebruik, "regels": lijst}
    rang = sorted(winkels.items(), key=lambda kv: kv[1]["tot"])
    return {"kcal": round(kcal / 4 / 5) * 5, "rang": rang, "regels": regels}

def gluten(m):
    """("vrij" | "bevat", lijst met ingrediënten waarvan je een glutenvrije variant moet kiezen)."""
    bevat, let = False, []
    for r in m["ing"]:
        sleutel, naam, voorraad = r[0], r[2], len(r) > 3 and r[3] == "v"
        tekst = naam.lower()
        if (not voorraad and sleutel in GLUTEN) or (voorraad and any(w in tekst for w in GLUTEN_WOORDEN)): bevat = True
        elif (not voorraad and sleutel in LET_OP): let.append(naam.split(" (")[0].lower())
        elif voorraad:
            let += [w for w in LET_OP_WOORDEN if w in tekst]
    return ("bevat" if bevat else "vrij"), sorted(set(let))

# Eiwit per 100 gram van de ingrediënten (NEVO-richtwaarden), voor het label eiwitrijk.
EIWIT_ING = {"gehakt": 18, "rundergehakt": 20, "kipfilet": 23, "kipdijfilet": 19, "kipfilet stuks": 23, "kipfiletblokjes": 23, "kalkoenfilet": 23,
    "zalm": 20, "tonijn": 25, "kabeljauw": 18, "gerookte vis": 21, "gerookte kip": 22, "kippenbouten": 17, "rookworst": 12, "spekreepjes": 15,
    "ontbijtspek": 13, "ham": 18, "eieren": 12.5, "eidooiers": 13, "geraspte kaas": 25, "parmezaanse kaas": 33, "parmezaanse snippers": 33,
    "pecorino": 30, "feta": 15, "mozzarella": 18, "geitenkaas": 12, "ricotta": 8, "halfvolle melk": 3.5, "yoghurt": 4, "griekse yoghurt": 6,
    "kookroom": 2.5, "slagroom": 2, "creme fraiche": 2.5, "roomkaas kruiden": 6, "biefstuk": 21, "runderlappen": 20, "vega gehakt": 15,
    "vegan gehakt": 15, "plantaardige burger": 15, "vegan worst": 14, "vegan spekjes": 12, "tofu": 12, "rode linzen": 24, "blonde linzen": 24,
    "linzen gekookt": 9, "kikkererwten": 7, "kidneybonen": 7, "zwarte bonen": 7, "witte bonen": 7, "bruine bonen": 7, "bonenmix": 7, "edamame": 11,
    "spliterwten": 22, "doperwten": 5, "tuinbonen": 6, "quinoa": 14, "rijst": 7, "zilvervliesrijst": 7.5, "risottorijst": 7, "paellarijst": 7,
    "pasta": 12, "penne": 12, "spaghetti": 12, "macaroni": 12, "volkorenpasta": 13, "volkorenspaghetti": 13, "orzo": 12, "lasagnebladen": 12,
    "mie": 11, "rijstnoedels": 6, "woknoedels": 5, "volkoren noedels": 12, "couscous": 12, "bulgur": 12, "aardappelen": 2, "krieltjes": 2,
    "zoete aardappel": 1.6, "aardappelschijfjes": 2, "pindakaas": 25, "pinda": 26, "cashewnoten": 18, "broccoli": 3, "spinazie": 2.5,
    "volkorenbrood": 10, "stokbrood": 9, "pitabroodjes": 9, "volkoren pita": 10, "tortilla wraps": 8, "volkoren wraps": 9, "focaccia": 8,
    "croutons": 11, "sesamzaad": 18, "pijnboompitten": 14, "amandelschaafsel": 21, "spruitjes": 3.5, "boerenkool": 3, "champignons": 3}
def eiwit(m):
    schaal = 4 / m.get("porties", 4); g = 0
    for r in m["ing"]:
        if len(r) > 3 and r[3] == "v": continue
        k = r[0]; e = EIWIT_ING.get(k)
        if e is None: e = 1.2 if (I[k][1] or 0) < 60 else 3
        g += r[1] * schaal * 1000 * e / 100
    return round(g / 4)
# Zuivel (lactose) in de ingrediënten; voor het label lactosevrij.
ZUIVEL = {"halfvolle melk", "roomboter", "kookroom", "slagroom", "creme fraiche", "yoghurt", "griekse yoghurt", "geraspte kaas", "parmezaanse kaas",
          "parmezaanse snippers", "pecorino", "feta", "mozzarella", "geitenkaas", "ricotta", "roomkaas kruiden", "zure room", "besciamelsaus", "pesto",
          "tzatziki", "caesar dressing", "mayonaise", "kruidnoten", "croutons", "volkorenbrood", "stokbrood", "pannenkoeken"}
ZUIVEL_WOORDEN = ("melk", "boter", "room", "kaas", "yoghurt", "kwark")
def lactosevrij(m):
    for r in m["ing"]:
        if len(r) > 3 and r[3] == "o": continue  # optioneel: laat je gewoon weg
        if len(r) > 3 and r[3] == "v":
            n = re.sub(r"\(?plantaardige?\)?\s*\w*|vloeibare margarine|margarine|kokosmelk|amandeldrink", "", r[2].lower())
            if any(w in n for w in ZUIVEL_WOORDEN): return False
        elif r[0] in ZUIVEL: return False
    return True
# Halal en koosjer: geen varkensvlees en geen alcohol; koosjer ook geen vlees samen met zuivel. Vlees moet wel halal of koosjer zijn (staat op de pagina).
VARKEN = {"spekreepjes", "ontbijtspek", "ham", "rookworst"}
VLEES = {"gehakt", "rundergehakt", "kipfilet", "kipdijfilet", "kipfilet stuks", "kipfiletblokjes", "kalkoenfilet", "biefstuk", "runderlappen",
         "kippenbouten", "gerookte kip", "rookworst", "spekreepjes", "ontbijtspek", "ham"}
ALCOHOL = ("wijn", "bier", "rum", "cognac", "port", "sherry")
def _actief(m):
    for r in m["ing"]:
        if len(r) > 3 and r[3] == "o": continue
        yield r
def halal(m):
    for r in _actief(m):
        if r[0] in VARKEN: return False
        n = r[2].lower()
        if any(re.search(r"\b" + w + r"\b", n) for w in ALCOHOL) and "azijn" not in n: return False
        if r[0] == "gehakt" and "lams" not in n and "rund" not in n: pass  # gemengd gehakt: op de pagina staat 'kies halal rundergehakt'
    return True
def koosjer(m):
    if not halal(m): return False
    vlees = any(r[0] in VLEES for r in _actief(m))
    return not (vlees and not lactosevrij(m))
# Welk vlees of welke vis zit erin? (gemengd gehakt is rund en varken)
DIERSOORT = {"kip": {"kipfilet", "kipdijfilet", "kipfilet stuks", "kipfiletblokjes", "kalkoenfilet", "kippenbouten", "gerookte kip"},
             "rund": {"rundergehakt", "biefstuk", "runderlappen", "gehakt"},
             "varken": {"spekreepjes", "ontbijtspek", "ham", "rookworst", "gehakt"},
             "vis": {"zalm", "tonijn", "kabeljauw", "gerookte vis"}}
def diersoorten(m):
    ks = {r[0] for r in _actief(m)}
    uit = {d for d, keys in DIERSOORT.items() if ks & keys}
    # gehakt waarvan de naam zegt dat het rund of lam is: geen varken
    if "varken" in uit and not (ks & (DIERSOORT["varken"] - {"gehakt"})):
        if all(("rund" in r[2].lower() or "lams" in r[2].lower()) for r in _actief(m) if r[0] == "gehakt"): uit.discard("varken")
    return sorted(uit)
MAAL = []
for m in MAALTIJDEN:
    b = bereken(m)
    gv, gl = gluten(m)
    if len(b["rang"]) >= 3:
        e = eiwit(m)
        MAAL.append({**m, **b, "glutenvrij": gv == "vrij", "gv_let": gl, "eiwit": e, "eiwitrijk": e >= 30 and e * 4 >= .2 * b["kcal"], "lactosevrij": lactosevrij(m), "halal": halal(m), "koosjer": koosjer(m), "dier": diersoorten(m)})

if __name__ == "__main__":
    for m in MAAL:
        print(f"\n{m['naam']} ({m['kcal']} kcal) – {len(m['rang'])} winkels: " + ", ".join(f"{stores[si]['id']} {r['tot']:.2f}" for si, r in m['rang']))
        for si, r in m["rang"][:3]:
            print("  ", stores[si]["id"], " | ".join(f"{n}: {nn}x {p[1][:26]} {k:.2f}" if p else f"{n}: -" for n, k, p, nn, gb in r["regels"]))
    for m in MAALTIJDEN:
        if m["slug"] in {x["slug"] for x in MAAL}: continue
        b = bereken(m); print("\nTE WEINIG:", m["naam"], {g["naam"]: sorted(stores[si]["id"] for si in g["prijzen"]) for g in b["regels"] if not g["voorraad"]})
    weg = [m["naam"] for m in MAALTIJDEN if m["slug"] not in {x["slug"] for x in MAAL}]
    print("\nTe weinig winkels:", weg)
