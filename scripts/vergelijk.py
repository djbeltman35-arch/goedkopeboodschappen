"""Gedeeld rekenwerk voor de paginabouwer en de prijsgeschiedenis. Was: bouwt alle pagina's van Goedkope Boodschappen in één map (standaard public/).

Gebruik: python3 scripts/bouw_paginas.py <uitmap>
Leest: <uitmap>/producten.json (Checkjebon + eigen data), data/aldi.json, data/aanbiedingen.json, data/status.json,
       scripts/cats.json en site/index.html (de app).
Maakt: startpagina, productvergelijkingen, categorieën, aanbiedingen (alle en per winkel), supermarktpagina's,
       onderlinge vergelijkingen (AH of Jumbo?), goedkoopste supermarkt, over, privacy, sitemap en robots.txt.
"""
import json, re, os, sys, html, unicodedata, datetime, itertools, statistics
from urllib.parse import quote_plus, quote
from zoneinfo import ZoneInfo

BASE = "https://goedkopeboodschappen.netlify.app"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "public")
NU = datetime.datetime.now(ZoneInfo("Europe/Amsterdam"))
VANDAAG = NU.date().isoformat()
VERSIE = NU.strftime("%d-%m-%Y %H:%M")
MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]
MAAND = f"{MAANDEN[NU.month - 1]} {NU.year}"
DAG = ["ma", "di", "wo", "do", "vr", "za", "zo"]
MND = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
def kortdag(t):
    d = datetime.date.fromisoformat(t); return f"{DAG[d.weekday()]} {d.day} {MND[d.month - 1]}"
DATUM = f"{NU.day} {MAANDEN[NU.month - 1]} {NU.year}"

NAMEN = {"ah": "Albert Heijn", "jumbo": "Jumbo", "lidl": "Lidl", "aldi": "Aldi", "plus": "PLUS", "dirk": "Dirk",
         "hoogvliet": "Hoogvliet", "dekamarkt": "DekaMarkt", "vomar": "Vomar", "spar": "SPAR", "poiesz": "Poiesz"}
KORT = {"ah": "AH"}
esc = lambda s: html.escape(str(s if s is not None else ""), quote=True)
eur = lambda v: ("€ %.2f" % v).replace(".", ",")
def tag(v, cls=""):
    return f'<span class="tag {cls}"><span class="e">€</span>{("%.2f" % v).replace(".", ",")}</span>'
def slug(t):
    t = unicodedata.normalize("NFD", t.lower()); t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")
def norm(s):
    s = unicodedata.normalize("NFD", str(s).lower()); s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9,.]+", " ", s); s = re.sub(r"(\d)[,.](\d)", r"\1,\2", s); return s.split()
def eenheid(u): return {"kg": "kilo", "l": "liter", "st": "stuk"}.get(u, "")
def per(v, u): return f"{eur(v)} per {eenheid(u)}" if v is not None and u else ""
cap = lambda t: t[:1].upper() + t[1:]

# ---------- data ----------
d = json.load(open(os.path.join(OUT, "producten.json")))
stores, prods = d["stores"], d["products"]
aldi_pad = os.path.join(ROOT, "data", "aldi.json")
if os.path.exists(aldi_pad) and not os.environ.get("ZONDER_ALDI"):
    ai = len(stores); stores.append({"id": "aldi", "name": "Aldi", "base": ""})
    for r in json.load(open(aldi_pad)).get("products", []): prods.append([ai, *r])
SIDX = {s["id"]: i for i, s in enumerate(stores)}
for s in stores: s["count"] = 0
for p in prods: stores[p[0]]["count"] += 1
ACTIEF = [s["id"] for s in stores if s["count"]]
AANTAL = len(ACTIEF)

SEARCHL = {"lidl": lambda n: "https://www.lidl.nl/q/search?q=" + quote_plus(n), "dekamarkt": lambda n: "https://www.dekamarkt.nl/zoeken?zoekterm=" + quote_plus(n)}
def plink(p):
    s = stores[p[0]]
    if str(p[2]).startswith("http"): return p[2]
    return SEARCHL[s["id"]](p[1]) if s["id"] in SEARCHL else s["base"] + p[2]

