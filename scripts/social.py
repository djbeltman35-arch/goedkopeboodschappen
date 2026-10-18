"""Maakt elke dag de afbeeldingen en teksten voor sociale media (Instagram en Facebook).

Gebruik: python3 scripts/social.py   (na het ophalen van de aanbiedingen)
Schrijft naar data/social/:
  - aanbiedingen-JJJJ-MM-DD.png  de 5 beste aanbiedingen van vandaag (1080x1350, staand formaat voor Instagram)
  - week-JJJJ-MM-DD.png          (alleen op maandag) de grootste kortingen per supermarkt
  - vandaag.json                 teksten en afbeeldingslinks voor de berichten van vandaag
Oude afbeeldingen (ouder dan 10 dagen) worden opgeruimd.
"""
import json, os, re, datetime, glob, urllib.request
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "social")
SITE = "https://goedkopeboodschappen.netlify.app"
NU = datetime.datetime.now(ZoneInfo("Europe/Amsterdam"))
VANDAAG = NU.date().isoformat()
DAGEN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]
NAMEN = {"ah": "Albert Heijn", "jumbo": "Jumbo", "lidl": "Lidl", "aldi": "Aldi", "plus": "PLUS", "dirk": "Dirk",
         "hoogvliet": "Hoogvliet", "dekamarkt": "DekaMarkt", "poiesz": "Poiesz"}
GROEN, DONKER, GEEL, ROOD, PAGINA, WIT, GRIJS = "#0e7c4a", "#1e2a22", "#ffd43b", "#e0472f", "#f4f7f1", "#ffffff", "#5d6a61"
eur = lambda v: ("€ %.2f" % v).replace(".", ",")

# ---------- lettertypes: die van de site, anders DejaVu ----------
FONTDIR = os.path.join(ROOT, "scripts", "fonts")
BRON = {"tekst": "https://github.com/google/fonts/raw/main/ofl/atkinsonhyperlegible/AtkinsonHyperlegible-Bold.ttf",
        "tekst-r": "https://github.com/google/fonts/raw/main/ofl/atkinsonhyperlegible/AtkinsonHyperlegible-Regular.ttf",
        "getal": "https://github.com/google/fonts/raw/main/ofl/barlowcondensed/BarlowCondensed-Bold.ttf"}
def lettertype(soort, grootte):
    os.makedirs(FONTDIR, exist_ok=True)
    pad = os.path.join(FONTDIR, soort + ".ttf")
    if not os.path.exists(pad):
        try: urllib.request.urlretrieve(BRON[soort], pad)
        except Exception: pass
    for p in [pad, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if soort != "tekst-r" else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        try: return ImageFont.truetype(p, grootte)
        except Exception: continue
    return ImageFont.load_default()

def afbreken(tekst, font, breedte, draw, max_regels=2):
    woorden, regels, regel = tekst.split(), [], ""
    for w in woorden:
        test = (regel + " " + w).strip()
        if draw.textlength(test, font=font) <= breedte: regel = test
        else:
            if regel: regels.append(regel)
            regel = w
    if regel: regels.append(regel)
    if len(regels) > max_regels:
        regels = regels[:max_regels]
        while draw.textlength(regels[-1] + "…", font=font) > breedte and " " in regels[-1]: regels[-1] = regels[-1].rsplit(" ", 1)[0]
        regels[-1] += "…"
    return regels

def prijskaartje(draw, x, y, prijs, rood=False, grootte=64):
    f = lettertype("getal", grootte); fe = lettertype("getal", int(grootte * .6))
    t = ("%.2f" % prijs).replace(".", ",")
    w = draw.textlength(t, font=f) + draw.textlength("€", font=fe) + 34
    h = int(grootte * 1.15)
    draw.rounded_rectangle([x - w, y, x, y + h], radius=10, fill=ROOD if rood else GEEL)
    draw.rectangle([x - w, y + h - 6, x, y + h], fill="#c63a25" if rood else "#e6bd2e")
    kleur = WIT if rood else DONKER
    draw.text((x - w + 14, y + h * .30), "€", font=fe, fill=kleur)
    draw.text((x - w + 18 + draw.textlength("€", font=fe), y + h * .06), t, font=f, fill=kleur)
    return w

def logo(img, x, y, maat):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x, y, x + maat, y + maat], radius=int(maat * .22), fill=GROEN)
    s = maat / 512
    pts = [(84, 156), (136, 156), (178, 338), (376, 338), (414, 200), (160, 200)]
    d.line([(x + a * s, y + b * s) for a, b in pts], fill=WIT, width=max(3, int(34 * s)), joint="curve")
    for cx in (204, 352): d.ellipse([x + (cx - 30) * s, y + 374 * s, x + (cx + 30) * s, y + 434 * s], fill=WIT)
    d.rounded_rectangle([x + 300 * s, y + 70 * s, x + 464 * s, y + 174 * s], radius=int(16 * s), fill=GEEL)