off_pad = os.path.join(ROOT, "data", "aanbiedingen.json")
if os.environ.get("ZONDER_AANBIEDINGEN"): off_pad = "/nonexistent"
OFFERS = []
if os.path.exists(off_pad):
    od = json.load(open(off_pad))
    OFFERS = [o for o in od.get("offers", []) if o.get("p") and o.get("s") in NAMEN and (not o.get("t") or o["t"] >= VANDAAG)]
    OFF_UPDATED = od.get("updated")
NU_GELDIG = [o for o in OFFERS if not o.get("v") or o["v"] <= VANDAAG]
for o in OFFERS:
    o["pct"] = (o["was"] - o["p"]) / o["was"] if o.get("was") and o["was"] > o["p"] else 0
    o["hay"] = set(norm(o["n"] + " " + (o.get("sz") or "")))

# Aanbieding koppelen aan product (zelfde logica als de app)
def pkey(p):
    sid, l = stores[p[0]]["id"], str(p[2])
    if sid == "ah": m = re.search(r"wi(\d+)", l); return "wi" + m.group(1) if m else None
    if sid == "jumbo": m = re.search(r"(\d+[A-Z]{2,4})/?$", l); return m.group(1) if m else None
    if sid == "plus": m = re.search(r"-(\d+)/?$", l); return m.group(1) if m else None
    if sid == "hoogvliet": return re.sub(r"-\d+$", "", re.sub(r"^.*/product/", "", l).rstrip("/"))
    if sid in ("dirk", "dekamarkt", "poiesz"): m = re.search(r"(\d+)/?$", l); return m.group(1) if m else None
    return None
OKEY = {(o["s"], o["k"]): o for o in NU_GELDIG if o.get("k")}
def offer_of(p):
    k = pkey(p); o = OKEY.get((stores[p[0]]["id"], k)) if k else None
    return o if o and o["p"] < p[3] - .004 else None
def eff(p):
    o = offer_of(p); return o["p"] if o else p[3]
def eff_unit(p):
    return p[5] * eff(p) / p[3] if p[5] is not None and p[3] else None

# ---------- zoeken (gelijk aan de app) ----------
ENDS = ["croissant","toetje","broodje","broodjes","flap","taart","koek","koeken","reep","repen","snack","snacks","mousse","tengels","wafels","chips","saus","drank","drink","tea","baguette","pizza","katreepjes","koekjes","salade","slaatje","hoef","loempia","servetten","carree","reiniger","muffin","muffins","kaas","mosterd"]
STARTS = ["kat", "hond"]
EXCL = set("choco chocolade gekookte spinazie roasted americanos krieltjes salade saus smaak snack snacks reep koek koekjes chips drink mix aardbei vanille banaan zuigtabletten tabletten pastilles snoepjes gummies siroop limonade thee vla yoghurt ijs sorbet shampoo douchegel zeep geurkaars kaars luchtverfrisser wasmiddel rijstwafels wafels koeken speculaaskoeken bladerdeeg kaastengels kaasstengels tengels tapenade croissant broodjes pizzabroodjes bakmix thuisbakmix mueslireep repen rooibos kat katten kattenmousse kattenvoer hond hondenvoer pate servet design cola toetje toetjes vochtig vochtige dessert pudding cake taart soep spread dip crackers biscuit ontbijtkoek drinkyoghurt ijsthee bonbons bonen vega vegan vegetarisch rulstukjes hema muesli zonnebloem granola sheba felix whiskas gourmet sauce ajax lactosevrij lactosevrije lactose biologisch biologische bio houdbaar houdbare spaghetti macaroni penne pasta noedels mayonaise gevulde bakbananen bakbanaan glutenvrij proteine protein light zero suikervrij display".split())
UNITW = set("g gr gram kg kilo l liter ml cl st stuk stuks per x ca pak pack fles blik zak naturel".split())
for p in prods:
    p.append(norm(p[1] + " " + (p[4] or "")))  # p[7] = woorden
def words(p): return sum(1 for x in p[7] if not re.match(r"^[\d,.%+]+[a-z]*$", x) and x not in UNITW)
# Woordindex: per woord de producten waarin het voorkomt (veel sneller dan alle 100.000 producten langslopen).
WOORDINDEX = {}
for _i, _p in enumerate(prods):
    for _x in set(_p[7]): WOORDINDEX.setdefault(_x, []).append(_i)
_VOCAB = list(WOORDINDEX)
_VREEMD = {}
def _vreemd_woord(x, t):
    k = (x, t)
    if k not in _VREEMD:
        _VREEMD[k] = x not in t and not any(len(w) >= 5 and x.endswith(w) for w in t) and (x in EXCL or any(x.endswith(e) and x != e.rstrip("s") for e in ENDS) or any(x.startswith(e) for e in STARTS))
    return _VREEMD[k]
VERFIJN = {k: v for k, v in json.load(open(os.path.join(ROOT, "scripts", "verfijn.json"))).items() if not k.startswith("_")}
def _verfijn(m, t):
    niet = [n for n in VERFIJN.get(" ".join(t), []) if not any(n in w for w in t)]
    return [p for p in m if not any(n in x for x in p[7] for n in niet)] if niet else m

# ---------- verpakking: blik of fles, inhoud per stuk en aantal (zelfde logica als pakInfo in de app) ----------
_MAAT = {"ml": 1, "milliliter": 1, "cl": 10, "l": 1000, "liter": 1000, "ltr": 1000, "g": 1, "gr": 1, "gram": 1, "kg": 1000, "kilo": 1000}
_MAATRE = r"(\d+(?:\.\d+)?)\s*(ml|milliliter|cl|ltr|liter|l|gram|gr|g|kg|kilo)\b"
_DRANK = {"fris", "water", "bier", "wijn"}
# Totale inhoud zonder aantal: welke verpakking is het meestal? (per soort drank)
_TOT = {"fris": {1800: (12, 150), 3960: (12, 330), 7920: (24, 330), 5000: (20, 250), 6000: (4, 1500), 9000: (6, 1500), 3000: (2, 1500)},
        "water": {9000: (6, 1500), 3000: (6, 500), 6000: (4, 1500), 4500: (3, 1500)},
        "bier": {7200: (24, 300), 6000: (24, 250), 7920: (24, 330), 12000: (24, 500), 1800: (6, 300), 1980: (6, 330), 3000: (6, 500),
                 3960: (12, 330), 3600: (12, 300), 2000: (4, 500), 2640: (6, 440), 1500: (6, 250), 1320: (4, 330), 4260: (12, 355)}}
def pakinfo(naam, eenh, soort):
    """Geeft (pak, ml per stuk, aantal) of None als de verpakking niet te bepalen is."""
    n_ = str(naam or "").lower().replace(",", "."); u_ = str(eenh or "").lower().replace(",", ".")
    s = n_ + " | " + u_
    m = re.search(r"(?:(\d+)\s*x\s*)?(\d+)\s*x\s*" + _MAATRE, s)
    if m:
        n = int(m.group(2)) * (int(m.group(1)) if m.group(1) else 1); ml = float(m.group(3)) * _MAAT[m.group(4)]
    else:
        c = re.search(r"\b(\d+)\s*[- ]?\s*(pack|pak|fles|flessen|flesjes|blikken|blikjes|st\.?|stuks)\b", n_)
        n = int(c.group(1)) if c else None
        mm = re.search(_MAATRE, u_) or re.search(_MAATRE, n_)
        if not mm:
            st = re.search(r"\b(\d+)\s*(st\.?|stuks|stuk|rollen|rol|pads|cups|capsules|zakjes|tabletten|wasbeurten|scoops|eieren)\b", u_ + " " + n_)
            return ("", 0, int(st.group(1))) if st else None
        ml = float(mm.group(1)) * _MAAT[mm.group(2)]
        if soort not in _DRANK: n = n or 1
        elif n and n > 1:
            if ml >= 900 and ml / n >= 150: ml = ml / n
        else:
            t = _TOT.get(soort, {}).get(round(ml))
            if t: n, ml = t
            elif ml > 2000 or re.search(r"\b(krat|tray|multipack|sixpack|voordeelpack)\b", n_): return None
            else: n = n or 1
    ml = round(ml)
    if soort not in _DRANK: pak = ""
    elif re.search(r"\b(blik|blikje|blikjes|blikken|can|cans)\b", n_): pak = "blik"
    elif re.search(r"\b(fles|flesje|flesjes|flessen|beugel|draaidop|twist|mono|bottle)\b", n_) or (soort == "bier" and "krat" in n_): pak = "fles"
    elif re.search(r"\b(pak|wijntap|tap|box|bag)\b", n_): pak = "pak"
    elif soort == "fris": pak = "blik" if ml <= 355 else "fles"
    elif soort == "bier": pak = "blik" if ml in (330, 355, 440, 500, 568) else "fles"
    elif soort == "wijn": pak = "fles" if ml <= 1000 else "pak"
    else: pak = "fles"
    return pak, ml, n