def kaart(titel, sub, regels, voet, bestand):
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), PAGINA); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 210], fill=GROEN)
    logo(img, 60, 50, 110)
    d.text((196, 58), "Goedkope Boodschappen", font=lettertype("tekst", 44), fill=WIT)
    d.text((196, 116), sub, font=lettertype("tekst-r", 32), fill="#d8eee2")
    y = 250
    for r in afbreken(titel, lettertype("tekst", 62), W - 120, d, 2):
        d.text((60, y), r, font=lettertype("tekst", 62), fill=DONKER); y += 74
    y += 18
    hoogte = (H - 140 - y) / max(1, len(regels))
    for i, o in enumerate(regels):
        top = y + i * hoogte
        d.rounded_rectangle([40, top + 6, W - 40, top + hoogte - 10], radius=22, fill=WIT, outline="#e1e7dc", width=2)
        winkel = NAMEN.get(o["s"], o["s"])
        fs = lettertype("tekst", 28)
        bw = d.textlength(winkel, font=fs) + 28
        d.rounded_rectangle([70, top + 28, 70 + bw, top + 72], radius=10, fill="#e2f2e8")
        d.text((84, top + 33), winkel, font=fs, fill="#0a6239")
        if o.get("lbl"):
            fl = lettertype("tekst", 26); lw = d.textlength(o["lbl"], font=fl) + 24
            d.rounded_rectangle([80 + bw, top + 30, 80 + bw + lw, top + 70], radius=10, fill="#fde9e5")
            d.text((92 + bw, top + 35), o["lbl"], font=fl, fill=ROOD)
        pw = prijskaartje(d, W - 70, top + 26, o["p"], rood=True, grootte=58)
        naam = o["n"] + (" " + o["sz"] if o.get("sz") and o["sz"].lower() not in o["n"].lower() else "")
        fn = lettertype("tekst", 34)
        ny = top + 86
        for r in afbreken(naam, fn, W - 140 - pw - 40, d, 2 if hoogte > 200 else 1):
            d.text((70, ny), r, font=fn, fill=DONKER); ny += 42
        if o.get("was"):
            fw = lettertype("getal", 34); t = eur(o["was"])
            tw = d.textlength(t, font=fw)
            d.text((W - 70 - tw, top + 98), t, font=fw, fill=GRIJS)
            d.line([(W - 72 - tw, top + 118), (W - 68, top + 118)], fill=GRIJS, width=3)
    d.rectangle([0, H - 110, W, H], fill=DONKER)
    fv = lettertype("tekst", 38)
    while d.textlength(voet, font=fv) > W - 120 and fv.size > 24: fv = lettertype("tekst", fv.size - 2)
    d.text(((W - d.textlength(voet, font=fv)) / 2, H - 82), voet, font=fv, fill=GEEL)
    img.save(bestand, optimize=True)

# ---------- keuze van de aanbiedingen ----------
d = json.load(open(os.path.join(ROOT, "data", "aanbiedingen.json")))
nu = [o for o in d["offers"] if o.get("p") and (not o.get("v") or o["v"] <= VANDAAG) and (not o.get("t") or o["t"] >= VANDAAG) and o.get("s") in NAMEN]
ETEN = {"Zuivel en eieren", "Kaas", "Vleeswaren en tapas", "Brood en ontbijt", "Broodbeleg", "Groente en aardappelen", "Fruit", "Vlees en vis", "Pasta, rijst en wereldkeuken", "Soep, conserven en bakken", "Sauzen, olie en kruiden", "Diepvries", "Koffie en thee", "Frisdrank en sap", "Koek en snoep", "Chips en noten", "Huishouden"}
def score(o):
    pct = (o["was"] - o["p"]) / o["was"] if o.get("was") and o["was"] > o["p"] else 0
    if pct > .8: pct = 0  # onwaarschijnlijke "van"-prijs
    return pct + (.15 if o.get("c") in ETEN else 0) + (.05 if o.get("lbl") else 0)