def is_alcoholvrij(naam):
    return bool(re.search(r"\b0[.,]0\b|alcoholvrij|alkoholfrei|alcohol ?free|\bmalt\b", str(naam).lower()))
LITERS = {}  # liters per verpakking, voor varianten: dan vergelijken we altijd per liter
VARIANT = json.load(open(os.path.join(ROOT, "scripts", "varianten.json")))
VARNORM = {" ".join(norm(k)): v for k, v in VARIANT.items()}
def _variant(v):
    seen, uit = set(), []
    for z in v["zoek"]:
        for p in matches(z, basis=True):
            if id(p) in seen: continue
            seen.add(id(p)); w = p[7]
            if any(x == n or (len(n) >= 4 and n in x) for x in w for n in v["niet"]): continue
            if v.get("wel") and not any(x == n or (len(n) >= 4 and n in x) for x in w for n in v["wel"]): continue
            if v.get("alc") == "vrij" and not is_alcoholvrij(p[1]): continue
            if v.get("alc") == "met" and is_alcoholvrij(p[1]): continue
            if v.get("ml") or v.get("n") or v.get("pak"):
                info = pakinfo(p[1], p[4], v.get("soort"))
                if not info: continue
                pak, ml, n = info
                if v.get("pak") and pak != v["pak"]: continue
                if v.get("ml") and not v["ml"][0] <= ml <= v["ml"][1]: continue
                if v.get("n") and not v["n"][0] <= n <= v["n"][1]: continue
                if v.get("soort") in _DRANK: LITERS[id(p)] = ml * n / 1000
            uit.append(p)
    return uit
def matches(term, basis=False):
    t = tuple(norm(term))
    if not t: return []
    if not basis and " ".join(t) in VARNORM: return _variant(VARNORM[" ".join(t)])
    sets = []
    for w in t:
        # Een woord past als heel woord of als eind van een samengesteld woord (scharreleieren, roomboter).
        ids = set()
        for x in ([w] if len(w) < 5 else [x for x in _VOCAB if x.endswith(w)]):
            ids.update(WOORDINDEX.get(x, ()))
        sets.append(ids)
    m = [prods[i] for i in sorted(set.intersection(*sets))]
    clean = [p for p in m if not any(_vreemd_woord(x, t) for x in p[7])]
    return _verfijn(clean or m, t)
def per_store(m):
    if not m: return {}
    mark_bad(m)
    gmin = min(words(p) for p in m); by = {}
    for p in m:
        if words(p) > gmin + 2: continue
        by.setdefault(p[0], []).append(p)
    res = {}
    for si, arr in by.items():
        mn = min(words(p) for p in arr)
        res[si] = sorted([p for p in arr if words(p) <= mn + 1], key=rank)[0]
    return res
BAD = set()
from kcal import kcal_van
def kcal_txt(t):
    k = kcal_van(t)
    if not k: return ""
    return f"{k[0]} kcal per {k[1]}"
def kcal_pak(t, p):
    """Ongeveer aantal kcal in de hele verpakking (als we de inhoud kennen)."""
    k = kcal_van(t)
    if not k or k[1] == "kopje" or not k[0]: return None
    l = LITERS.get(id(p))
    if l: tot = l * 1000
    else:
        i = pakinfo(p[1], p[4], None)
        if not i or not i[1]: return None
        tot = i[1] * i[2]
    if tot <= 0 or tot > 25000: return None
    return round(k[0] * tot / 100 / 10) * 10
def toon_unit(p):
    """Prijs per eenheid zoals we die tonen: bij drankverpakkingen altijd per liter."""
    l = LITERS.get(id(p))
    return (eff(p) / l, "l") if l else (eff_unit(p), p[6])
def vgl_unit(p):
    l = LITERS.get(id(p))
    return eff(p) / l if l else eff_unit(p)
def mark_bad(arr):
    # Een prijs per kilo of liter die ver van de rest afwijkt, komt bijna altijd door een verkeerde maat in de data.
    u = sorted(v for v in (vgl_unit(p) for p in arr) if v is not None)
    if len(u) < 3: return
    med = u[len(u) // 2]
    for p in arr:
        v = vgl_unit(p)
        if v is not None and (v > med * 3 or v < med / 3): BAD.add(id(p))
def rank(p):
    if id(p) in BAD: return 1e6 + eff(p)
    u = vgl_unit(p)
    return u if u is not None else eff(p) * 1000

CATS = json.load(open(os.path.join(ROOT, "scripts", "cats.json")))
TERMS = []
for c in CATS:
    for t in c[2]:
        if t not in TERMS: TERMS.append(t)
CATOF = {}
for c in CATS:
    for t in c[2]: CATOF.setdefault(t, c)
GROEPEN = json.load(open(os.path.join(ROOT, "scripts", "groepen.json")))
GROEPICOON = {g: i for g, i in GROEPEN}
SUBS = {g: [c for c in CATS if c[3] == g] for g, _ in GROEPEN}

# ---------- aanbiedingen indelen in dezelfde (sub)categorieën als de producten ----------
_SUBTERMEN = []  # (categorie, woorden van de zoekterm, uitsluitwoorden)
for _c in CATS:
    for _t in _c[2]:
        _k = " ".join(norm(_t))
        for _z in (VARNORM[_k]["zoek"] if _k in VARNORM else [_t]):
            _w = tuple(norm(_z))
            if _w: _SUBTERMEN.append((_c, _w, [n for n in VERFIJN.get(" ".join(_w), []) if not any(n in x for x in _w)], _t))
def subcat_van(naam, groep):
    """Beste subcategorie voor een aanbieding: (categorie, aantal woorden, zoekterm) van de meest specifieke zoekterm die past, binnen de eigen hoofdgroep."""
    ws = set(norm(naam)); beste = None
    pas = lambda w: w in ws or (len(w) >= 5 and any(x.endswith(w) for x in ws))
    for c, tw, niet, term in _SUBTERMEN:
        if groep != "Overig" and c[3] != groep: continue
        if not all(pas(w) for w in tw) or any(n in x for x in ws for n in niet): continue
        if beste is None or len(tw) > beste[1]: beste = (c, len(tw), term)
    return beste

PICKED = {}
for t in TERMS:
    rows = sorted(per_store(matches(t)).items(), key=lambda kv: rank(kv[1]))
    if rows: PICKED[t] = rows

def term_offers(t, n=6):
    w = [x for x in norm(t) if len(x) > 1]
    m = [o for o in NU_GELDIG if all(any(h == x or (len(x) >= 5 and h.endswith(x)) for h in o["hay"]) for x in w) and not any(h in EXCL and h not in w for h in o["hay"])
         and sum(1 for h in o["hay"] if not re.match(r"^[\d,.%+]+[a-z]*$", h) and h not in UNITW) <= len(w) + 3]
    m.sort(key=lambda o: (o.get("pp") or o["p"] * 1000))
    return m[:n]

# ---------- basispakket: goedkoopste supermarkt ----------
# Vaste hoeveelheden, zodat elke winkel voor precies dezelfde boodschappen wordt doorgerekend.
PAKKET = [("halfvolle melk", 2, "l"), ("yoghurt", 1, "l"), ("eieren", 10, "st"), ("roomboter", .25, "kg"), ("jonge kaas", .5, "kg"),
          ("ham", .15, "kg"), ("volkoren brood", .8, "kg"), ("pindakaas", .35, "kg"), ("hagelslag", .4, "kg"), ("jam", .45, "kg"),
          ("bananen", 1, "kg"), ("appels", 1, "kg"), ("aardappelen", 2, "kg"), ("uien", 1, "kg"), ("tomaten", .5, "kg"),
          ("komkommer", 1, "st"), ("paprika", .5, "kg"), ("wortels", 1, "kg"), ("kipfilet", .5, "kg"), ("gehakt", .5, "kg"),
          ("rijst", 1, "kg"), ("spaghetti", .5, "kg"), ("pastasaus", .5, "kg"), ("olijfolie", .5, "l"), ("suiker", 1, "kg"),
          ("koffiebonen", .5, "kg"), ("thee", 20, "st"), ("sinaasappelsap", 1.5, "l"), ("cola", 1.5, "l"), ("chips", .2, "kg"),
          ("toiletpapier", 8, "st"), ("wasmiddel", 1, "l"), ("tandpasta", .075, "l"), ("afwasmiddel", .5, "l")]
# Andere eenheden waarin winkels hetzelfde verkopen (komkommer per stuk of per kilo, appels per kilo of per stuk).
OMREKEN = {"komkommer": {"kg": .4}, "appels": {"st": 6}, "uien": {"st": 8}, "bananen": {"st": 6}, "roomboter": {"st": 1},
           "thee": {"kg": .04}, "volkoren brood": {"st": 1}, "tomaten": {"st": 5}, "paprika": {"st": 3}, "eieren": {}}
def pakket_kosten():
    tabel = {}
    for term, q, u in PAKKET:
        rows = dict(per_store(matches(term)).items())
        for si, p in rows.items():
            if id(p) in BAD or eff_unit(p) is None or not 0 < eff_unit(p) < 500: continue
            if p[6] == u: tabel.setdefault(term, {})[si] = (eff_unit(p) * q, p)
            elif p[6] in OMREKEN.get(term, {}): tabel.setdefault(term, {})[si] = (eff_unit(p) * OMREKEN[term][p[6]], p)
    # Eerlijk vergelijken: alleen boodschappen die bij álle meegenomen winkels te vinden zijn.
    # Winkels die te veel missen vallen af, tot er minstens 18 gemeenschappelijke boodschappen over zijn.
    winkels = [si for si, s in enumerate(stores) if s["count"] and sum(1 for t in tabel if si in tabel[t]) >= 0.75 * len(PAKKET)]
    while True:
        termen = [t for t, _, _ in PAKKET if t in tabel and all(si in tabel[t] for si in winkels)]
        if len(termen) >= 15 or len(winkels) <= 3: break
        winkels.remove(min(winkels, key=lambda si: sum(1 for t in tabel if si in tabel[t])))
    res = []
    for si in winkels:
        regels = [(t, tabel[t][si][0], tabel[t][si][1], False) for t in termen]
        res.append({"si": si, "tot": sum(r[1] for r in regels), "mist": 0, "regels": regels})
    res.sort(key=lambda r: r["tot"])
    return res, termen
PAK, PAKTERMEN = pakket_kosten()
if os.environ.get('DEBUG_PAKKET'):
    _t = {}
    for term, q, u in PAKKET:
        for si, p in per_store(matches(term)).items():
            ok = p[6] == u and eff_unit(p) is not None
            _t.setdefault(stores[si]['id'], []).append(term if ok else term.upper()+'('+str(p[6])+')')
    for k, v in _t.items(): print(k, len([x for x in v if x.islower()]), v)
PAKRANG = {r["si"]: i + 1 for i, r in enumerate(PAK)}