def beste(lst, n, per_winkel=1, uitsluiten=()):
    gekozen, tel, namen = [], {}, set()
    for o in sorted(lst, key=score, reverse=True):
        if o["s"] in uitsluiten or tel.get(o["s"], 0) >= per_winkel: continue
        k = re.sub(r"[^a-z]", "", (o["n"].lower().split() or [""])[0])  # één keer per merk (niet 3x Robijn)
        if k in namen: continue
        gekozen.append(o); tel[o["s"]] = tel.get(o["s"], 0) + 1; namen.add(k)
        if len(gekozen) == n: break
    return gekozen

os.makedirs(OUT, exist_ok=True)
for f in glob.glob(os.path.join(OUT, "*.png")):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", f)
    if m and (NU.date() - datetime.date.fromisoformat(m.group(1))).days > 10: os.remove(f)

datum = f"{DAGEN[NU.weekday()]} {NU.day} {MAANDEN[NU.month - 1]}"
# Elke dag een ander thema, zodat de berichten niet steeds hetzelfde zijn.
THEMA = [("Nieuwe week, nieuwe aanbiedingen", None), ("Goedkoop koken vandaag", {"Vlees en vis", "Pasta, rijst en wereldkeuken", "Groente en aardappelen", "Soep, conserven en bakken", "Sauzen, olie en kruiden"}),
         ("Voordelig ontbijt en lunch", {"Brood en ontbijt", "Broodbeleg", "Zuivel en eieren", "Kaas", "Vleeswaren en tapas", "Fruit"}), ("Grootste kortingen van vandaag", None),
         ("Weekendboodschappen voor minder", {"Bier en wijn", "Frisdrank en sap", "Chips en noten", "Koek en snoep", "Vlees en vis", "Vleeswaren en tapas"}), ("Zaterdag: dit is nu het goedkoopst", None),
         ("Alvast voor volgende week", {"Huishouden", "Verzorging en baby", "Koffie en thee", "Zuivel en eieren"})]
thema, cats = THEMA[NU.weekday()]
pool = [o for o in nu if not cats or o.get("c") in cats] or nu
top = beste(pool, 5)
posts = []
if top:
    png = f"aanbiedingen-{VANDAAG}.png"
    kaart(thema, f"De beste aanbiedingen van {datum}", top, "goedkopeboodschappen.netlify.app", os.path.join(OUT, png))
    regels = "\n".join(f"🛒 {NAMEN[o['s']]}: {o['n']} voor {eur(o['p'])}" + (f" (was {eur(o['was'])})" if o.get("was") else "") for o in top)
    tekst = (f"{thema} 💰\n\nDe beste aanbiedingen van {datum}:\n\n{regels}\n\n"
             f"Bekijk alle {len(nu)} aanbiedingen van {len(set(o['s'] for o in nu))} supermarkten en zie waar jouw boodschappenlijst het goedkoopst is. Gratis en zonder reclame.\n"
             f"👉 {SITE}/aanbiedingen/\n\n#aanbiedingen #boodschappen #besparen #goedkoop #supermarkt #korting #bonus")
    posts.append({"soort": "aanbiedingen", "tijd": "12:00", "tekst": tekst, "afbeelding": f"{SITE}/data/social/{png}", "link": f"{SITE}/aanbiedingen/"})
# Avondbericht: per supermarkt de grootste klapper (een tweede moment op de dag met andere inhoud).
avond = beste([o for o in nu if o.get("c") in ETEN - {"Huishouden"} and o not in top], 5)
if avond:
    png = f"avond-{VANDAAG}.png"
    kaart("Morgen boodschappen doen?", "Per supermarkt de grootste korting", avond, "goedkopeboodschappen.netlify.app", os.path.join(OUT, png))
    regels = "\n".join(f"✅ {NAMEN[o['s']]}: {o['n']} {eur(o['p'])}" for o in avond)
    tekst = (f"Morgen boodschappen doen? Check eerst waar het goedkoopst is 👇\n\n{regels}\n\n"
             f"Zet je boodschappen op een lijst en zie in één keer bij welke supermarkt je het minst betaalt. Je lijst blijft bewaard, en als je terugkomt zie je meteen wat goedkoper is geworden.\n"
             f"👉 {SITE}\n\n#boodschappenlijst #besparen #supermarkt #aanbiedingen #goedkoop")
    posts.append({"soort": "avond", "tijd": "19:30", "tekst": tekst, "afbeelding": f"{SITE}/data/social/{png}", "link": SITE})
json.dump({"datum": VANDAAG, "posts": posts}, open(os.path.join(OUT, "vandaag.json"), "w"), ensure_ascii=False, indent=1)
print(f"{len(posts)} berichten voor {VANDAAG}")
