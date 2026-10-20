"""Bouwt alle pagina's van Goedkope Boodschappen in één map (standaard public/).

Gebruik: python3 scripts/bouw_paginas.py <uitmap>
Het rekenwerk (data laden, producten zoeken, basispakket) staat in scripts/vergelijk.py.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vergelijk import *
from vergelijk import json, re, html, datetime, itertools, statistics, quote, quote_plus
# ---------- sjabloon ----------
FONT = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Barlow+Condensed:wght@600;700&display=swap">'
FAV = '<link rel="icon" href="/icons/icon.svg" type="image/svg+xml"><link rel="icon" href="/icons/icon-192.png" sizes="192x192" type="image/png"><link rel="apple-touch-icon" href="/icons/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest">'
GC = '<script data-goatcounter="https://goedkopeboodschappen.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>'
NAV = [("/aanbiedingen/", '<span class="ic">🔥 </span>Aanbiedingen', "pill aanb"), ("/maaltijden/", '<span class="ic">🍽️ </span>Maaltijden', "pill mt"), ("/feestdagen/", "🎉 Feestdagen", "feest"), ("/categorie/", "Categorieën", "wide")]
def header(actief=""):
    links = "".join(f'<a href="{h}"{' class="' + c + '"' if c else ""}{" aria-current=page" if h == actief else ""}>{t}</a>' for h, t, c in NAV)
    return f'<header class="top"><div class="wrap bar"><a class="brand" href="/"><img src="/icons/icon.svg" alt="" width="34" height="34"><span>Goedkope Boodschappen</span></a><nav class="nav" aria-label="Menu">{links}</nav><nav class="snel" aria-label="Populair"><a class="sk best" href="/goedkoopste-supermarkt/">🏆 Goedkoopste<span class="lg2"> supermarkt</span></a><a class="sk wm" href="/maaltijden/weekmenu/">📅 Weekmenu<span class="lg2"> met boodschappenlijst</span></a></nav></div></header>'
FOOTER = f'''<footer class="foot"><div class="wrap"><p class="free">Goedkope Boodschappen is gratis en onafhankelijk. Geen reclame, geen betaalde plekken, geen commissie: ik verdien er geen cent aan.</p>
<nav aria-label="Supermarkten"><a href="/supermarkt/ah/">Albert Heijn</a><a href="/supermarkt/jumbo/">Jumbo</a><a href="/supermarkt/lidl/">Lidl</a><a href="/supermarkt/aldi/">Aldi</a><a href="/supermarkt/plus/">PLUS</a><a href="/supermarkt/dirk/">Dirk</a><a href="/supermarkt/hoogvliet/">Hoogvliet</a><a href="/supermarkt/dekamarkt/">DekaMarkt</a><a href="/supermarkt/vomar/">Vomar</a><a href="/supermarkt/spar/">SPAR</a><a href="/supermarkt/poiesz/">Poiesz</a></nav>
<nav aria-label="Over"><a href="/over/">Over deze site</a><a href="/zo-vergelijken-wij/">Zo vergelijken wij</a><a href="/privacy/">Privacy</a><a href="/aanbiedingen/">Aanbiedingen</a><a href="/maaltijden/">Complete maaltijden</a><a href="/besparen/">Besparen op boodschappen</a><a href="/glutenvrij/">Glutenvrij</a><a href="/lactosevrij/">Lactosevrij</a><a href="/vegan/">Vegan</a><a href="/halal/">Halal</a><a href="/koosjer/">Koosjer</a><a href="/eiwitrijk/">Eiwitrijk</a><a href="/sinterklaas/">Sinterklaas</a><a href="/kerst/">Kerst</a><a href="/oud-en-nieuw/">Oud en nieuw</a><a href="/goedkoopste-supermarkt/">Goedkoopste supermarkt</a><a href="/vergelijk/">Alle producten</a><a href="mailto:goedkopeboodschappen@proton.me">Contact: goedkopeboodschappen@proton.me</a></nav>
<p class="small">Gemaakt door Erik. Prijzen van de webshops van de supermarkten, bijgewerkt op {DATUM}. De prijs aan de kassa is leidend.</p><p class="small">Meer gratis van Erik: <a href="https://goedkopertanken.netlify.app/">Tankwijzer (goedkoper tanken)</a> · <a href="https://vluchtwijzer.netlify.app/">Vluchtwijzer</a> · <a href="https://vakantietoppers.netlify.app/">Vakantiewijzer</a></p></div></footer>'''
# Knoppen "+ Op mijn lijst" op losse pagina's: bewaren in de browser en op de startpagina aan de lijst toevoegen.
LISTJS = '''<script>document.addEventListener("click",e=>{const d=e.target.closest("[data-deel]");if(!d||!navigator.share)return;e.preventDefault();try{const o=JSON.parse(d.dataset.deel);navigator.share({title:o.t,text:o.t,url:o.u}).catch(()=>{})}catch(x){}try{window.goatcounter&&goatcounter.count({path:"delen"+location.pathname,title:"Gedeeld",event:true})}catch(x){}})</script><script>(()=>{let m=null;try{m=JSON.parse(localStorage.getItem("mijn-winkel")||"null")}catch(e){}if(!m)return;document.querySelectorAll('.ptable [data-out="'+m+'"]').forEach(a=>{const r=a.closest("tr");if(!r||r.classList.contains("mijn"))return;r.classList.add("mijn");const b=document.createElement("span");b.className="mijnlbl";b.textContent="⭐ Jouw winkel";a.after(b)})})()</script><script>(()=>{const t=document.querySelector(".pagehead nav.terug");if(!t||!("IntersectionObserver" in window))return;const c=t.cloneNode(true);c.classList.add("vast");c.hidden=true;document.body.appendChild(c);new IntersectionObserver(([e])=>{c.hidden=e.isIntersecting||e.boundingClientRect.top>0}).observe(t)})()</script><div class="dock" id="dock" hidden><span id="dockt"></span><a class="btn" href="/#lijst">Mijn lijst</a></div>
<script>(()=>{const K="lijst-erbij",get=()=>{try{return JSON.parse(localStorage.getItem(K)||"[]")}catch(e){return []}},put=v=>{try{localStorage.setItem(K,JSON.stringify(v));return true}catch(e){return false}},
cnt=()=>{try{return (JSON.parse(localStorage.getItem("lijst-v3")||"[]")||[]).length}catch(e){return 0}};
window.mark=()=>{const q=get(),u=new Set(q.map(x=>x.u));document.querySelectorAll(".add[data-o]").forEach(b=>{const o=JSON.parse(b.dataset.o);if(u.has(o.u)){b.textContent="✓ Klaar voor je lijst";b.classList.add("on")}});
const n=q.length,m=cnt(),d=document.getElementById("dock");if(!d)return;d.hidden=false;document.body.classList.add("hasdock");document.getElementById("dockt").innerHTML=n?"<b>"+n+(n===1?" artikel":" artikelen")+"</b> klaar voor je lijst":m?"<b>Mijn lijst</b>: "+m+(m===1?" artikel":" artikelen"):"<b>Mijn lijst</b> is nog leeg"};
const gc=(p,t)=>{try{window.goatcounter&&goatcounter.count&&goatcounter.count({path:p,title:t||p,event:true})}catch(e){}};
document.addEventListener("click",ev=>{const out=ev.target.closest("[data-out]");if(out){gc("naar/"+out.dataset.out,"Doorklik");return}const b=ev.target.closest(".add[data-o]");if(!b)return;const o=JSON.parse(b.dataset.o),q=get();if(!q.some(x=>x.u===o.u)){q.push(o);if(!put(q)){b.textContent="Bewaren lukt niet in deze browser";return}gc("lijst/"+(o.term||o.n).toLowerCase(),"Op lijst")}mark()});mark()})()</script>'''
def page(path, title, desc, head_html, body_html, ld=None, actief="", extra_css="", og_title=None, og_img=None):
    # Google toont ongeveer 60 tekens titel en 155 tekens omschrijving: te lange titels zonder maand/jaar, omschrijvingen netjes inkorten.
    if len(title) > 65: title = re.sub(r"\s*\((januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december) \d{4}\)$", "", title)
    if len(title) > 65: title = re.sub(r"\s*\|\s*Goedkope Boodschappen$", "", title)
    if len(title) > 65: title = title.replace(" (alle merken)", "").replace(": vanaf ", ": ")
    if len(title) > 65: title = re.sub(r", goedkoopst bij [^,:]+$", "", title)
    if len(title) > 65: title = re.sub(r"(: € [\d,]+ per \w+) bij [^:]+$", r"\1", title)
    if len(title) > 65: title = re.sub(r"\s*\([^)]*\)", "", title)
    if len(title) > 65: title = title.replace(": waar is het goedkoopst?", ": prijs per supermarkt").replace(" vergelijken: goedkoopst bij ", ": goedkoopst bij ")
    if len(title) > 68: title = title[:title.rfind(" ", 0, 64)].rstrip(",:;–-") + "…"
    if len(desc) > 160: desc = desc[:desc.rfind(" ", 0, 155)].rstrip(",;:") + "…"
    _t = re.search(r'<nav class="terug".*?</nav>', head_html, re.S)
    if _t: body_html = body_html + _t.group(0).replace('class="terug"', 'class="terug onder"', 1)
    ldtag = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
    return f'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{BASE}{path}"><meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="website"><meta property="og:locale" content="nl_NL"><meta property="og:site_name" content="Goedkope Boodschappen"><meta property="og:url" content="{BASE}{path}"><meta property="og:title" content="{esc(og_title or title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{BASE}{og_img or "/icons/og.png"}"><meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#0e7c4a">
{FAV}{FONT}<link rel="stylesheet" href="/stijl.css?v={quote(VERSIE)}"><script src="/fout.js?v={quote(VERSIE)}" defer></script>{f"<style>{extra_css}</style>" if extra_css else ""}{ldtag}{GC}</head><body>
{header(actief)}<main><div class="wrap pagehead">{head_html}</div><div class="wrap content">{body_html}</div></main>{FOOTER}{LISTJS}</body></html>'''
def schrijf(path, inhoud):
    p = os.path.join(OUT, path.strip("/"), "index.html") if path.endswith("/") else os.path.join(OUT, path.lstrip("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(inhoud)
# Labels: glutenvrij (in de productnaam) en caloriearm (EU-regel: hooguit 40 kcal per 100 g of 20 kcal per 100 ml).
GV_RE = re.compile(r"gluten ?vrij|gluten[- ]?free|zonder gluten|sans gluten|senza glutine", re.I)
def kcal_arm(kt):
    m = re.match(r"^(\d+(?:[.,]\d+)?) kcal per 100 (g|ml)$", kt or "")
    return bool(m) and float(m.group(1).replace(",", ".")) <= (20 if m.group(2) == "ml" else 40)
# Lactosevrij: met lactosevrij in de naam, of van nature zonder melk (plantaardige drinks en zuivelvervangers, vegan).
LV_RE = re.compile(r"lactose ?vrij|zonder lactose|lactose[- ]?free|laktosefrei|\bvegan\b|100% plantaardig|plantaardige? (?:drink|yoghurt|kwark|kaas|room|variatie|alternatief|boter|ijs)|soja ?drink|haver ?drink|havermelk|amandel ?drink|kokos ?drink|rijst ?drink|\balpro\b|\boatly\b|\bviolife\b", re.I)
# Vegan: met vegan of 100% plantaardig in de naam, plantaardige zuivel- en vleesvervangers, tofu/tempeh/seitan en volledig plantaardige merken.
VG_RE = re.compile(r"\bvegan\b|100% plantaardig|plantaardige? (?:drink|yoghurt|kwark|kaas|room|variatie|alternatief|boter|ijs|burger|gehakt|stukjes|balletjes|schnitzel|worst|kipstukjes|reepjes)|soja ?drink|haver ?drink|havermelk|amandel ?drink|kokos ?drink|rijst ?drink|\balpro\b|\boatly\b|\bviolife\b|\b(?:tofu|tempeh|seitan)\b", re.I)
VG_NIET = re.compile(r"gyoza|dumpling|loempia|niet vegan|aftersun|zonnebrand|spray|vitamine|supplement|capsule|tablet|shampoo|zeep|douche|creme voor|tandpasta|deodorant|lippen|nagel|make-up|mascara|\bmet (?:kip|ei|kaas|vlees)\b", re.I)
HALAL_RE = re.compile(r"\bhalal\b", re.I)
def is_vegan(naam): return bool(naam) and bool(VG_RE.search(naam)) and not VG_NIET.search(naam)
VG_SOORTEN = [  # (slug, naam, icoon, woorden in de productnaam); de eerste soort die past telt
    ("melk", "Plantaardige melk en drinks", "🥛", ["drink", "drank", "melk", "barista", "latte", "cappuccino", "shake", "calcium", "meal to go", "the original", "oatly haver", "no sugars", "ongezoet 1"]),
    ("yoghurt", "Plantaardige yoghurt en toetjes", "🥣", ["mild & creamy", "mild&creamy", "m&c", "alpro aardbei", "apple pie", "alpro matcha", "fresh original", "alpro protein", "yoghurt", "kwark", "skyr", "vla", "pudding", "dessert", "toetje", "mousse", "variatie", "griekse stijl"]),
    ("kaas", "Vegan kaas", "🧀", ["creamy original", "creamy orginal", "creamy strawberry", "greek white", "vioblock", "kaas", "cheese", "plakken", "geraspt", "mozzarella", "feta", "cheddar", "parmesan", "gouda", "smeerkaas", "roomkaas"]),
    ("vlees", "Vegan vleesvervangers en tofu", "🌱", ["burger", "gehakt", "worst", "schnitzel", "stukjes", "balletjes", "bal", "filet", "nugget", "kip", "shoarma", "kebab", "gyros", "bacon", "spek", "reepjes", "tofu", "tempeh", "seitan", "frikandel", "kroket", "bitterbal", "vegetarisch", "vlees", "slager", "hamburger", "braadworst", "rookworst", "tonijn", "vis", "rauwe ham", "paté", "pate", "kornet", "broodbeleg", "nuggets"]),
    ("boter", "Plantaardige boter, room en sauzen", "🧈", ["smeren", "smeerbaar", "halvarine", "minarine", "cooking", "olie", "aioli", "dip", "paturain", "cuisine", "kookroom", "bakken en braden", "boter", "room", "slagroom", "creme", "crème", "margarine", "mayo", "saus", "dressing", "pesto", "hummus", "spread"]),
    ("zoet", "Vegan koek, chocolade en ijs", "🍫", ["gums", "streken", "veters", "regenboog", "marshmallow", "winegum", "koek", "chocolade", "choco", "reep", "ijs", "cake", "wafel", "biscuit", "snoep", "drop", "cookie", "brownie", "hagelslag", "pasta", "taart"]),
    ("maaltijd", "Vegan maaltijden, soepen en snacks", "🍲", ["risotto", "tikka", "ravioli", "tortelloni", "gnocchi", "moussaka", "empanada", "falafel", "rendang", "roti", "saucijzen", "tenders", "kroepoek", "tortilla", "crackers", "baguet", "omelet", "vermicelli", "pizza", "maaltijd", "soep", "salade", "wrap", "curry", "noodle", "noedel", "snack", "chips", "lasagne", "quiche", "bowl"]),
]
def _vg_soort(naam):
    n = naam.lower()
    if re.search(r"cheesecake|\bijs\b|ijsje|ijsbeker|sorbet|magnum|cornetto|fruittella|mentos|lolli|pepermunt|wilhelmina|zwartwit|hondenkoppen|leeuwenkoppen|macaroon|tiramisu|treets|look-o-look|snoep|\bdrop|\bchoc\b|bites|repen|\bbar\b|\bdark\b|kitkat|ritter|nutella|praline|\bstol\b", n): return "zoet"
    if "gurt" in n: return "yoghurt"
    for sl, _, _, ws in VG_SOORTEN:
        if any(w in n for w in ws): return sl
    return "overig"
VG_PER = {}
for p in prods:
    if stores[p[0]].get("count") and is_vegan(p[1]): VG_PER.setdefault(_vg_soort(p[1]), []).append(p)
VG_LIJST = [(sl, nm_, ic) for sl, nm_, ic, _ in VG_SOORTEN + [("overig", "Overige vegan producten", "🛒", [])] if len({p[0] for p in VG_PER.get(sl, [])}) >= 2 and len(VG_PER.get(sl, [])) >= 5]
from eiwit import EIWIT
def eiwitrijk(term, kt=""):
    """EU-regel 'rijk aan eiwitten': minstens 20% van de energie uit eiwit (en hier ook minstens 5 g per 100 g)."""
    g = EIWIT.get((term or "").lower())
    if not g or g < 5: return False
    m = re.match(r"^(\d+(?:[.,]\d+)?) kcal per 100", kt or "")
    return g * 4 / float(m.group(1).replace(",", ".")) >= .2 if m and float(m.group(1).replace(",", ".")) > 0 else g >= 10
def labels(naam, kt="", term=""):
    return (('<span class="lbl gv">🌾 Glutenvrij</span>' if GV_RE.search(naam or "") else "")
            + ('<span class="lbl lv">🥛 Lactosevrij</span>' if LV_RE.search(naam or "") else "")
            + ('<span class="lbl vg">🌱 Vegan</span>' if is_vegan(naam) else "")
            + ('<span class="lbl hl">Halal</span>' if HALAL_RE.search(naam or "") else "")
            + ('<span class="lbl arm">🥗 Caloriearm</span>' if kcal_arm(kt) else "")
            + ('<span class="lbl eiw">💪 Eiwitrijk</span>' if eiwitrijk(term, kt) else ""))

def crumbs(*items):
    # Duidelijk terug kunnen: een knop naar de bovenliggende pagina en naar Home, met daaronder het kruimelpad.
    ouder = [(t, h) for t, h in items if h]
    # Geen bovenliggende pagina (bijv. Aanbiedingen of Feestdagen): dan terug naar alle categorieën.
    if not ouder and not (items and items[-1][0] in ("Categorieën", "Alle categorieën")): ouder = [("Alle categorieën", "/categorie/")]
    terug = (f'<a class="tknop" href="{ouder[-1][1]}">← {esc(ouder[-1][0])}</a>' if ouder else "")
    html_ = (f'<nav class="terug" aria-label="Terug">{terug}<a class="tknop home" href="/">🏠 Home</a></nav>'
             + '<p class="crumbs"><a href="/">Home</a>' + "".join(f' › <a href="{h}">{esc(t)}</a>' if h else f" › {esc(t)}" for t, h in items) + "</p>")
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"}] +
          [{"@type": "ListItem", "position": i + 2, "name": t, **({"item": BASE + h} if h else {})} for i, (t, h) in enumerate(items)]}
    return html_, ld
def faq_ld(faq): return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
def faq_html(faq): return '<section class="faq"><h2>Veelgestelde vragen</h2>' + "".join(f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in faq) + "</section>"
def addbtn(p, term):
    o = {"s": stores[p[0]]["id"], "n": p[1], "sz": p[4] or "", "p": round(eff(p), 2), "u": plink(p), "r": 1, "term": term}
    return f'<button type="button" class="add" data-o="{esc(json.dumps(o, ensure_ascii=False))}">+ Op mijn lijst</button>'
def offerbtn(o):
    d_ = {k: o.get(k) for k in ("s", "n", "sz", "p", "u", "t")}
    return f'<button type="button" class="add" data-o="{esc(json.dumps(d_, ensure_ascii=False))}">+ Op mijn lijst</button>'
def offer_card(o):
    lbl = f'<span class="pill">{esc(o["lbl"])}</span>' if o.get("lbl") else ""
    soon = f'<span class="soon">vanaf {kortdag(o["v"])}</span>' if o.get("v") and o["v"] > VANDAAG else ""
    was = f'<span class="was">{eur(o["was"])}</span>' if o.get("was") else ""
    pp = f'<span class="unit">{esc(per(o.get("pp"), o.get("eh")))}</span>' if o.get("pp") else ""
    t = f'<span class="till">t/m {kortdag(o["t"])}</span>' if o.get("t") else ""
    return (f'<li class="offer" data-c="{esc(o.get("c") or "Overig")}"><span class="top2"><span class="shop">{esc(KORT.get(o["s"], NAMEN[o["s"]]))}</span>{lbl}{soon}</span>'
            f'<span><a class="on" href="{esc(o["u"])}" rel="nofollow noopener" target="_blank" data-out="{o["s"]}">{esc(o["n"])}</a> <span class="sz">{esc(o.get("sz") or "")}</span>{labels(o["n"], o.get("kc"), o.get("tm", ""))}</span>'
            + (f'<span class="kc">{esc(o["kc"])}</span>' if o.get("kc") else "") +
            f'<span class="prow">{tag(o["p"], "deal")}{was}{pp}</span>'
            + (f'<span class="oordeel {o["ds"]}">{"🔥" if o["ds"] == "top" else "👍" if o["ds"] == "ok" else "ℹ️" if o["ds"] == "let" else "⚠️"} {esc(o["dt"])}</span>' if o.get("ds") else "")
            + f'{t}{offerbtn(o)}</li>')
def fout_knop(t, si, p):
    """Knopje "Klopt niet?" (afgehandeld in /fout.js)."""
    d = {"term": t, "winkel": NAMEN.get(stores[si]["id"], stores[si]["name"]), "naam": p[1] + (" " + p[4] if p[4] else ""), "link": plink(p), "prijs": eur(eff(p))}
    return f'<button type="button" class="fout" data-fout="{esc(json.dumps(d, ensure_ascii=False))}">Klopt niet?</button>'


# ---------- prijsgeschiedenis ----------
try: HIST = json.load(open(os.path.join(ROOT, "data", "historie.json")))
except Exception: HIST = {"dagen": [], "termen": {}, "eenheid": {}}
# Klein bestand voor de app: per product en winkel de laagste gewone prijs per eenheid van de bewaarde dagen (zonder vandaag).
if len(HIST["dagen"]) >= 30:
    laagste = {"sinds": HIST["dagen"][0], "eh": HIST["eenheid"], "t": {}}
    for t_, perw in HIST["termen"].items():
        m = {w: min(v for v in r[:-1] if v is not None) for w, r in perw.items() if any(v is not None for v in r[:-1])}
        if m: laagste["t"][t_] = {w: round(v, 3) for w, v in m.items()}
        # "Normale" prijs: het midden (mediaan) van de laatste 30 metingen, als er minstens 10 zijn.
        nm = {}
        for w, r in perw.items():
            v = sorted(x for x in r[:-1][-30:] if x is not None)
            if len(v) >= 10: nm[w] = round(v[len(v) // 2], 3)
        if nm: laagste.setdefault("n", {})[t_] = nm
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    json.dump(laagste, open(os.path.join(OUT, "data", "laagste.json"), "w"), ensure_ascii=False, separators=(",", ":"))
def kortdatum(d):
    d = datetime.date.fromisoformat(d); return f"{d.day} {MND[d.month - 1]}"
def prijsverloop(t, nu_laagst):
    """Grafiek (inline SVG) van de laagste en de middelste prijs per eenheid over de bewaarde dagen, met een kort oordeel."""
    reeks = HIST["termen"].get(t); dagen = HIST["dagen"]
    if not reeks or len(dagen) < 5: return ""
    laag, mid = [], []
    for i in range(len(dagen)):
        v = sorted(x[i] for x in reeks.values() if x[i] is not None)
        laag.append(v[0] if v else None); mid.append(v[len(v) // 2] if v else None)
    pts = [(i, a, b) for i, (a, b) in enumerate(zip(laag, mid)) if a is not None]
    if len(pts) < 5: return ""
    eh = eenheid(HIST["eenheid"].get(t, ""))
    lo, hi = min(p[1] for p in pts), max(max(p[1], p[2]) for p in pts)
    if hi - lo < .01: hi = lo + .01
    W, H, L, R, T, B = 640, 260, 110, 14, 20, 46
    x = lambda i: L + (W - L - R) * i / max(1, len(dagen) - 1)
    y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))
    lijn = lambda k: " ".join(f"{'M' if j == 0 else 'L'}{x(p[0]):.1f},{y(p[k]):.1f}" for j, p in enumerate(pts))
    gem = sum(p[1] for p in pts) / len(pts)
    nu = nu_laagst if nu_laagst is not None else pts[-1][1]
    laagste_max = max(p[1] for p in pts)
    if laagste_max - lo < .005:
        tekst = f"De laagste prijs per {eh} is sinds {kortdatum(dagen[0])} niet veranderd: {eur(lo)}."
        oordeel = None
    elif nu <= lo * 1.01: oordeel = f"Dit is de laagste prijs sinds {kortdatum(dagen[0])}."
    elif nu < gem * .97: oordeel = "Dat is lager dan gemiddeld: een goed moment om te kopen."
    elif nu > gem * 1.03: oordeel = "Dat is hoger dan gemiddeld."
    else: oordeel = "Dat is ongeveer de gemiddelde prijs."
    if oordeel is not None:
        tekst = (f"De laagste prijs per {eh} was sinds {kortdatum(dagen[0])} tussen {eur(lo)} en {eur(laagste_max)}, gemiddeld {eur(gem)}. "
                 f"Nu is de laagste prijs {eur(nu)}. {oordeel}")
    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(tekst)}" style="width:100%;height:auto;display:block">'
           f'<line x1="{L}" x2="{W - R}" y1="{y(lo):.1f}" y2="{y(lo):.1f}" stroke="var(--line)"/><line x1="{L}" x2="{W - R}" y1="{y(hi):.1f}" y2="{y(hi):.1f}" stroke="var(--line)"/>'
           f'<text x="{L - 10}" y="{y(hi) + 8:.1f}" text-anchor="end" font-size="22" fill="var(--muted)">{eur(hi)}</text><text x="{L - 10}" y="{y(lo) + 8:.1f}" text-anchor="end" font-size="22" fill="var(--muted)">{eur(lo)}</text>'
           f'<text x="{L}" y="{H - 8}" font-size="22" fill="var(--muted)">{kortdatum(dagen[0])}</text><text x="{W - R}" y="{H - 8}" text-anchor="end" font-size="22" fill="var(--muted)">{kortdatum(dagen[-1])}</text>'
           f'<path d="{lijn(2)}" fill="none" stroke="var(--muted)" stroke-width="3" stroke-dasharray="8 7"/>'
           f'<path d="{lijn(1)}" fill="none" stroke="var(--green)" stroke-width="5" stroke-linejoin="round"/></svg>')
    # Per winkel: nu, normaal (midden van de laatste 30 metingen) en de laagste prijs sinds de eerste meting.
    pw = []
    for w_, r_ in reeks.items():
        oud = [v for v in r_[:-1] if v is not None]
        if len(oud) < 10 or r_[-1] is None: continue
        norm_ = sorted(oud[-30:])[len(oud[-30:]) // 2]; laag_ = min(oud); nu_ = r_[-1]
        if nu_ < laag_ * .99: o_ = '<span class="low">Laagste prijs ooit</span>'
        elif nu_ <= norm_ * .95: o_ = f'<span class="low">{round((1 - nu_ / norm_) * 100)}% onder normaal</span>'
        elif nu_ >= norm_ * 1.08: o_ = '<span class="hoger">Duurder dan normaal</span>'
        else: o_ = '<span class="sub">Normale prijs</span>'
        pw.append((nu_, w_, norm_, laag_, o_))
    pw.sort()
    tabel = ""
    if len(pw) >= 2:
        tabel = (f'<h3>Is het nu een goede prijs? Per supermarkt</h3><div class="tblwrap"><table class="ptable hist"><thead><tr><th>Supermarkt</th><th style="text-align:right">Nu</th><th style="text-align:right">Normaal</th><th style="text-align:right">Laagste sinds {kortdatum(dagen[0])}</th></tr></thead><tbody>'
                 + "".join(f'<tr><td><b data-out="{esc(w_)}">{esc(NAMEN.get(w_, w_))}</b><br>{o_}</td><td class="p">{eur(nu_)}</td><td class="p">{eur(n_)}</td><td class="p">{eur(l_)}</td></tr>' for nu_, w_, n_, l_, o_ in pw)
                 + f'</tbody></table></div><p class="note">Prijzen per {esc(eh)}. Normaal is het midden van de laatste 30 metingen bij die winkel. Zo zie je of een aanbieding echt voordelig is.</p>')
    return (f'<h2>Prijsverloop van {esc(t)}</h2><div class="panel">{svg}<p class="note" style="margin:8px 0 0"><span style="color:var(--green);font-weight:700">━</span> laagste prijs per {esc(eh)} &nbsp; '
            f'<span style="color:var(--muted);font-weight:700">┅</span> middelste prijs van alle supermarkten</p></div><p>{esc(tekst)}</p>' + tabel)

made = []  # (pad, prioriteit)
from maaltijd_kosten import MAAL, I as MAAL_ING
# Per product de complete maaltijden waarin het zit (voor links vanaf de productpagina's).
MAAL_PER_TERM = {}
for _m in MAAL:
    for _r in _m["ing"]:
        if len(_r) > 3 and _r[3] == "v": continue
        for _t in {_r[0], *MAAL_ING.get(_r[0], ([],))[0]}:
            if _t in PICKED and _m not in MAAL_PER_TERM.get(_t, []): MAAL_PER_TERM.setdefault(_t, []).append(_m)
for _t in PICKED:
    if _t in VARIANT and _t not in MAAL_PER_TERM:
        for _z in VARIANT[_t]["zoek"]:
            for _m in MAAL_PER_TERM.get(_z, []) or [m for m in MAAL if any(r[0] == _z for r in m["ing"])]:
                if _m not in MAAL_PER_TERM.get(_t, []): MAAL_PER_TERM.setdefault(_t, []).append(_m)

# ---------- productpagina's ----------
for t, rows in PICKED.items():
    name = cap(t); sl = slug(t); path = f"/vergelijk/{sl}/"
    goed = [r for r in rows if id(r[1]) not in BAD] or rows
    (si0, p0), (siN, pN) = goed[0], goed[-1]
    win, loser = NAMEN.get(stores[si0]["id"], stores[si0]["name"]), NAMEN.get(stores[siN]["id"], stores[siN]["name"])
    (u0, e0), (uN, eN) = toon_unit(p0), toon_unit(pN)
    eh = eenheid(e0)
    vanaf = f"{eur(u0)} per {eh}" if u0 is not None and eh else eur(eff(p0))
    besp = round((1 - u0 / uN) * 100) if u0 and uN and uN > u0 else 0
    title = f"{name}: vanaf {vanaf} bij {win} ({MAAND})"
    desc = (f"{name} kost {vanaf} bij {win}" + (f" en {per(uN, eN)} bij {loser}" if uN and u0 and uN > u0 * 1.02 else "") +
            (f". Vergelijk {len(rows)} supermarkten" if len(rows) > 1 else f". Nu alleen te koop bij {win}") + (", inclusief de aanbiedingen van deze week" if any(offer_of(p) for _, p in rows) else "") + ". Elke dag bijgewerkt." + (f" Ongeveer {kcal_txt(t)}." if kcal_txt(t) else ""))
    c = CATOF.get(t)
    ch, cld = crumbs(*([(c[3], f"/categorie/{slug(c[3])}/"), (c[0], f"/categorie/{slug(c[0])}/")] if c else [("Alle producten", "/vergelijk/")]), (name, None))
    trs = ""
    for i, (si, p) in enumerate(rows):
        o = offer_of(p)
        unit = "" if id(p) in BAD else (per(*toon_unit(p)) or "inhoud onbekend")
        trs += (f'<tr{" class=win" if i == 0 else ""}><td><span class="shop">{esc(NAMEN.get(stores[si]["id"], stores[si]["name"]))}</span>{" <b class=sub style=display:inline;color:var(--green-dark)>Goedkoopst</b>" if i == 0 else ""}{" <span class=pill>" + esc(o["lbl"] or "aanbieding") + "</span>" if o else ""}<br>'
                f'<a href="{esc(plink(p))}" rel="nofollow noopener" target="_blank" data-out="{stores[si]["id"]}"><b>{esc(p[1])}</b></a><span class="sub">{esc(p[4] or "")}</span>{labels(p[1], kcal_txt(t), t)}{fout_knop(t, si, p)}{addbtn(p, t)}</td>'
                f'<td class="p">{tag(eff(p), "deal" if o else "")}{"<br><span class=was>" + eur(p[3]) + "</span>" if o else ""}<br><span class="unit">{esc(unit)}</span></td></tr>')
    acties = term_offers(t)
    actie_html = (f'<h2>{esc(name)} in de aanbieding</h2><ul class="offers">' + "".join(offer_card(o) for o in acties) + "</ul>") if acties else ""
    faq = [(f"Waar is {t} het goedkoopst?", f"{name} is nu het goedkoopst bij {win}: {p0[1]} kost {eur(eff(p0))}" + (f", dat is {per(u0, e0)}" if u0 else "") + "."),
           (f"Wat kost {t} bij de supermarkt?", f"Bij {len(rows)} supermarkten kost het voordeligste product tussen {eur(min(eff(p) for _, p in rows))} en {eur(max(eff(p) for _, p in rows))}, afhankelijk van merk en verpakking." if len(rows) > 1 else f"{name} is op dit moment alleen bij {win} te koop, voor {eur(eff(p0))}.")]
    kt = kcal_txt(t); kp = kcal_pak(t, p0)
    if kt: faq.append((f"Hoeveel calorieën zitten er in {t}?", f"{name} bevat gemiddeld ongeveer {kt}" + (f". Het goedkoopste product, {p0[1]} ({p0[4] or 'per stuk'}), is in totaal ongeveer {format(kp, ',').replace(',', '.')} kcal" if kp else "") + ". Dat is een richtwaarde; de precieze waarde staat op de verpakking."))
    if besp >= 5: faq.append((f"Hoeveel bespaar je op {t}?", f"Per {eh} is {win} {besp}% goedkoper dan {loser} ({per(u0, e0)} tegen {per(uN, eN)})."))
    rel = [x for x in (c[2] if c else []) if x != t and x in PICKED][:24]
    mm = MAAL_PER_TERM.get(t, [])[:6]
    maalhtml = (f'<h2>Complete maaltijden met {esc(t)}</h2><ul class="links">' + "".join(f'<li><a href="/maaltijden/{x["slug"]}/">{esc(x["naam"])}</a></li>' for x in mm) + '</ul>') if mm else ""
    relhtml = (f"<h2>Meer uit {esc(c[0].lower())}</h2><ul class=\"links\">" + "".join(f'<li><a href="/vergelijk/{slug(x)}/">{esc(cap(x))}</a></li>' for x in rel) + "</ul>") if rel else ""
    head = ch + f"<h1>{esc(name)}: waar is het goedkoopst?</h1><p class=\"lead\">{esc(name)} koop je nu het voordeligst bij <b>{esc(win)}</b>" + (f": {esc(vanaf)}" if vanaf else "") + (f", {besp}% goedkoper dan bij {esc(loser)}." if besp >= 5 else ".") + "</p>"
    body = (f'<div class="tblwrap"><table class="ptable"><thead><tr><th>Supermarkt en product</th><th style="text-align:right">Prijs</th></tr></thead><tbody>{trs}</tbody></table></div>'
            f'<p class="note">Prijzen van {DATUM}, gesorteerd op prijs per {esc(eh or "stuk")}. Per supermarkt het voordeligste vergelijkbare product. De prijs aan de kassa is leidend.</p>'
            + (f'<p class="kcal">🔥 Calorieën: ongeveer <b>{esc(kt)}</b> (gemiddelde richtwaarde, per merk iets anders).</p>' if kt else "") +
            f'<a class="cta" href="/?q={quote(t)}">Zet {esc(t)} op je boodschappenlijst</a>{actie_html}{prijsverloop(t, min((eff_unit(p) for _, p in goed if eff_unit(p) is not None and id(p) not in BAD), default=None))}{faq_html(faq)}{maalhtml}{relhtml}')
    ld = [cld, faq_ld(faq), {"@context": "https://schema.org", "@type": "ItemList", "name": f"{name} prijzen per supermarkt", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "item": {"@type": "Product", "name": p[1], "offers": {"@type": "Offer", "price": f"{eff(p):.2f}", "priceCurrency": "EUR", "url": plink(p), "availability": "https://schema.org/InStock",
         "seller": {"@type": "Organization", "name": NAMEN.get(stores[si]["id"], stores[si]["name"])}}}} for i, (si, p) in enumerate(rows)]}]
    schrijf(path, page(path, title, desc, head, body, ld, og_title=f"{name}: waar is het goedkoopst?"))
    made.append((path, "0.7"))
print(len(PICKED), "productpagina's")

# ---------- categorieën: hoofdgroepen met subcategorieën ----------
def winkels_txt(t):
    """Bij welke winkels het product te koop is, van goedkoop naar duur."""
    w = [NAMEN.get(stores[si]["id"], stores[si]["name"]) for si, _ in PICKED[t]]
    return f'<span class="wk">🏪 {"Alleen bij " if len(w) == 1 else f"Bij {len(w)} winkels: "}{esc(", ".join(w))}</span>'
def cat_rij(t):
    si, p = PICKED[t][0]
    kt = kcal_txt(t)
    return (f'<tr><td><a href="/vergelijk/{slug(t)}/"><b>{esc(cap(t))}</b></a><span class="sub">{esc(p[1])}</span>' + (f'<span class="kc">{esc(kt)}</span>' if kt else "") + labels(p[1], kt, t) + winkels_txt(t) + fout_knop(t, si, p) + f'{addbtn(p, t)}</td>'
            + f'<td class="wcol"><b>{esc(NAMEN.get(stores[si]["id"]))}</b></td><td class="p"><span class="wnm">{esc(NAMEN.get(stores[si]["id"]))}</span>{tag(eff(p))}<br><span class="unit">{esc(per(*toon_unit(p)) or "inhoud onbekend")}</span></td></tr>')
# Drank per verpakking onder een eigen kopje (zelfde indeling als pakGroep/perPak in site/index.html).
PAKGROEP = ["Losse flessen", "Flessen per pack", "Kratten", "Losse blikjes", "Blikjes per pack", "Trays", "Andere soorten"]
PAKSTART = re.compile(r"\b(fles|flesje|flesjes|flessen|beugelflessen|kinderflesjes|los|sixpack|blikjes|blikken|krat|mini|\d+ x)\b")
def pak_groep(t):
    s = t.lower()
    if re.search(r"\bkrat\b", s): return 2
    if re.search(r"\btray\b", s): return 5
    if re.search(r"\blos blik(je)?\b", s): return 3
    if re.search(r"\b(blikjes|blikken)\b", s): return 4
    if re.search(r"\b(flesjes|flessen|beugelflessen|kinderflesjes)\b", s) or re.search(r"\d+ x \d", s): return 1
    if re.search(r"\b(fles|flesje)\b", s): return 0
    return -1
def per_pak(items):
    g = {t: pak_groep(t) for t in items}
    if len({x for x in g.values() if x >= 0}) < 2: return [("", items)]
    def rest(t):
        s = t.lower(); m = PAKSTART.search(s); return s[m.start():] if m else s
    plek = {}
    for t in items: plek.setdefault(rest(t), len(plek))
    uit = {}
    for t in items: uit.setdefault(6 if g[t] < 0 else g[t], []).append(t)
    return [(PAKGROEP[k], sorted(uit[k], key=lambda t: (plek[rest(t)], items.index(t)))) for k in sorted(uit)]
def cat_tabel(items):
    kop = '<div class="tblwrap"><table class="ptable"><thead><tr><th>Product</th><th class="wcol">Goedkoopst bij</th><th style="text-align:right">Prijs</th></tr></thead><tbody>'
    return "".join((f'<h3 class="pakkop">{esc(k)}</h3>' if k else "") + kop + "".join(cat_rij(t) for t in ts) + '</tbody></table></div>' for k, ts in per_pak(items))
def winnaar(items):
    winst = {}
    for t in items: winst[PICKED[t][0][0]] = winst.get(PICKED[t][0][0], 0) + 1
    top = max(winst, key=winst.get); return top, winst[top]
def maal_links(items, kop):
    cm = []
    for t_ in items:
        for m_ in MAAL_PER_TERM.get(t_, []):
            if m_ not in cm: cm.append(m_)
    return (f'<h2>{esc(kop)}</h2><ul class="links">' + "".join(f'<li><a href="/maaltijden/{m_["slug"]}/">{esc(m_["naam"])}</a></li>' for m_ in cm[:9]) + '</ul>') if cm else ""
GROEP_ITEMS = {}
catpaths = []
for g, gic in GROEPEN:
    subs = [(c, [t for t in c[2] if t in PICKED]) for c in SUBS[g]]
    subs = [(c, it) for c, it in subs if it]
    if not subs: continue
    alle = [t for _, it in subs for t in it]; GROEP_ITEMS[g] = (subs, alle)
    gpath = f"/categorie/{slug(g)}/"
    for c, items in subs:
        if slug(c[0]) == slug(g): continue
        path = f"/categorie/{slug(c[0])}/"
        top, n = winnaar(items)
        ch, cld = crumbs(("Categorieën", "/categorie/"), (g, gpath), (c[0], None))
        title = f"{c[0]}: goedkoopste supermarkt per product ({MAAND})"
        desc = (f"Waar koop je {c[0].lower()} het goedkoopst? {len(items)} producten vergeleken bij {AANTAL} supermarkten: " + ", ".join(items[:4]) +
                f". {NAMEN[stores[top]['id']]} is het vaakst de goedkoopste. Elke dag bijgewerkt.")
        head = ch + f"<h1>{c[1]} {esc(c[0])} vergelijken</h1><p class=\"lead\">Per product de goedkoopste supermarkt. {esc(NAMEN[stores[top]['id']])} is bij {n} van de {len(items)} producten het voordeligst.</p>"
        broers = [x for x, _ in subs if x is not c]
        _ct = cat_tabel(items)
        body = (('<h2>Prijzen per verpakking</h2>' if _ct.startswith('<h3') else '') + _ct + (f'<h2>Meer in {esc(g.lower())}</h2><ul class="chips">' + "".join(f'<li><a href="/categorie/{slug(x[0])}/">{x[1]} {esc(x[0])}</a></li>' for x in broers) + "</ul>" if broers else "")
                + maal_links(items, f"Complete maaltijden met {c[0].lower()}") + f'<p><a href="{gpath}">Alles in {esc(g.lower())}</a> · <a href="/categorie/">Alle categorieën</a></p>'
                + '<a class="cta" href="/aanbiedingen/">Bekijk de aanbiedingen van deze week</a>')
        ld = [cld, {"@context": "https://schema.org", "@type": "ItemList", "name": c[0], "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE}/vergelijk/{slug(t)}/", "name": cap(t)} for i, t in enumerate(items)]}]
        schrijf(path, page(path, title, desc, head, body, ld, actief="/categorie/"))
        catpaths.append((c, path, items)); made.append((path, "0.7"))
    # hoofdgroep: alle subcategorieën onder elkaar
    top, n = winnaar(alle)
    ch, cld = crumbs(("Categorieën", "/categorie/"), (g, None))
    title = f"{g}: goedkoopste supermarkt per product ({MAAND})"
    desc = (f"{g} vergelijken: " + ", ".join(c[0].lower() for c, _ in subs[:5]) + f". {len(alle)} producten bij {AANTAL} supermarkten, "
            f"{NAMEN[stores[top]['id']]} is het vaakst de goedkoopste. Elke dag bijgewerkt.")
    head = (ch + f"<h1>{gic} {esc(g)} vergelijken</h1><p class=\"lead\">{len(alle)} producten in {len(subs)} groepen. {esc(NAMEN[stores[top]['id']])} is bij {n} producten het voordeligst.</p>"
            + ('<ul class="chips">' + "".join(f'<li><a href="#{slug(c[0])}">{c[1]} {esc(c[0])}</a></li>' for c, _ in subs) + "</ul>" if len(subs) > 1 else ""))
    body = "".join((f'<h2 id="{slug(c[0])}">{c[1]} <a href="/categorie/{slug(c[0])}/">{esc(c[0])}</a></h2>' if len(subs) > 1 else "") + cat_tabel(items) for c, items in subs)
    body += (maal_links(alle, f"Complete maaltijden met {g.lower()}") + '<h2>Andere categorieën</h2><ul class="links">' +
             "".join(f'<li><a href="/categorie/{slug(x)}/">{xi} {esc(x)}</a></li>' for x, xi in GROEPEN if x != g) + '</ul><a class="cta" href="/aanbiedingen/">Bekijk de aanbiedingen van deze week</a>')
    ld = [cld, {"@context": "https://schema.org", "@type": "ItemList", "name": g, "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE}/vergelijk/{slug(t)}/", "name": cap(t)} for i, t in enumerate(alle)]}]
    schrijf(gpath, page(gpath, title, desc, head, body, ld, actief="/categorie/"))
    made.append((gpath, "0.8"))
head = crumbs(("Categorieën", None))[0] + "<h1>Boodschappen vergelijken per categorie</h1><p class=\"lead\">Kies een categorie en zie per product welke supermarkt het goedkoopst is.</p>"
body = "".join(f'<h2><a href="/categorie/{slug(g)}/">{gi} {esc(g)}</a></h2><ul class="chips">' + "".join(f'<li><a href="/categorie/{slug(c[0])}/">{c[1]} {esc(c[0])}</a></li>' for c, _ in GROEP_ITEMS[g][0] if slug(c[0]) != slug(g)) + "</ul>"
               for g, gi in GROEPEN if g in GROEP_ITEMS)
body += ('<h2><a href="/vegan/">🌱 Vegan</a></h2><ul class="chips">' + "".join(f'<li><a href="/vegan/{sl}/">{ic} {esc(nm_)}</a></li>' for sl, nm_, ic in VG_LIJST)
         + '<li><a href="/maaltijden/vegan/">🍽️ Vegan maaltijden</a></li></ul>'
         + '<h2>Dieet en leefstijl</h2><ul class="chips"><li><a href="/glutenvrij/">🌾 Glutenvrij</a></li><li><a href="/lactosevrij/">🥛 Lactosevrij</a></li><li><a href="/eiwitrijk/">💪 Eiwitrijk</a></li><li><a href="/vegan/">🌱 Vegan</a></li><li><a href="/halal/">Halal</a></li><li><a href="/koosjer/">Koosjer</a></li><li><a href="/maaltijden/caloriearm/">🥗 Caloriearm</a></li></ul>')
schrijf("/categorie/", page("/categorie/", f"Alle categorieën: boodschappen vergelijken ({MAAND})", f"Vergelijk {len(PICKED)} boodschappen in {len(catpaths)} categorieën bij {AANTAL} supermarkten: groente, diepvries, zuivel, vlees, frisdrank, bier, huishouden en meer.", head, body, actief="/categorie/"))
made.append(("/categorie/", "0.6"))
lis = "".join(f'<li><a href="/vergelijk/{slug(t)}/">{esc(cap(t))}</a></li>' for t in sorted(PICKED))
schrijf("/vergelijk/", page("/vergelijk/", f"Alle {len(PICKED)} producten vergelijken bij {AANTAL} supermarkten", f"Van halfvolle melk tot wasmiddel: zie voor {len(PICKED)} producten bij welke supermarkt ze het goedkoopst zijn. Elke dag bijgewerkt.",
    crumbs(("Alle producten", None))[0] + f"<h1>Alle producten vergelijken</h1><p class=\"lead\">Kies een product en zie bij welke supermarkt het nu het goedkoopst is.</p>", f'<ul class="links">{lis}</ul><a class="cta" href="/">Maak je boodschappenlijst</a>'))
made.append(("/vergelijk/", "0.6"))

# ---------- aanbiedingen ----------
# Elke aanbieding krijgt de subcategorie (sc) van de producten, zodat ze dezelfde indeling hebben. De app leest data/aanbiedingen.json.
def _deel_in(o):
    naam = o["n"] + " " + (o.get("sz") or "")
    c = subcat_van(naam, o.get("c") or "Overig")  # zonder groep ("Overig") wordt in alle groepen gezocht
    if not c and eerste_woord(o["n"]) in MERKKAART:  # geen soort gevonden: dan de soort die bij het merk hoort
        k = MERKKAART[eerste_woord(o["n"])]; c = (k, 0, None)
    if c:
        o["sc"], o["c"] = c[0][0], c[0][3]
        k = kcal_txt(c[2]) if c[2] else None
        if k: o["kc"] = k  # calorieën van de productsoort
        if c[2]: o["tm"] = c[2]; _oordeel(o, c[2])
    return bool(c)
_TERMPROD = {}
def _historie_check(o, term):
    """Is het een echte aanbieding? Vergeleken met de prijzen van dezelfde soort bij dezelfde winkel van de afgelopen weken."""
    if not o.get("pp") or o.get("ds") == "duur" or HIST.get("eenheid", {}).get(term) != o.get("eh"): return
    r = HIST.get("termen", {}).get(term, {}).get(o.get("s")) or []
    oud = [v for v in r[:-1] if v is not None]
    if len(oud) < 10: return
    eh = {"kg": "kilo", "l": "liter", "st": "stuk"}.get(o["eh"], o["eh"])
    wn = NAMEN.get(o["s"], o["s"])
    normaal = sorted(oud[-30:])[len(oud[-30:]) // 2]
    if not (normaal * .3 < o["pp"] < normaal * 3): return  # andere maat of soort: niets zeggen
    zes = [v for v in oud[-42:]]
    if o["pp"] < min(oud) * .99 and o.get("ds") != "top":
        o["ds"], o["dt"] = "top", f"Echte korting: goedkoper dan de gewone prijs van alle {term} bij {wn} sinds {kortdatum(HIST['dagen'][0])}"
    elif o["pp"] >= normaal and o.get("ds") != "top":
        o["ds"], o["dt"] = "let", f"Let op: bij {wn} is {term} zonder actie al te koop vanaf {eur(normaal)} per {eh}"
    elif zes and o["pp"] > min(zes) * 1.05 and o.get("ds") is None:
        o["ds"], o["dt"] = "let", f"De afgelopen weken was {term} bij {wn} al eens {eur(min(zes))} per {eh}"
def _oordeel(o, term):
    """Eerlijk oordeel per actie: vergeleken met de gewone prijs per kilo/liter/stuk van dezelfde soort bij alle supermarkten."""
    _oordeel0(o, term); _historie_check(o, term)
def _oordeel0(o, term):
    if not o.get("pp") or not o.get("eh") or term not in PICKED: return
    gewoon = [(p[5], si) for si, p in PICKED[term] if p[6] == o["eh"] and p[5] and id(p) not in BAD]
    if len(gewoon) < 2: return
    best, bsi = min(gewoon)
    if o["pp"] < best * .3 or o["pp"] > best * 4: return  # waarschijnlijk een andere maat of soort: geen oordeel
    eh = {"kg": "kilo", "l": "liter", "st": "stuk"}.get(o["eh"], o["eh"])
    if o["pp"] <= best * .97: o["ds"], o["dt"] = "top", f"Laagste prijs per {eh} van alle winkels"
    elif o["pp"] <= best * 1.10: o["ds"], o["dt"] = "ok", "Goede prijs, vergeleken met alle winkels"
    else:
        # Nepkorting: hetzelfde merk is bij een andere supermarkt zonder actie duidelijk goedkoper.
        merk = eerste_woord(o["n"])
        if merk in HUISMERK_W or len(merk) < 3 or merk in norm(term): return  # geen merk, maar de soort zelf (blauwe bessen)
        if term not in _TERMPROD: _TERMPROD[term] = [p for p in matches(term) if p[5] and id(p) not in BAD]
        ow = {w for w in norm(o["n"]) if len(w) > 2 and not w[0].isdigit()}
        o_inh = o["p"] / o["pp"] if o["pp"] else 0
        def lijkt(p):
            pw = {w for w in norm(p[1]) if len(w) > 2 and not w[0].isdigit()}
            if not ow or len(ow & pw) / len(ow | pw) < .6: return False
            inh = p[3] / p[5] if p[5] else 0
            return o_inh > 0 and inh > 0 and 1 / 1.4 <= inh / o_inh <= 1.4  # ongeveer even grote verpakking
        zelfde = [(p[5], p[0]) for p in _TERMPROD[term] if eerste_woord(p[1]) == merk and p[6] == o["eh"] and stores[p[0]]["id"] != o["s"] and lijkt(p)]
        if zelfde:
            b2, s2 = min(zelfde)
            if o["pp"] * .3 < b2 <= o["pp"] * .85: o["ds"], o["dt"] = "duur", f"Zelfde merk zonder actie goedkoper: {eur(b2)} per {eh} bij {NAMEN.get(stores[s2]['id'], stores[s2]['name'])}"
_od = json.load(open(os.path.join(ROOT, "data", "aanbiedingen.json")))
_n = sum(_deel_in(o) for o in _od.get("offers", []))
for o in OFFERS: _deel_in(o)
json.dump(_od, open(os.path.join(OUT, "data", "aanbiedingen.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(_n, "van", len(_od.get("offers", [])), "aanbiedingen in een subcategorie ingedeeld")
OFFJS = '''<script>document.addEventListener("click",e=>{const b=e.target.closest("[data-fc]");if(!b)return;const v=b.dataset.fc;document.querySelectorAll("[data-fc]").forEach(x=>x.setAttribute("aria-pressed",x===b));let n=0;document.querySelectorAll("#grid>li").forEach(li=>{const h=!!v&&li.dataset.c!==v;li.hidden=h;if(!h)n++});document.getElementById("cnt").textContent=n});</script>'''
per_winkel = {}
for o in OFFERS: per_winkel.setdefault(o["s"], []).append(o)
winkels_o = sorted(per_winkel, key=lambda s: NAMEN[s])
def chips_o(cur):
    return '<nav class="chips" aria-label="Supermarkten">' + f'<a class="chip{" on" if not cur else ""}" href="/aanbiedingen/">Alle winkels</a>' + "".join(f'<a class="chip{" on" if cur == s else ""}" href="/aanbiedingen/{s}/">{esc(NAMEN[s])}</a>' for s in winkels_o) + "</nav>"
AP_MERKEN = [("coca-cola", "Coca-Cola"), ("pepsi-max", "Pepsi Max"), ("red-bull", "Red Bull"), ("ben-jerrys", "Ben & Jerry's"), ("ijs", "IJs"), ("hertog-jan", "Hertog Jan"), ("heineken", "Heineken"),
             ("dolce-gusto", "Dolce Gusto"), ("koffiecups", "Koffiecups"), ("douwe-egberts", "Douwe Egberts"), ("mosselen", "Mosselen"), ("pizza", "Pizza"), ("pampers", "Pampers"), ("ariel", "Ariel"), ("lays", "Lay's")]
AP_LINKS = [("krat-bier", "Krat bier"), ("pils", "Bier"), ("gehakt", "Gehakt"), ("kipfilet", "Kipfilet"), ("koffie", "Koffie"), ("wasmiddel", "Wasmiddel"), ("luiers", "Luiers"),
            ("cola", "Cola en frisdrank"), ("toiletpapier", "Toiletpapier"), ("kaas", "Kaas"), ("eieren", "Eieren"), ("chips", "Chips"), ("wijn", "Wijn"), ("boter", "Boter")]
def offers_page(cur, lst):
    nu_ = [o for o in lst if not o.get("v") or o["v"] <= VANDAAG]; straks = [o for o in lst if o.get("v") and o["v"] > VANDAAG]
    nu_.sort(key=lambda o: (-o["pct"], o["p"])); straks.sort(key=lambda o: (o["v"], -o["pct"]))
    path = f"/aanbiedingen/{cur}/" if cur else "/aanbiedingen/"
    eind_tel = {}
    for o in nu_:
        if o.get("t"): eind_tel[o["t"]] = eind_tel.get(o["t"], 0) + 1
    eind = max(eind_tel, key=eind_tel.get) if eind_tel else None
    beste = nu_[0] if nu_ else None
    if cur:
        nm = NAMEN[cur]; naam_actie = "Bonus" if cur == "ah" else "aanbiedingen"
        _wk = datetime.date.fromisoformat(VANDAAG).isocalendar()[1]
        title = (f"AH Bonus folder week {_wk}: {len(nu_)} aanbiedingen" if cur == "ah" else f"{nm} folder week {_wk}: {len(nu_)} aanbiedingen") + (f" t/m {kortdag(eind)}" if eind else "")
        desc = f"Alle {len(nu_)} {naam_actie} van {nm} op een rij, de grootste korting eerst" + (f", zoals {beste['n']} voor {eur(beste['p'])}" if beste else "") + ". Elke dag bijgewerkt, met directe links naar het product."
        h1 = f"{'AH Bonus folder' if cur == 'ah' else nm + ' folder en aanbiedingen'} deze week (week {_wk})"
        lead = f"<span id=\"cnt\">{len(nu_)}</span> acties van {esc(nm)}, de grootste korting eerst." + (f" Plus {len(straks)} acties die binnenkort beginnen." if straks else "")
    else:
        title = f"Supermarkt aanbiedingen week {datetime.date.fromisoformat(VANDAAG).isocalendar()[1]}: {len(nu_)} acties bij {len(winkels_o)} winkels"
        desc = f"De aanbiedingen van {', '.join(NAMEN[s] for s in winkels_o[:-1])} en {NAMEN[winkels_o[-1]]} op één plek, de grootste korting eerst. Elke dag bijgewerkt." if winkels_o else "Supermarktaanbiedingen van deze week."
        h1 = "Alle supermarktaanbiedingen van deze week"
        lead = f"<span id=\"cnt\">{len(nu_)}</span> acties van {len(winkels_o)} supermarkten, de grootste korting eerst. Zet ze op je lijst en zie waar je het goedkoopst uit bent."
    cnt = {}
    for o in nu_: cnt[o.get("c") or "Overig"] = cnt.get(o.get("c") or "Overig", 0) + 1
    # De aanbiedingen zijn ingedeeld in de hoofdgroepen (groepen.json), niet in de subcategorieën.
    order = [g for g, _ in GROEPEN if g in cnt] + (["Overig"] if "Overig" in cnt else [])
    icon = dict(GROEPEN)
    sel = ('<div class="chips" role="group" aria-label="Categorie"><button type="button" class="chip" data-fc="" aria-pressed="true">Alle categorieën</button>' + "".join(f'<button type="button" class="chip" data-fc="{esc(c)}" aria-pressed="false"><span class="ic">{icon.get(c, "🛒")}</span>{esc(c)} ({cnt[c]})</button>' for c in order) + "</div>") if len(order) > 1 else ""
    # De 240 grootste kortingen, plus per categorie de beste 30, zodat elke categorieknop genoeg laat zien.
    toon = set(map(id, nu_[:240]))
    for c in order: toon |= set(map(id, [o for o in nu_ if (o.get("c") or "Overig") == c][:30]))
    toon = [o for o in nu_ if id(o) in toon]
    ch, cld = crumbs(*([("Aanbiedingen", "/aanbiedingen/"), (NAMEN[cur], None)] if cur else [("Aanbiedingen", None)]))
    body = (chips_o(cur) + sel + f'<ul class="offers" id="grid">{"".join(offer_card(o) for o in toon)}</ul>' +
            (f'<h2>Binnenkort in de aanbieding</h2><ul class="offers">{"".join(offer_card(o) for o in straks[:120])}</ul>' if straks else "") +
            '<a class="cta" href="/?v=aanbiedingen">Zoek en filter in alle aanbiedingen</a>'
            '<p class="note">Actieprijzen zoals de supermarkt ze online toont. Bij acties als 1+1 gratis zie je de prijs per stuk als je de actie benut. De prijs aan de kassa is leidend.</p>'
            '<p class="note">Vomar, SPAR, Jan Linders en Nettorama zetten hun acties alleen in een folder of per winkel online. <a href="https://www.vomar.nl/folders" rel="nofollow noopener" target="_blank">Vomar-folder</a> · <a href="https://www.nettorama.nl/actiefolder" rel="nofollow noopener" target="_blank">Nettorama-folder</a></p>'
            + OFFJS)
    ld = [cld, {"@context": "https://schema.org", "@type": "CollectionPage", "name": h1, "url": BASE + path, "dateModified": VANDAAG}]
    if cur and nu_:
        # Op welke dag beginnen de nieuwe acties? Afgeleid uit de meest voorkomende einddag (de dag erna begint de nieuwe week).
        DAGN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
        eindd = {}
        for o in nu_:
            if o.get("t"): wd = datetime.date.fromisoformat(o["t"]).weekday(); eindd[wd] = eindd.get(wd, 0) + 1
        nmw = NAMEN[cur]; actie = "Bonus" if cur == "ah" else "aanbiedingen"
        faq = []
        if eindd:
            ed = max(eindd, key=eindd.get)
            faq.append((f"Op welke dag beginnen de nieuwe {nmw} {actie}?", f"De meeste weekacties van {nmw} lopen tot en met {DAGN[ed]}; de nieuwe {actie} beginnen dus op {DAGN[(ed + 1) % 7]}. Deze pagina werkt elke ochtend bij."))
        b_ = max(nu_, key=lambda o: o["pct"])
        faq.append((f"Wat is de grootste korting bij {nmw} deze week?", f"{b_['n']} voor {eur(b_['p'])}" + (f" in plaats van {eur(b_['was'])}" if b_.get('was') else "") + (f" ({round(b_['pct'] * 100)}% korting)." if b_['pct'] else ".")))
        faq.append((f"Hoeveel aanbiedingen heeft {nmw} deze week?", f"In week {datetime.date.fromisoformat(VANDAAG).isocalendar()[1]} heeft {nmw} {len(nu_)} acties" + (f", en {len(straks)} acties die binnenkort beginnen." if straks else ".")))
        body += faq_html(faq); ld.append(faq_ld(faq))
        if len(straks) >= 15: body += f'<p><a class="cta" href="/aanbiedingen/{cur}/volgende-week/">{esc(nmw)} aanbiedingen volgende week bekijken</a></p>'
    if cur and len(straks) >= 15:
        vpath = f"/aanbiedingen/{cur}/volgende-week/"; vwk = datetime.date.fromisoformat(VANDAAG).isocalendar()[1] % 52 + 1
        vbeg = min(o["v"] for o in straks)
        vch, vcld = crumbs(("Aanbiedingen", "/aanbiedingen/"), (NAMEN[cur], path), ("Volgende week", None))
        vtitle = f"{NAMEN[cur]} folder volgende week (week {vwk}): {len(straks)} aanbiedingen vanaf {kortdag(vbeg)}"
        vdesc = f"De {len(straks)} aanbiedingen van {NAMEN[cur]} die vanaf {kortdag(vbeg)} beginnen, de grootste korting eerst" + (f", zoals {straks[0]['n'][:50]} voor {eur(straks[0]['p'])}" if straks else "") + ". Nu al bekijken en op je lijst zetten."
        vlijst = sorted(straks, key=lambda o: -o["pct"])
        vbody = (f'<ul class="offers" id="grid">{"".join(offer_card(o) for o in vlijst[:150])}</ul>'
                 + f'<p class="note">Acties die bij {esc(NAMEN[cur])} al bekend zijn en binnenkort beginnen. Prijzen kunnen nog wijzigen; elke ochtend bijgewerkt.</p>'
                 + f'<p><a href="{path}">{esc(NAMEN[cur])} aanbiedingen van deze week</a> · <a href="/aanbiedingen/">Alle supermarkten</a></p>')
        schrijf(vpath, page(vpath, vtitle, vdesc, vch + f"<h1>{esc(NAMEN[cur])} aanbiedingen volgende week</h1><p class=\"lead\">Week {vwk}: {len(straks)} acties die vanaf {kortdag(vbeg)} beginnen, de grootste korting eerst.</p>", vbody, [vcld], actief="/aanbiedingen/"))
        made.append((vpath, "0.7"))
    body += '<h2>Aanbiedingen per product</h2><ul class="links">' + "".join(f'<li><a href="/aanbieding/{s_}/">{n_} aanbieding</a></li>' for s_, n_ in AP_LINKS) + "</ul>" + '<h2>Populaire merken in de aanbieding</h2><ul class="links">' + "".join(f'<li><a href="/aanbieding/{s_}/">{esc(n_)} aanbieding</a></li>' for s_, n_ in AP_MERKEN) + "</ul>" + '<h2>Feestdagen</h2><ul class="links"><li><a href="/sinterklaas/">🎁 Sinterklaas: pepernoten en chocoladeletters</a></li><li><a href="/kerst/">🎄 Kerst: gourmet, wild en bubbels</a></li><li><a href="/oud-en-nieuw/">🎆 Oud en nieuw: oliebollen en champagne</a></li></ul>'
    schrijf(path, page(path, title, desc, ch + f"<h1>{esc(h1)}</h1><p class=\"lead\">{lead}</p>", body, ld, actief="/aanbiedingen/"))
    made.append((path, "0.8"))
if OFFERS:
    offers_page(None, OFFERS)
    for s in winkels_o: offers_page(s, per_winkel[s])
print(len(winkels_o) + 1, "aanbiedingenpagina's")

# ---------- goedkoopste supermarkt ----------
# Blok met de uitkomst van de eigen lijst van de bezoeker (die rekent de startpagina uit en bewaart hij in de browser).
JOUW = ('<div class="panel" id="jouw" style="margin-top:16px;background:var(--green-soft);border-color:var(--green)"><b>Waar is jouw eigen lijst het goedkoopst?</b> '
        'Dat hangt af van wat jij koopt. <a href="/#lijst">Maak je lijst</a> en we rekenen het voor je uit.</div>'
        '<script>(()=>{const N=' + json.dumps({s_["id"]: NAMEN.get(s_["id"], s_["name"]) for s_ in stores}, ensure_ascii=False) + ';'
        'let n=0,u=null;try{n=(JSON.parse(localStorage.getItem("lijst-v3")||"[]")||[]).length;u=JSON.parse(localStorage.getItem("lijst-uitkomst")||"null")}catch(e){}'
        'const el=document.getElementById("jouw");if(!n||!el)return;const e=v=>"€ "+v.toFixed(2).replace(".",",");'
        'if(u&&u.n===n&&u.top&&u.top.length){const t=u.top[0];el.innerHTML="<b>Jouw eigen lijst ("+n+(n===1?" artikel":" artikelen")+")</b> is het goedkoopst bij <b>"+(N[t.s]||t.s)+"</b>: <span class=\'tag\'><span class=\'e\'>€</span>"+t.sum.toFixed(2).replace(".",",")+"</span>"+(u.top[1]?". Daarna "+(N[u.top[1].s]||u.top[1].s)+" ("+e(u.top[1].sum)+")":"")+". <a href=\'/#lijst\'>Bekijk je lijst</a>"}'
        'else el.innerHTML="<b>Jouw eigen lijst</b> heeft "+n+(n===1?" artikel":" artikelen")+". <a href=\'/#lijst\'>Bekijk waar die het goedkoopst is</a>"})()</script>')
def nm(si): return NAMEN.get(stores[si]["id"], stores[si]["name"])
if PAK:
    w, l = PAK[0], PAK[-1]
    verschil = l["tot"] - w["tot"]
    title = f"Goedkoopste supermarkt {VANDAAG[:4]}: {nm(w['si'])} (update {MAAND.split()[0]}) – ranglijst {len(PAK)} supermarkten"
    desc = f"We vergeleken {len(PAKTERMEN)} vaste boodschappen bij {len(PAK)} supermarkten. {nm(w['si'])} is het goedkoopst met {eur(w['tot'])}, bij {nm(l['si'])} betaal je {eur(verschil)} meer. Elke dag bijgewerkt."
    trs = "".join(f'<tr{" class=win" if i == 0 else ""}><td><b>{i + 1}. <a href="/supermarkt/{stores[r["si"]]["id"]}/">{esc(nm(r["si"]))}</a></b>{"<span class=sub>" + str(r["mist"]) + " niet gevonden, gerekend met de middenprijs</span>" if r["mist"] else ""}</td><td class="p">{tag(r["tot"])}</td><td class="p">{"" if i == 0 else "+ " + eur(r["tot"] - w["tot"])}<br><span class="unit">{"" if i == 0 else "+" + str(round((r["tot"] / w["tot"] - 1) * 100)) + "%"}</span></td></tr>' for i, r in enumerate(PAK))
    mand = "".join(f"<li>{esc(cap(t))} ({esc(str(q).replace('.', ','))} {esc({'l': 'liter', 'kg': 'kilo', 'st': 'stuks'}[u])})</li>" for t, q, u in PAKKET if t in PAKTERMEN)
    detail = ""
    for r in PAK[:3]:
        detail += f"<h3>{esc(nm(r['si']))}: {eur(r['tot'])}</h3><div class=\"tblwrap\"><table class=\"ptable\"><tbody>" + "".join(f'<tr><td>{esc(cap(t))}</td><td>{"<span class=muted>niet gevonden</span>" if m else esc(p[1])}</td><td class="p">{eur(v)}</td></tr>' for t, v, p, m in r["regels"]) + "</tbody></table></div>"
    faq = [("Welke supermarkt is het goedkoopst?", f"In {MAAND} is {nm(w['si'])} de goedkoopste supermarkt: {len(PAKTERMEN)} vaste boodschappen kosten daar {eur(w['tot'])}. {nm(PAK[1]['si'])} volgt met {eur(PAK[1]['tot'])}."),
           ("Welke supermarkt is het duurst?", f"Van de vergeleken supermarkten is {nm(l['si'])} het duurst: dezelfde boodschappen kosten daar {eur(l['tot'])}, {eur(verschil)} meer dan bij {nm(w['si'])}."),
           ("Hoe wordt dit berekend?", "Voor elke supermarkt zoeken we per boodschap het voordeligste vergelijkbare product en rekenen we met de prijs per kilo, liter of stuk voor een vaste hoeveelheid. Zo vergelijken we precies dezelfde boodschappen. Aanbiedingen die nu lopen tellen mee."),
           ("Hoe vaak wordt dit bijgewerkt?", "Elke dag. De prijzen komen van de webshops van de supermarkten.")]
    ch, cld = crumbs(("Goedkoopste supermarkt", None))
    head = ch + f"<h1>De goedkoopste supermarkt van {MAAND}</h1><p class=\"lead\">Een vast boodschappenmandje van {len(PAKTERMEN)} producten, voor iedereen hetzelfde, kost bij <b>{esc(nm(w['si']))}</b> {eur(w['tot'])}. Bij {esc(nm(l['si']))} betaal je {eur(verschil)} meer.</p>" + JOUW
    # Waarom bovenaan: per product welke winkel het goedkoopst is (zuiver uitgerekend, niemand betaalt voor een plek).
    _wins = {}
    for i_, t_ in enumerate(PAKTERMEN):
        vv = [(r["regels"][i_][1], r["si"]) for r in PAK]; mn = min(v for v, _ in vv)
        for v, si_ in vv:
            if v <= mn + .004: _wins[si_] = _wins.get(si_, 0) + 1
    _waarom_html = (f'<div class="panel"><p style="margin:0"><b>Waarom staat {esc(nm(w["si"]))} bovenaan?</b> Puur uitgerekend: het hele mandje is daar het goedkoopst. '
                    f'Bij {_wins.get(w["si"], 0)} van de {len(PAKTERMEN)} producten is {esc(nm(w["si"]))} zelf de goedkoopste winkel. '
                    'Geen enkele supermarkt betaalt voor een plek. <a href="/zo-vergelijken-wij/">Zo vergelijken wij</a></p></div>')
    paren = [(a, b) for a, b in itertools.combinations([r["si"] for r in PAK[:8]], 2)]
    body = (f'<div class="tblwrap"><table class="ptable"><thead><tr><th>Supermarkt</th><th style="text-align:right">Totaal</th><th style="text-align:right">Verschil</th></tr></thead><tbody>{trs}</tbody></table></div>'
            f'<p class="note">Bijgewerkt op {DATUM}. Supermarkten met te weinig producten online (zoals Vomar en Poiesz) staan alleen in de lijst als we genoeg van deze boodschappen vinden.</p>'
            + _waarom_html +
            f'<h2>Wat zit er in het vaste boodschappenmandje?</h2><p class="note">Dit mandje is voor iedereen hetzelfde en staat los van je eigen lijst.</p><ul class="links">{mand}</ul><h2>Zo is het opgebouwd</h2>{detail}'
            + '<h2>Twee supermarkten vergelijken</h2><ul class="links">' + "".join(f'<li><a href="/vergelijk-supermarkten/{stores[a]["id"]}-of-{stores[b]["id"]}/">{esc(nm(a))} of {esc(nm(b))}?</a></li>' for a, b in paren) + "</ul>"
            + faq_html(faq) + '<a class="cta" href="/">Bereken het voor je eigen lijst</a>')
    schrijf("/goedkoopste-supermarkt/", page("/goedkoopste-supermarkt/", title, desc, head, body, [cld, faq_ld(faq)], actief="/goedkoopste-supermarkt/", og_title=f"De goedkoopste supermarkt van {MAAND}"))
    made.append(("/goedkoopste-supermarkt/", "0.9"))
    # Onderlinge vergelijkingen: "AH of Jumbo, wie is goedkoper?"
    for a, b in paren:
        ra, rb = next(r for r in PAK if r["si"] == a), next(r for r in PAK if r["si"] == b)
        win, lose = (ra, rb) if ra["tot"] <= rb["tot"] else (rb, ra)
        diff = lose["tot"] - win["tot"]; pct = round((lose["tot"] / win["tot"] - 1) * 100)
        path = f"/vergelijk-supermarkten/{stores[a]['id']}-of-{stores[b]['id']}/"
        wins_a = sum(1 for t in PICKED if PICKED[t][0][0] == a); wins_b = sum(1 for t in PICKED if PICKED[t][0][0] == b)
        regels = "".join(f'<tr><td>{esc(cap(t))}</td><td class="p">{eur(va)}</td><td class="p">{eur(vb)}</td></tr>' for (t, va, _, _), (_, vb, _, _) in zip(ra["regels"], rb["regels"]))
        title = f"{nm(a)} of {nm(b)}: {nm(win['si'])} is {pct}% goedkoper ({MAAND})"
        desc = f"Dezelfde {len(PAKTERMEN)} boodschappen kosten bij {nm(win['si'])} {eur(win['tot'])} en bij {nm(lose['si'])} {eur(lose['tot'])}. Bekijk per product wie goedkoper is. Elke dag bijgewerkt."
        ch, cld = crumbs(("Goedkoopste supermarkt", "/goedkoopste-supermarkt/"), (f"{nm(a)} of {nm(b)}", None))
        faq = [(f"Is {nm(a)} goedkoper dan {nm(b)}?", f"{'Ja' if win['si'] == a else 'Nee'}. Voor dezelfde {len(PAKTERMEN)} boodschappen betaal je bij {nm(win['si'])} {eur(win['tot'])} en bij {nm(lose['si'])} {eur(lose['tot'])}: {eur(diff)} ({pct}%) verschil.")]
        head = ch + f"<h1>{esc(nm(a))} of {esc(nm(b))}: wie is goedkoper?</h1><p class=\"lead\">{esc(nm(win['si']))} is {pct}% goedkoper: {eur(win['tot'])} tegen {eur(lose['tot'])} voor dezelfde {len(PAKTERMEN)} boodschappen.</p>"
        body = (f'<div class="tblwrap"><table class="ptable"><thead><tr><th>Boodschap</th><th style="text-align:right">{esc(nm(a))}</th><th style="text-align:right">{esc(nm(b))}</th></tr></thead><tbody>{regels}'
                f'<tr class="win"><td><b>Totaal</b></td><td class="p">{tag(ra["tot"])}</td><td class="p">{tag(rb["tot"])}</td></tr></tbody></table></div>'
                f'<p class="note">Van de {len(PICKED)} producten op deze site is {esc(nm(a))} bij {wins_a} het goedkoopst en {esc(nm(b))} bij {wins_b}. Bijgewerkt op {DATUM}.</p>'
                f'{faq_html(faq)}<p><a href="/supermarkt/{stores[a]["id"]}/">Alles over {esc(nm(a))}</a> · <a href="/supermarkt/{stores[b]["id"]}/">Alles over {esc(nm(b))}</a> · <a href="/goedkoopste-supermarkt/">Alle supermarkten</a></p><a class="cta" href="/">Vergelijk je eigen lijst</a>')
        schrijf(path, page(path, title, desc, head, body, [cld, faq_ld(faq)], actief="/goedkoopste-supermarkt/"))
        made.append((path, "0.6"))

# ---------- supermarktpagina's ----------
for si, s in enumerate(stores):
    if not s["count"]: continue
    sid = s["id"]; nm_ = NAMEN.get(sid, s["name"]); path = f"/supermarkt/{sid}/"
    wint = [t for t in PICKED if PICKED[t][0][0] == si]
    acties = sorted([o for o in NU_GELDIG if o["s"] == sid], key=lambda o: -o["pct"])
    r = next((r for r in PAK if r["si"] == si), None)
    rang = PAKRANG.get(si)
    kern = (f"{nm_} staat op plek {rang} van de {len(PAK)} supermarkten: dezelfde boodschappen kosten er {eur(r['tot'])}" + (f", {eur(r['tot'] - PAK[0]['tot'])} meer dan bij {nm(PAK[0]['si'])}." if rang > 1 else ", de laagste prijs van allemaal.")) if r else f"Van {nm_} staan te weinig producten online voor een eerlijke vergelijking van het hele mandje."
    title = f"Is {nm_} goedkoop? Prijzen en aanbiedingen vergeleken ({MAAND})"
    desc = f"{kern} Bekijk welke producten bij {nm_} het goedkoopst zijn" + (f" en alle {len(acties)} aanbiedingen van deze week." if acties else ".")
    ch, cld = crumbs(("Goedkoopste supermarkt", "/goedkoopste-supermarkt/"), (nm_, None))
    head = ch + f"<h1>Is {esc(nm_)} goedkoop?</h1><p class=\"lead\">{esc(kern)}</p>"
    body = ""
    if acties:
        body += f'<h2>{"AH Bonus" if sid == "ah" else "Aanbiedingen"} van deze week</h2><ul class="offers">{"".join(offer_card(o) for o in acties[:12])}</ul><a class="cta" href="/aanbiedingen/{sid}/">Alle {len(acties)} aanbiedingen van {esc(nm_)}</a>'
    if wint:
        body += f"<h2>Hier is {esc(nm_)} het goedkoopst</h2><ul class=\"links\">" + "".join(f'<li><a href="/vergelijk/{slug(t)}/">{esc(cap(t))}</a></li>' for t in wint[:60]) + "</ul>"
    body += f"<h2>{esc(nm_)} vergelijken met</h2><ul class=\"links\">" + "".join(f'<li><a href="/vergelijk-supermarkten/{stores[a]["id"]}-of-{stores[b]["id"]}/">{esc(nm(b if a == si else a))}</a></li>' for a, b in itertools.combinations([r_["si"] for r_ in PAK[:8]], 2) if si in (a, b)) + "</ul>" if r and rang <= 8 else ""
    hier = [m_ for m_ in MAAL if m_["rang"] and m_["rang"][0][0] == si]
    top3 = [m_ for m_ in MAAL if any(x[0] == si for x in m_["rang"][:3]) and m_ not in hier]
    if hier or top3:
        body += (f"<h2>Complete maaltijden: goedkoop bij {esc(nm_)}</h2>" + (f"<p>Hier is {esc(nm_)} de goedkoopste supermarkt voor het hele gerecht:</p><ul class=\"links\">" + "".join(f'<li><a href="/maaltijden/{m_["slug"]}/">{esc(m_["naam"])}</a> ({eur(m_["rang"][0][1]["tot"])})</li>' for m_ in hier) + "</ul>" if hier else "")
                 + (f"<p>Bij deze maaltijden hoort {esc(nm_)} bij de 3 goedkoopste:</p><ul class=\"links\">" + "".join(f'<li><a href="/maaltijden/{m_["slug"]}/">{esc(m_["naam"])}</a></li>' for m_ in top3) + "</ul>" if top3 else ""))
    body += f'<p class="note">{s["count"]:,} producten van {esc(nm_)} in de vergelijking. Bijgewerkt op {DATUM}.</p>'.replace(",", ".")
    schrijf(path, page(path, title, desc, head, body, [cld], actief="/goedkoopste-supermarkt/"))
    made.append((path, "0.6"))

# ---------- over en privacy ----------
over = f'''<div class="panel"><h2 style="margin-top:0">Ik verdien er niets aan</h2><p>Goedkope Boodschappen is een hobbyproject van Erik. Er staat geen reclame op, supermarkten kunnen geen plek kopen en er zitten geen affiliatelinks in: als je doorklikt naar een supermarkt, krijg ik daar niets voor. De volgorde is altijd gewoon: goedkoopste eerst. <a href="/zo-vergelijken-wij/">Lees precies hoe we vergelijken</a>.</p></div>
<h2>Waarom deze site?</h2><p>Boodschappen zijn duur en iedere supermarkt is ergens anders goedkoop. Met deze site zie je in een paar seconden waar jouw lijst het minst kost, zonder dat je zelf tien folders hoeft door te bladeren.</p>
<h2>Waar komen de prijzen vandaan?</h2><p>Elke dag halen we automatisch de prijzen en aanbiedingen op van de webshops van {AANTAL} supermarkten: {", ".join(NAMEN[s] for s in ACTIEF if s in NAMEN)}. De gewone prijzen komen deels uit de open dataset van <a href="https://www.checkjebon.nl/" rel="noopener">Checkjebon</a> (MIT-licentie). Vomar, SPAR, Jan Linders en Nettorama zetten hun acties niet als losse prijzen online; daarvan tonen we alleen de gewone prijzen waar die beschikbaar zijn. Coop is inmiddels PLUS geworden.</p>
<p>Supermarkten kunnen in de winkel een andere prijs hanteren dan online. De prijs aan de kassa is altijd leidend.</p>
<h2>Hoe vergelijken we?</h2><p>Per product zoeken we bij elke supermarkt het voordeligste vergelijkbare product en vergelijken we de prijs per kilo, liter of stuk. Varianten als lactosevrij of biologisch tellen alleen mee als je ernaar zoekt. Lopende aanbiedingen rekenen we mee.</p>
<h2>Contact</h2><p>Een fout gezien of een idee? Mail naar <a href="mailto:goedkopeboodschappen@proton.me">goedkopeboodschappen@proton.me</a>.</p>'''
schrijf("/over/", page("/over/", "Over Goedkope Boodschappen: gratis, onafhankelijk en zonder reclame", "Goedkope Boodschappen is een gratis hobbyproject zonder reclame of commissie. Lees waar de prijzen vandaan komen en hoe we vergelijken.",
    crumbs(("Over deze site", None))[0] + "<h1>Over deze site</h1><p class=\"lead\">Gratis, onafhankelijk en zonder reclame. Gemaakt om je geld te besparen, niet om aan je te verdienen.</p>", over))
# ---------- Zo vergelijken wij: open over de werkwijze, zodat iedereen ziet dat er geen winkel voorgaat ----------
_nprod = sum(1 for p in prods if stores[p[0]].get("count"))
zvw = (f'''<div class="panel"><h2 style="margin-top:0">Onze belofte</h2><ul class="beloftes">
<li><b>Goedkoopste eerst, altijd.</b> De volgorde komt alleen uit de prijs per kilo, liter of stuk. Er is geen knop waarmee ik een winkel hoger kan zetten.</li>
<li><b>Geen betaalde plekken.</b> Supermarkten en merken kunnen niets kopen: geen advertenties, geen gesponsorde producten, geen "uitgelicht".</li>
<li><b>Geen commissie.</b> Klik je door naar een webshop, dan krijg ik daar niets voor. Er zitten geen affiliatelinks in.</li>
<li><b>Voor elke winkel dezelfde regels.</b> Albert Heijn, Lidl of Vomar: alles gaat door dezelfde berekening.</li>
<li><b>Ik verdien er niets aan.</b> Dit is een gratis hobbyproject van Erik, zonder reclame of abonnement.</li></ul></div>
<h2>Waar komen de prijzen vandaan?</h2><p>Elke dag halen we automatisch de prijzen en aanbiedingen op van de webshops van {AANTAL} supermarkten: {", ".join(NAMEN[s] for s in ACTIEF if s in NAMEN)}. Een deel van de gewone prijzen komt uit de open dataset van <a href="https://www.checkjebon.nl/" rel="noopener">Checkjebon</a>. Nu zitten er <b>{_nprod:,}</b> producten in de vergelijking; de laatste update was op {DATUM}.</p>
<p>Online prijzen kunnen afwijken van de winkel. De prijs aan de kassa is altijd leidend.</p>
<h2>Hoe kiezen we het vergelijkbare product?</h2><ul>
<li>Per product zoeken we bij elke supermarkt het <b>voordeligste vergelijkbare</b> product: dezelfde soort, met huismerken en A-merken door elkaar.</li>
<li>We vergelijken de <b>prijs per kilo, liter of stuk</b>, zodat een grote en een kleine verpakking eerlijk naast elkaar staan.</li>
<li>Varianten zoals lactosevrij, biologisch of light tellen alleen mee als je daar zelf naar zoekt.</li>
<li>Producten waarvan we de inhoud niet kunnen lezen, zetten we onderaan in plaats van ze te raden.</li></ul>
<h2>Aanbiedingen</h2><p>Lopende aanbiedingen rekenen we mee in de prijs, maar alleen in de dagen dat ze echt geldig zijn. We bewaren elke dag de prijzen. Daarmee zie je bij een product of de prijs nu <b>lager of hoger dan normaal</b> is. Normaal is het midden van de laatste 30 metingen bij die winkel. Zo zie je meteen of een "aanbieding" echt voordelig is.</p>
<p>Persoonlijke aanbiedingen (zoals een persoonlijke bonus op je klantenkaart) en zegeltjes kunnen we niet zien. Die tellen dus niet mee.</p>
<h2>Welke supermarkt is het goedkoopst?</h2><p>Daarvoor gebruiken we een vast boodschappenmandje van {len(PAKTERMEN)} gewone producten, van melk en brood tot wasmiddel. Per winkel tellen we het voordeligste vergelijkbare product op, voor dezelfde hoeveelheid. We nemen alleen producten mee die bij álle vergeleken winkels te koop zijn. Zo wordt geen winkel goedkoper omdat hij iets niet verkoopt. Een winkel waar online te veel ontbreekt, laten we in deze ranglijst weg.</p>
<h2>Complete maaltijden</h2><p>Bij maaltijden rekenen we met <b>hele verpakkingen</b>, zoals aan de kassa: heb je 300 gram nodig en zit het per 500 gram, dan betaal je 500 gram. Olie, zout en kruiden uit de voorraadkast tellen niet mee. De recepten komen van bekende receptensites; bij elk gerecht staat de bron.</p>
<h2>Fout gezien?</h2><p>Bij elk product staat een knop <b>Klopt niet?</b>. Daarmee meld je met één tik een verkeerde prijs of een product dat niet klopt. Ik kijk elke melding na. Je kunt ook mailen naar <a href="mailto:goedkopeboodschappen@proton.me">goedkopeboodschappen@proton.me</a>.</p>
<p><a href="/over/">Over deze site</a> · <a href="/goedkoopste-supermarkt/">Goedkoopste supermarkt</a> · <a href="/privacy/">Privacy</a></p>''').replace(f"{_nprod:,}", f"{_nprod:,}".replace(",", "."))
_zfaq = [("Krijgt Goedkope Boodschappen geld van supermarkten?", "Nee. Er is geen reclame, er zijn geen betaalde plekken en geen affiliatelinks. De site is gratis en ik verdien er niets aan."),
         ("Kan een supermarkt hoger in de lijst komen?", "Nee. De volgorde komt alleen uit de prijs per kilo, liter of stuk. Voor elke winkel gelden dezelfde regels."),
         ("Hoe vaak worden de prijzen bijgewerkt?", "Elke dag, automatisch. Aanbiedingen tellen alleen mee in de dagen dat ze geldig zijn.")]
schrijf("/zo-vergelijken-wij/", page("/zo-vergelijken-wij/", "Zo vergelijken wij: onafhankelijk en zonder betaalde plekken", "Hoe Goedkope Boodschappen prijzen vergelijkt: elke dag nieuwe prijzen, prijs per kilo of liter, geen reclame, geen commissie en voor elke supermarkt dezelfde regels.",
    crumbs(("Over deze site", "/over/"), ("Zo vergelijken wij", None))[0] + "<h1>Zo vergelijken wij</h1><p class=\"lead\">Eerlijk en open: hoe we prijzen ophalen en vergelijken, en waarom er geen supermarkt voorgaat.</p>", zvw + faq_html(_zfaq), [faq_ld(_zfaq)]))
made.append(("/zo-vergelijken-wij/", "0.6"))
privacy = '''<h2>Je boodschappenlijst</h2><p>Je lijst en je gekozen supermarkten worden alleen in je eigen browser bewaard. Ze worden niet naar ons verstuurd. Wis je je browsergegevens, dan is je lijst weg.</p>
<h2>Meldingen</h2><p>Zet je meldingen aan, dan bewaren we alleen wat nodig is om je een bericht te sturen: het anonieme adres dat je browser daarvoor maakt, de productnamen op je lijst en je gekozen supermarkten. Geen naam, geen e-mailadres. Zet je meldingen uit, dan wissen we dit meteen.</p>
<h2>Samen één lijst</h2><p>Deel je je lijst met je huisgenoot, dan bewaren we die lijst (per artikel de productnaam, winkel, link, prijs, aantal en of het is afgevinkt) onder een willekeurige code. Iedereen met de link kan de lijst zien en wijzigen; deel hem dus alleen met wie je vertrouwt. Geen naam, geen e-mailadres. Na 60 dagen zonder gebruik wissen we de lijst.</p><h2>Foto van kassabon of lijstje</h2><p>De tekst op je foto wordt op je eigen toestel herkend. De foto wordt niet naar ons gestuurd en niet bewaard. Alleen het herkenningsprogramma (Tesseract) wordt eenmalig van cdn.jsdelivr.net geladen.</p><h2>E-mail bij aanbiedingen</h2><p>Meld je je aan voor e-mail, dan bewaren we je e-mailadres, de productnamen op je lijst, je gekozen supermarkten en de prijsalarmen die je zelf instelt (soort en maximale prijs). Je krijgt eerst een mail om te bevestigen; zonder bevestiging sturen we niets en wissen we je adres na 7 dagen. Je krijgt hoogstens één mail per dag, en alleen als er iets nieuws in de aanbieding is. Elke mail heeft een afmeldlink; afmelden wist je adres meteen. We gebruiken je adres nergens anders voor en geven het aan niemand.</p>
<h2>Supermarkten in de buurt</h2><p>Tik je op "Zoek winkels bij mij in de buurt", dan vraagt je browser eerst toestemming voor je locatie. Je locatie gaat dan alleen naar <a href="https://www.openstreetmap.org/" rel="noopener">OpenStreetMap</a> (via de openbare Overpass-dienst) om de supermarkten in de buurt op te zoeken. Wij krijgen je locatie niet en bewaren hem nergens. In je eigen browser onthouden we alleen welke winkels je aan hebt staan en waar de dichtstbijzijnde vestigingen zijn, zodat je er met één tik naartoe kunt navigeren. Tik je op Route, dan opent Google Maps; daar gelden de regels van Google.</p>
<h2>"Klopt niet?"</h2><p>Meld je dat een product of prijs niet klopt, dan bewaren we alleen het product, de winkel, wat er niet klopt en je toelichting. Om te zorgen dat één persoon niet steeds hetzelfde kan melden, maken we van je internetadres een onomkeerbare code die na hooguit een maand verloopt; je internetadres zelf bewaren we niet. Je kunt hooguit 5 meldingen per dag doen; wie die grens op 3 dagen in een maand haalt, kan de rest van die maand niets melden. Melden drie verschillende mensen hetzelfde product, dan laten we het tijdelijk weg tot we het hebben gecontroleerd. We gebruiken de meldingen alleen om fouten te verbeteren.</p>
<h2>Bezoekersstatistieken</h2><p>We tellen bezoeken met <a href="https://www.goatcounter.com/" rel="noopener">GoatCounter</a>. Dat gebruikt geen cookies en slaat geen persoonsgegevens op. We zien bijvoorbeeld hoeveel mensen de site bezoeken, welke pagina's populair zijn en naar welke producten wordt gezocht, maar nooit wie jij bent. Daarom hoef je ook geen cookiemelding weg te klikken.</p>
<h2>Cookies</h2><p>Deze site plaatst geen cookies. Klik je door naar een supermarkt, dan gelden daar de regels van die supermarkt.</p>
<h2>Vragen</h2><p>Mail naar <a href="mailto:goedkopeboodschappen@proton.me">goedkopeboodschappen@proton.me</a>.</p>'''
schrijf("/privacy/", page("/privacy/", "Privacy: geen cookies, geen tracking | Goedkope Boodschappen", "Je boodschappenlijst blijft in je eigen browser. Geen cookies, geen persoonsgegevens, geen cookiemelding.",
    crumbs(("Privacy", None))[0] + "<h1>Privacy</h1><p class=\"lead\">Kort gezegd: geen cookies, geen persoonsgegevens, en je lijst blijft op je eigen apparaat.</p>", privacy))
made += [("/over/", "0.4"), ("/privacy/", "0.3")]

# ---------- complete maaltijden ----------
exec(open(os.path.join(ROOT, "scripts", "bouw_maaltijden.py")).read())

# ---------- startpagina ----------
app = open(os.path.join(ROOT, "site", "index.html")).read()
pop = ["halfvolle melk", "eieren", "jonge kaas", "pindakaas", "hagelslag", "volkoren brood", "koffiebonen", "bananen", "kipfilet", "gehakt", "spaghetti", "rijst", "coca cola", "chips", "toiletpapier", "wasmiddel", "roomboter", "aardappelen", "tomaten", "olijfolie"]
pop = [t for t in pop if t in PICKED]
faq = [("Welke supermarkt is het goedkoopst?", f"In {MAAND} is {nm(PAK[0]['si'])} het goedkoopst voor een vast boodschappenmandje van {len(PAKTERMEN)} producten ({eur(PAK[0]['tot'])}), gevolgd door {nm(PAK[1]['si'])} ({eur(PAK[1]['tot'])})." if len(PAK) > 1 else "Dat verschilt per product. Zoek je boodschappen op en zie het meteen."),
       ("Is Goedkope Boodschappen gratis?", "Ja. Er is geen account nodig, er staat geen reclame op en ik verdien er niets aan. Supermarkten betalen niet voor een plek."),
       ("Hoe actueel zijn de prijzen?", "De prijzen en aanbiedingen worden elke dag automatisch opgehaald van de webshops van de supermarkten. De prijs aan de kassa is leidend."),
       ("Blijft mijn boodschappenlijst bewaard?", "Ja, je lijst wordt bewaard in je eigen browser. Kom je terug, dan zie je meteen welke producten goedkoper of duurder zijn geworden en wat er in de aanbieding is.")]
seo = (f'<section class="wrap seo" aria-labelledby="sh"><h2 id="sh">Boodschappen vergelijken bij {AANTAL} supermarkten</h2>'
       f'<p>Goedkope Boodschappen vergelijkt de prijzen van {", ".join(NAMEN[s] for s in ACTIEF[:-1] if s in NAMEN)} en {NAMEN.get(ACTIEF[-1], "")}. Je ziet per product de prijs per kilo of liter, bij welke supermarkt het het goedkoopst is en een directe link naar het product. De aanbiedingen van deze week tellen automatisch mee.</p>'
       + (f'<p><b>Goedkoopste supermarkt van {MAAND}:</b> <a href="/goedkoopste-supermarkt/">{esc(nm(PAK[0]["si"]))}</a>, gevolgd door {esc(nm(PAK[1]["si"]))} en {esc(nm(PAK[2]["si"]))}.</p>' if len(PAK) > 2 else "")
       + '<h3>Populaire producten</h3><ul class="links">' + "".join(f'<li><a href="/vergelijk/{slug(t)}/">{esc(cap(t))}</a></li>' for t in pop) + '<li><a href="/vergelijk/">Alle producten</a></li></ul>'
       + '<h3>Aanbiedingen per supermarkt</h3><ul class="links">' + "".join(f'<li><a href="/aanbiedingen/{s}/">{"AH Bonus" if s == "ah" else esc(NAMEN[s]) + " aanbiedingen"}</a></li>' for s in winkels_o) + '</ul>'
       + '<h3>Complete maaltijden</h3><ul class="links">' + "".join(f'<li><a href="/maaltijden/{m["slug"]}/">{esc(m["naam"])}</a></li>' for m in MAAL) + '<li><a href="/maaltijden/">Alle maaltijden</a></li></ul>'
       + '<h3>Categorieën</h3><ul class="links">' + "".join(f'<li><a href="{p}">{c[1]} {esc(c[0])}</a></li>' for c, p, _ in catpaths) + '</ul>'
       + faq_html(faq) + "</section>")
ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "Goedkope Boodschappen", "url": BASE + "/", "inLanguage": "nl-NL",
       "potentialAction": {"@type": "SearchAction", "target": BASE + "/?q={search_term_string}", "query-input": "required name=search_term_string"}},
      {"@context": "https://schema.org", "@type": "Organization", "name": "Goedkope Boodschappen", "url": BASE + "/", "logo": BASE + "/icons/icon-512.png", "email": "goedkopeboodschappen@proton.me"},
      faq_ld(faq)]
cats_app = [[c[0], c[1], [t for t in c[2] if t in PICKED], c[3]] for c in CATS if any(t in PICKED for t in c[2])]
# Prijslijst in twee delen, zodat de app snel start: eerst alle producten die bij een categorie horen (ongeveer de helft),
# daarna op de achtergrond de rest (voor zoeken naar bijzondere producten). producten.json zelf blijft ook bestaan.
_pd = json.load(open(os.path.join(OUT, "producten.json")))
_n = len(_pd["products"]); _kern = {i for i in range(_n) if id(prods[i]) in KERN}
json.dump({"stores": _pd["stores"], "products": [p_ for i, p_ in enumerate(_pd["products"]) if i in _kern], "totaal": _n},
          open(os.path.join(OUT, "producten-kern.json"), "w"), ensure_ascii=False, separators=(",", ":"))
json.dump({"products": [p_ for i, p_ in enumerate(_pd["products"]) if i not in _kern]},
          open(os.path.join(OUT, "producten-rest.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(_kern), "van", _n, "producten in producten-kern.json")
# Ook per winkel (p/<winkel>-kern.json en p/<winkel>-rest.json): de app laadt dan alleen de winkels die je aan hebt staan.
os.makedirs(os.path.join(OUT, "p"), exist_ok=True)
_per = {}
for i, p_ in enumerate(_pd["products"]): _per.setdefault((p_[0], i in _kern), []).append(p_)
_tel = {}
for si_, s_ in enumerate(_pd["stores"]):
    for deel, k_ in (("kern", True), ("rest", False)):
        json.dump(_per.get((si_, k_), []), open(os.path.join(OUT, "p", f"{s_['id']}-{deel}.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    _tel[s_["id"]] = len(_per.get((si_, True), [])) + len(_per.get((si_, False), []))
json.dump({"stores": _pd["stores"], "n": _tel}, open(os.path.join(OUT, "winkels.json"), "w"), ensure_ascii=False, separators=(",", ":"))
# Prijzen per soort en winkel voor het weekoverzicht per mail (netlify/functions/weekoverzicht.mjs):
# {soort: {"w": {winkel: prijs}, "n": naam van het goedkoopste product, "s": winkel daarvan}}
_tp = {}
for t_, rows in PICKED.items():
    w = {stores[si]["id"]: round(eff(p_), 2) for si, p_ in rows if id(p_) not in BAD}
    u = {stores[si]["id"]: round(vgl_unit(p_), 3) for si, p_ in rows if id(p_) not in BAD and vgl_unit(p_) is not None}
    if w:
        si0, p0_ = rows[0]
        _tp[t_.lower()] = {"t": t_, "w": w, "u": u, "n": p0_[1], "s": stores[si0]["id"]}
json.dump({"dag": VANDAAG, "soorten": _tp}, open(os.path.join(OUT, "data", "termprijzen.json"), "w"), ensure_ascii=False, separators=(",", ":"))
# A-merken voor de app: eerste woord van de productnaam, bij minstens 3 supermarkten, en meestal vooraan (niet een gewoon woord).
_eerst, _overal, _win = {}, {}, {}
for _p in prods:
    _w = re.findall(r"[a-z0-9à-ÿ'&+-]+", _p[1].lower())
    if not _w: continue
    _eerst[_w[0]] = _eerst.get(_w[0], 0) + 1; _win.setdefault(_w[0], set()).add(stores[_p[0]]["id"])
    for _x in set(_w): _overal[_x] = _overal.get(_x, 0) + 1
AMERK = sorted(f for f, ws in _win.items() if not f[0].isdigit() and len(f) > 1 and len(ws) >= 3 and _eerst[f] / _overal[f] >= .7)
app = app.replace("{{AMERK}}", json.dumps(AMERK, ensure_ascii=False))
app = (app.replace("{{EIWIT}}", json.dumps(EIWIT, ensure_ascii=False)).replace("{{VERFIJN}}", json.dumps(VERFIJN, ensure_ascii=False)).replace("{{VARIANT}}", json.dumps(VARIANT, ensure_ascii=False)).replace("{{VERSIE}}", VERSIE).replace("{{AANTAL}}", str(AANTAL)).replace("{{CATS}}", json.dumps(cats_app, ensure_ascii=False)).replace("{{KCAL}}", json.dumps({t: kcal_txt(t) for t in PICKED if kcal_txt(t)}, ensure_ascii=False)).replace("{{GROEPEN}}", json.dumps([gg for gg in GROEPEN if any(c[3] == gg[0] for c in cats_app)], ensure_ascii=False))
          .replace("{{LDJSON}}", json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")).replace("<!--SEO-->", seo).replace("<!--MAALTIJDEN-->", MAAL_HOME)
          .replace("bij 11 supermarkten", f"bij {AANTAL} supermarkten").replace("Vergelijk 11 winkels", f"Vergelijk {AANTAL} winkels"))
open(os.path.join(OUT, "index.html"), "w").write(app)
made.insert(0, ("/", "1.0"))

# ---------- Glutenvrij: alle producten met glutenvrij in de naam, per soort ----------
GV_SOORTEN = [  # (slug, naam, icoon, woorden in de productnaam)
    ("brood", "Glutenvrij brood", "🍞", ["brood", "bollen", "broodje", "desem", "baguette", "ciabatta", "bagel", "buns", "flatbread", "pita", "tijger", "volkoren", "meergranen"]),
    ("pasta", "Glutenvrije pasta", "🍝", ["pasta", "spaghetti", "penne", "fusilli", "macaroni", "lasagne", "tagliatelle", "farfalle", "tortellini", "ravioli", "gnocchi", "noedels", "mie"]),
    ("crackers", "Glutenvrije crackers en knäckebröd", "🍘", ["cracker", "knäcke", "knacke", "beschuit", "toast", "rijstwafel", "maiswafel", "grissin", "soepstengel", "cracotte"]),
    ("koek", "Glutenvrije koek, cake en snoep", "🍪", ["koek", "wafel", "cake", "brownie", "biscuit", "muffin", "cookie", "speculaas", "taart", "donut", "reep", "chocolade", "snoep", "drop", "gevuld", "croissant", "kaneel", "spekulatius", "lange vinger", "madeleine"]),
    ("ontbijt", "Glutenvrije ontbijtgranen", "🥣", ["muesli", "granola", "cornflakes", "havermout", "cereal", "crunch", "flakes", "pap", "ontbijt", "porridge", "oats"]),
    ("bakken", "Glutenvrij meel en bakmixen", "🥖", ["meel", "bloem", "mix", "bakmix", "paneermeel", "maizena", "deeg"]),
    ("diepvries", "Glutenvrije pizza en snacks", "🍕", ["pizza", "nugget", "schnitzel", "kroket", "bitterbal", "frikandel", "loempia", "snack", "burger", "quiche"]),
    ("sauzen", "Glutenvrije sauzen en ketjap", "🥫", ["ketjap", "saus", "tamari", "soja", "jus", "bouillon", "soep", "dressing", "mayonaise"]),
    ("bier", "Glutenvrij bier", "🍺", ["bier", "pils", "beer", "lager"]),
]
def _gv_soort(naam):
    n = naam.lower()
    for sl, _, _, ws in GV_SOORTEN:
        if any(w in n for w in ws): return sl
    return None
def _ut(p):
    u = eff_unit(p)
    if u is None or not p[6]: return ""
    return f"{eur(u)} per {dict(kg='kilo', l='liter', st='stuk').get(p[6], p[6])}"
GV_PER = {}
for p in prods:
    if not stores[p[0]].get("count") or not GV_RE.search(p[1]): continue
    sl = _gv_soort(p[1])
    if sl: GV_PER.setdefault(sl, []).append(p)
def _gv_sort(p):
    u = eff_unit(p); return (u if u is not None else 1e9, eff(p))
GV_LIJST = [(sl, nm_, ic) for sl, nm_, ic, _ in GV_SOORTEN if len({p[0] for p in GV_PER.get(sl, [])}) >= 2]
if GV_LIJST:
    totaal = sum(len(GV_PER[sl]) for sl, _, _ in GV_LIJST)
    def _rij(p, t):
        return (f'<tr><td><span class="shop">{esc(nm(p[0]))}</span> <a href="{esc(plink(p))}" rel="nofollow noopener" target="_blank" data-out="{stores[p[0]]["id"]}"><b>{esc(p[1])}</b></a>'
                f'<span class="sub">{esc(p[4] or "")}</span>{fout_knop(t, p[0], p)}{addbtn(p, t)}</td><td class="p">{tag(eff(p))}<span class="sub">{esc(_ut(p))}</span></td></tr>')
    for sl, naam_, ic in GV_LIJST:
        arr = sorted(GV_PER[sl], key=_gv_sort)
        best = {}
        for p in arr: best.setdefault(p[0], p)
        bestl = sorted(best.values(), key=_gv_sort)
        w = bestl[0]; n_w = len(best)
        path = f"/glutenvrij/{sl}/"
        title = f"{naam_} vergelijken: goedkoopst bij {nm(w[0])} ({MAAND})"
        desc = f"{len(arr)} producten {naam_.lower().replace('glutenvrij ', '').replace('glutenvrije ', '')} zonder gluten bij {n_w} supermarkten naast elkaar, op prijs per kilo. Nu het voordeligst: {w[1]} bij {nm(w[0])} voor {eur(eff(w))}. Elke dag bijgewerkt."
        ch, cld = crumbs(("Glutenvrij", "/glutenvrij/"), (naam_, None))
        head = ch + f'<h1>{ic} {esc(naam_)}: waar is het goedkoopst?</h1><p class="lead">{len(arr)} glutenvrije producten bij {n_w} supermarkten, van goedkoop naar duur op prijs per kilo of liter. Nu het voordeligst: <b>{esc(w[1])}</b> bij <b>{esc(nm(w[0]))}</b>.</p>'
        faq = [(f"Waar koop je {naam_.lower()} het goedkoopst?", f"Op {DATUM} is {w[1]} bij {nm(w[0])} het voordeligst: {eur(eff(w))}" + (f" ({_ut(w)})" if _ut(w) else "") + "."),
               (f"Welke supermarkten verkopen {naam_.lower()}?", ", ".join(nm(si) for si in sorted(best, key=lambda si: _gv_sort(best[si]))) + "."),
               ("Hoe weet ik zeker dat het glutenvrij is?", "We tonen producten met glutenvrij of gluten free in de productnaam. Controleer bij coeliakie altijd het etiket en het glutenvrij-logo (de doorgestreepte aar).")]
        body = (f'<h2>Goedkoopst per supermarkt</h2><div class="tblwrap"><table class="ptable"><tbody>' + "".join(_rij(p, naam_) for p in bestl) + "</tbody></table></div>"
                + (f'<h2>Alle {len(arr)} producten</h2><div class="tblwrap"><table class="ptable"><tbody>' + "".join(_rij(p, naam_) for p in arr[:80]) + "</tbody></table></div>" if len(arr) > len(bestl) else "")
                + f'<p class="note">Bijgewerkt op {DATUM}. Prijzen van de webshops; lopende aanbiedingen tellen mee. Controleer bij een allergie altijd het etiket.</p>'
                + '<h2>Meer glutenvrij</h2><ul class="links">' + "".join(f'<li><a href="/glutenvrij/{s2}/">{i2} {esc(n2)}</a></li>' for s2, n2, i2 in GV_LIJST if s2 != sl)
                + '<li><a href="/maaltijden/glutenvrij/">🍽️ Glutenvrije maaltijden met prijs per supermarkt</a></li></ul>' + faq_html(faq))
        schrijf(path, page(path, title, desc, head, body, [cld, faq_ld(faq)], og_title=f"{naam_}: goedkoopst bij {nm(w[0])}"))
        made.append((path, "0.7"))
    # Verzamelpagina
    blok = ""
    for sl, naam_, ic in GV_LIJST:
        arr = sorted(GV_PER[sl], key=_gv_sort); w = arr[0]
        blok += f'<li><a href="/glutenvrij/{sl}/"><b>{ic} {esc(naam_)}</b></a> <span class="sub">{len(arr)} producten bij {len({p[0] for p in arr})} supermarkten · voordeligst: {esc(w[1])} bij {esc(nm(w[0]))}, {eur(eff(w))}</span></li>'
    perwinkel = {}
    for sl, _, _ in GV_LIJST:
        for p in GV_PER[sl]: perwinkel[p[0]] = perwinkel.get(p[0], 0) + 1
    ww = sorted(perwinkel.items(), key=lambda kv: -kv[1])
    title = f"Glutenvrije boodschappen vergelijken: {totaal} producten bij {len(ww)} supermarkten"
    desc = f"Glutenvrij brood, pasta, crackers, koek en meer: {totaal} producten zonder gluten bij {len(ww)} supermarkten naast elkaar, op prijs per kilo. Zie waar je glutenvrij het goedkoopst koopt. Elke dag bijgewerkt."
    ch, cld = crumbs(("Glutenvrij", None))
    head = ch + f'<h1>🌾 Glutenvrije boodschappen: waar is het goedkoopst?</h1><p class="lead">{totaal} glutenvrije producten bij {len(ww)} supermarkten, per soort van goedkoop naar duur. Glutenvrij is vaak duur; hier zie je in één keer waar je het minst betaalt.</p>'
    faq = [("Welke supermarkt heeft de meeste glutenvrije producten?", f"Online vinden we nu de meeste glutenvrije producten bij {nm(ww[0][0])} ({ww[0][1]}), gevolgd door {nm(ww[1][0])} ({ww[1][1]})." if len(ww) > 1 else ""),
           ("Hoe komen jullie aan deze producten?", "We tonen alle producten met glutenvrij of gluten free in de productnaam uit de webshops van de supermarkten, elke dag bijgewerkt. Groente, fruit, vlees en vis zijn van nature glutenvrij en staan hier niet apart."),
           ("Is dit geschikt bij coeliakie?", "Gebruik het als prijsvergelijking. Controleer bij coeliakie altijd het etiket en het glutenvrij-logo (de doorgestreepte aar).")]
    faq = [f for f in faq if f[1]]
    body = (f'<ul class="links gvlijst">{blok}</ul><h2>Glutenvrij per supermarkt</h2><ul class="links">' + "".join(f"<li>{esc(nm(si))}: {n} producten</li>" for si, n in ww) + "</ul>"
            + '<h2>Glutenvrij koken</h2><p><a href="/maaltijden/weekmenu-glutenvrij/">📅 Glutenvrij weekmenu</a>: 5 avondmaaltijden zonder gluten, samen ingekocht, met boodschappenlijst.</p><p><a href="/maaltijden/glutenvrij/">Glutenvrije maaltijden met prijs per supermarkt</a>: gewone avondmaaltijden zonder pasta, brood of bloem, met de goedkoopste winkel voor alle ingrediënten. In de app kun je ook bij elke categorie op <b>🌾 Alleen glutenvrij</b> tikken.</p>'
            + faq_html(faq) + '<a class="cta" href="/">Vergelijk je hele boodschappenlijst</a>')
    schrijf("/glutenvrij/", page("/glutenvrij/", title, desc, head, body, [cld, faq_ld(faq)], og_title="Glutenvrije boodschappen: waar is het goedkoopst?"))
    made.append(("/glutenvrij/", "0.8"))
    print(len(GV_LIJST), "glutenvrij-pagina's,", totaal, "producten")

# ---------- Eiwitrijk: wat kost 10 gram eiwit? ----------
SPORT = {"protein kwark", "protein yoghurt", "protein pudding", "protein drink", "proteine drink", "protein bar", "proteine reep", "eiwitreep", "whey", "proteine brood"}
PLANT = {"tofu", "tempeh", "edamame", "linzen", "rode linzen", "kikkererwten", "kidneybonen", "bruine bonen", "witte bonen", "zwarte bonen", "pindakaas", "pinda's", "amandelen",
         "cashewnoten", "walnoten", "sojadrink", "havermout", "quinoa", "spliterwten", "vegetarisch gehakt", "volkoren brood"}
_eiw = []
for t, g in EIWIT.items():
    if t not in PICKED: continue
    si, p = PICKED[t][0]
    u = vgl_unit(p) or eff_unit(p)
    if not u or not p[6]: continue
    pkg = u if p[6] in ("kg", "l") else (u / .06 if t in ("eieren", "scharreleieren", "vrije uitloop eieren") and p[6] == "st" else None)
    if not pkg: continue
    _eiw.append((pkg / g, t, g, si, p))  # euro per 10 gram eiwit = prijs per kilo / gram eiwit per 100 g
_eiw.sort()
if len(_eiw) >= 10:
    def _er(rij, i):
        c, t, g, si, p = rij
        soort = "sport" if t in SPORT else "plant" if t in PLANT else "dier"
        return (f'<tr{" class=win" if i == 0 else ""}><td><a href="/vergelijk/{slug(t)}/"><b>{esc(cap(t))}</b></a> <span class="lbl {"eiw" if soort == "sport" else "arm" if soort == "plant" else "gv"}">{"💪 sport" if soort == "sport" else "🌱 plantaardig" if soort == "plant" else "🥩 dierlijk"}</span>'
                f'<span class="sub">{esc(p[1])} ({esc(nm(si))}) · {str(g).replace(".", ",")} g eiwit per 100 g</span></td><td class="p"><b>{eur(c)}</b><span class="sub">per 10 g eiwit</span></td></tr>')
    top = _eiw[0]; sport = [r for r in _eiw if r[1] in SPORT]; plant = [r for r in _eiw if r[1] in PLANT]
    ch, cld = crumbs(("Eiwitrijk", None))
    faq = [("Wat is de goedkoopste eiwitbron?", f"Op {DATUM} is {top[1]} het voordeligst: {eur(top[0])} per 10 gram eiwit, bij {nm(top[3])}."),
           ("Zijn proteïneproducten duurder dan gewone eiwitbronnen?", (f"Meestal wel. De goedkoopste proteïne-sportproduct hier is {sport[0][1]} met {eur(sport[0][0])} per 10 gram eiwit; gewone producten als " + ", ".join(r[1] for r in _eiw[:3]) + f" kosten {eur(_eiw[0][0])} tot {eur(_eiw[2][0])}.") if sport else "Gewone producten als kwark, eieren en kipfilet zijn meestal goedkoper per gram eiwit dan speciale proteïneproducten."),
           ("Hoeveel eiwit heb je nodig?", "Volgens de Gezondheidsraad hebben volwassenen ongeveer 0,8 gram eiwit per kilo lichaamsgewicht per dag nodig. Sporters die spieren willen opbouwen, gebruiken vaak 1,2 tot 1,6 gram per kilo. Uit gewone voeding is dat meestal goed te halen."),
           ("Wat betekent het label Eiwitrijk?", "Volgens de Europese regels mag een product 'rijk aan eiwitten' heten als minstens 20% van de calorieën uit eiwit komt. Dat label tonen we bij de producten op deze site.")]
    head = ch + f'<h1>💪 Goedkoopste eiwitten: wat kost 10 gram eiwit?</h1><p class="lead">Voor sporters en iedereen die op eiwit let: per product de prijs voor 10 gram eiwit, met de goedkoopste supermarkt. Nu het voordeligst: <b>{esc(top[1])}</b> voor {eur(top[0])} per 10 gram.</p>'
    body = (f'<div class="tblwrap"><table class="ptable"><thead><tr><th>Product</th><th style="text-align:right">Prijs</th></tr></thead><tbody>' + "".join(_er(r, i) for i, r in enumerate(_eiw)) + "</tbody></table></div>"
            + f'<p class="note">Berekend met de goedkoopste verpakking per product op {DATUM} en gemiddelde eiwitwaarden per 100 gram (richtwaarden; per merk iets anders, kijk op het etiket). Eieren gerekend met 60 gram per ei.</p>'
            + '<h2>Proteïneproducten vergelijken</h2><p>Proteïnekwark, -pudding, -drinks, -repen en whey per supermarkt: <a href="/categorie/proteine-en-sportvoeding/">bekijk de categorie Proteïne en sportvoeding</a>. In de app kun je bij elke categorie op <b>💪 Alleen eiwitrijk</b> tikken.</p>'
            + '<h2>Eiwitrijk koken</h2><p><a href="/maaltijden/weekmenu-eiwitrijk/">📅 Eiwitrijk weekmenu</a>: 5 avondmaaltijden met minstens 30 gram eiwit per persoon, samen ingekocht. Of bekijk alle <a href="/maaltijden/eiwitrijk/">eiwitrijke maaltijden met prijs per supermarkt</a>.</p>'
            + faq_html(faq) + '<a class="cta" href="/">Zet eiwitrijke producten op je lijst</a>')
    schrijf("/eiwitrijk/", page("/eiwitrijk/", f"Goedkoopste eiwitten: prijs per 10 gram eiwit ({MAAND})", f"Wat kost 10 gram eiwit? Kipfilet, kwark, eieren, tonijn, linzen, whey en proteïnerepen vergeleken bij 11 supermarkten. Nu het goedkoopst: {top[1]} voor {eur(top[0])} per 10 g.", head, body, [cld, faq_ld(faq)], og_title="Goedkoopste eiwitten: wat kost 10 gram eiwit?"))
    made.append(("/eiwitrijk/", "0.8"))
    print("/eiwitrijk/:", len(_eiw), "producten, goedkoopst", top[1], eur(top[0]))

# ---------- Lactosevrij: alle producten met lactosevrij in de naam, per soort ----------
LV_SOORTEN = [("melk", "Lactosevrije melk en drinks", "🥛", ["melk", "drink", "chocomel", "karnemelk", "koffiemelk", "optimel", "fristi"]),
              ("yoghurt", "Lactosevrije yoghurt, kwark en vla", "🥣", ["yoghurt", "kwark", "vla", "skyr", "pudding", "toetje", "dessert", "mousse"]),
              ("kaas", "Lactosevrije kaas", "🧀", ["kaas", "gouda", "mozzarella", "plakken", "roomkaas", "smeerkaas", "geraspt"]),
              ("boter", "Lactosevrije boter en room", "🧈", ["boter", "room", "slagroom", "kookroom", "creme", "crème"]),
              ("zoet", "Lactosevrije koek, chocolade en ijs", "🍫", ["koek", "chocolade", "reep", "ijs", "cake", "wafel", "biscuit", "cereal", "céréal", "hagelslag"])]
def _lv_soort(naam):
    n = naam.lower()
    for sl, _, _, ws in LV_SOORTEN:
        if any(w in n for w in ws): return sl
    return "overig"
LV_PER = {}
for p in prods:
    if stores[p[0]].get("count") and LV_RE.search(p[1]): LV_PER.setdefault(_lv_soort(p[1]), []).append(p)
_lv_n = sum(len(v) for v in LV_PER.values())
if _lv_n >= 20:
    ch, cld = crumbs(("Lactosevrij", None))
    blok = ""
    for sl, naam_, ic, _ in LV_SOORTEN + [("overig", "Overige lactosevrije producten", "🛒", [])]:
        arr = sorted(LV_PER.get(sl, []), key=_gv_sort)
        if not arr: continue
        best = {}
        for p in arr: best.setdefault(p[0], p)
        blok += (f'<h2>{ic} {esc(naam_)}</h2><div class="tblwrap"><table class="ptable"><tbody>'
                 + "".join(f'<tr><td><span class="shop">{esc(nm(p[0]))}</span> <a href="{esc(plink(p))}" rel="nofollow noopener" target="_blank" data-out="{stores[p[0]]["id"]}"><b>{esc(p[1])}</b></a><span class="sub">{esc(p[4] or "")}</span>{addbtn(p, naam_)}</td><td class="p">{tag(eff(p))}<span class="sub">{esc(_ut(p))}</span></td></tr>' for p in arr[:25])
                 + "</tbody></table></div>")
    winkels_lv = sorted({p[0] for v in LV_PER.values() for p in v})
    faq = [("Is lactosevrij hetzelfde als glutenvrij?", "Nee. Lactose is de suiker in melk; gluten is een eiwit uit tarwe, rogge en gerst. Lactosevrij is belangrijk bij lactose-intolerantie, glutenvrij bij coeliakie. Een product kan het een zijn zonder het ander."),
           ("Welke supermarkten verkopen lactosevrije producten?", ", ".join(nm(si) for si in winkels_lv) + ". Arla, Melkan en de huismerken hebben de meeste."),
           ("Zit er lactose in kaas?", "Harde, belegen en oude kaas bevatten van nature bijna geen lactose; veel mensen met lactose-intolerantie kunnen die gewoon eten. Bij zachte kaas, melk en yoghurt is lactosevrij wel handig.")]
    head = ch + f'<h1>🥛 Lactosevrije boodschappen: waar is het goedkoopst?</h1><p class="lead">{_lv_n} lactosevrije producten bij {len(winkels_lv)} supermarkten, per soort van goedkoop naar duur op prijs per kilo of liter.</p>'
    body = blok + f'<p class="note">Alle producten met lactosevrij in de naam, bijgewerkt op {DATUM}. Controleer bij een allergie altijd het etiket. In de app kun je bij elke categorie op <b>🥛 Alleen lactosevrij</b> tikken.</p>' + '<h2>Lactosevrij koken</h2><p><a href="/maaltijden/weekmenu-lactosevrij/">📅 Lactosevrij weekmenu</a> en alle <a href="/maaltijden/lactosevrij/">lactosevrije maaltijden met prijs per supermarkt</a>.</p>' + faq_html(faq) + '<p><a href="/glutenvrij/">Glutenvrije boodschappen vergelijken →</a></p>'
    schrijf("/lactosevrij/", page("/lactosevrij/", f"Lactosevrij vergelijken: {_lv_n} producten bij {len(winkels_lv)} supermarkten", f"Lactosevrije melk, yoghurt, kaas, boter en meer: {_lv_n} producten bij {len(winkels_lv)} supermarkten naast elkaar op prijs per liter of kilo. Elke dag bijgewerkt.", head, body, [cld, faq_ld(faq)]))
    made.append(("/lactosevrij/", "0.7"))
    print("/lactosevrij/:", _lv_n, "producten")

# ---------- Vegan: verzamelpagina en per soort een eigen pagina (zoals de gewone categorieën) ----------
if VG_LIJST:
    _vg_n = sum(len(VG_PER[sl]) for sl, _, _ in VG_LIJST)
    def _vrij(p, t):
        return (f'<tr><td><span class="shop">{esc(nm(p[0]))}</span> <a href="{esc(plink(p))}" rel="nofollow noopener" target="_blank" data-out="{stores[p[0]]["id"]}"><b>{esc(p[1])}</b></a>'
                f'<span class="sub">{esc(p[4] or "")}</span>{fout_knop(t, p[0], p)}{addbtn(p, t)}</td><td class="p">{tag(eff(p))}<span class="sub">{esc(_ut(p))}</span></td></tr>')
    _vg_maal = '<li><a href="/maaltijden/vegan/">🍽️ Vegan maaltijden met prijs per supermarkt</a></li>'
    for sl, naam_, ic in VG_LIJST:
        arr = sorted(VG_PER[sl], key=_gv_sort)
        best = {}
        for p in arr: best.setdefault(p[0], p)
        bestl = sorted(best.values(), key=_gv_sort); w = bestl[0]; n_w = len(best)
        path = f"/vegan/{sl}/"
        title = f"{naam_} vergelijken: goedkoopst bij {nm(w[0])} ({MAAND})"
        desc = f"{len(arr)} producten: {naam_.lower()} bij {n_w} supermarkten naast elkaar, op prijs per kilo of liter. Nu het voordeligst: {w[1]} bij {nm(w[0])} voor {eur(eff(w))}. Elke dag bijgewerkt."
        ch, cld = crumbs(("Vegan", "/vegan/"), (naam_, None))
        head = (ch + f'<h1>{ic} {esc(naam_)}: waar is het goedkoopst?</h1><p class="lead">{len(arr)} vegan producten bij {n_w} supermarkten, van goedkoop naar duur op prijs per kilo of liter. Nu het voordeligst: <b>{esc(w[1])}</b> bij <b>{esc(nm(w[0]))}</b>.</p>'
                + '<ul class="chips">' + "".join(f'<li><a href="/vegan/{s2}/"{" aria-current=\"page\"" if s2 == sl else ""}>{i2} {esc(n2)}</a></li>' for s2, n2, i2 in VG_LIJST) + '</ul>')
        faq = [(f"Waar koop je {naam_.lower()} het goedkoopst?", f"Op {DATUM} is {w[1]} bij {nm(w[0])} het voordeligst: {eur(eff(w))}" + (f" ({_ut(w)})" if _ut(w) else "") + "."),
               (f"Welke supermarkten verkopen {naam_.lower()}?", ", ".join(nm(si) for si in sorted(best, key=lambda si: _gv_sort(best[si]))) + "."),
               ("Hoe weten jullie dat het vegan is?", "We tonen producten met vegan of 100% plantaardig in de naam, plantaardige zuivel- en vleesvervangers, tofu, tempeh en seitan, en merken die alleen plantaardig maken (zoals Alpro, Oatly en Violife). Controleer bij twijfel altijd het etiket.")]
        body = (f'<h2>Goedkoopst per supermarkt</h2><div class="tblwrap"><table class="ptable"><tbody>' + "".join(_vrij(p, naam_) for p in bestl) + "</tbody></table></div>"
                + (f'<h2>Alle {len(arr)} producten</h2><div class="tblwrap"><table class="ptable"><tbody>' + "".join(_vrij(p, naam_) for p in arr[:100]) + "</tbody></table></div>" if len(arr) > len(bestl) else "")
                + f'<p class="note">Bijgewerkt op {DATUM}. Prijzen van de webshops; lopende aanbiedingen tellen mee.</p>'
                + '<h2>Meer vegan</h2><ul class="links">' + "".join(f'<li><a href="/vegan/{s2}/">{i2} {esc(n2)}</a></li>' for s2, n2, i2 in VG_LIJST if s2 != sl) + _vg_maal + '</ul>' + faq_html(faq))
        schrijf(path, page(path, title, desc, head, body, [cld, faq_ld(faq)], og_title=f"{naam_}: goedkoopst bij {nm(w[0])}"))
        made.append((path, "0.7"))
    blok = ""
    for sl, naam_, ic in VG_LIJST:
        arr = sorted(VG_PER[sl], key=_gv_sort); w = arr[0]
        blok += f'<li><a href="/vegan/{sl}/"><b>{ic} {esc(naam_)}</b></a> <span class="sub">{len(arr)} producten bij {len({p[0] for p in arr})} supermarkten · voordeligst: {esc(w[1])} bij {esc(nm(w[0]))}, {eur(eff(w))}</span></li>'
    perwinkel = {}
    for sl, _, _ in VG_LIJST:
        for p in VG_PER[sl]: perwinkel[p[0]] = perwinkel.get(p[0], 0) + 1
    ww = sorted(perwinkel.items(), key=lambda kv: -kv[1])
    ch, cld = crumbs(("Vegan", None))
    head = ch + f'<h1>🌱 Vegan boodschappen: waar is het goedkoopst?</h1><p class="lead">{_vg_n} vegan producten bij {len(ww)} supermarkten, ingedeeld in {len(VG_LIJST)} soorten zoals de gewone categorieën. Per soort zie je waar je het minst betaalt.</p>'
    faq = [("Welke supermarkt heeft de meeste vegan producten?", f"Online vinden we nu de meeste vegan producten bij {nm(ww[0][0])} ({ww[0][1]}), gevolgd door {nm(ww[1][0])} ({ww[1][1]})." if len(ww) > 1 else ""),
           ("Wat is het verschil tussen vegan en vegetarisch?", "Vegetarisch is zonder vlees en vis. Vegan is helemaal plantaardig: ook zonder melk, kaas, eieren en honing. Niet alle vegetarische vleesvervangers zijn vegan; sommige bevatten ei of melk."),
           ("Is vegan ook lactosevrij?", "Ja, vegan producten bevatten geen melk en dus geen lactose. Daarom staan ze ook op de pagina lactosevrij."),
           ("Hoe weten jullie dat het vegan is?", "We kijken naar de productnaam (vegan, 100% plantaardig, plantaardige drink of kaas, tofu, tempeh, seitan) en naar merken die alleen plantaardig maken. Controleer bij twijfel altijd het etiket.")]
    body = (f'<ul class="links">{blok}</ul>'
            + '<h2>Vegan koken</h2><p><a href="/maaltijden/weekmenu-vegan/">📅 Vegan weekmenu</a>: 5 plantaardige avondmaaltijden, samen ingekocht, met boodschappenlijst.</p><p><a href="/maaltijden/vegan/">🍽️ Vegan maaltijden met prijs per supermarkt</a>: complete avondmaaltijden zonder vlees, vis, zuivel en ei, met de goedkoopste winkel voor alle ingrediënten. In de app kun je bij elke categorie ook op <b>🌱 Alleen vegan</b> tikken.</p>'
            + f'<p class="note">Bijgewerkt op {DATUM}.</p>' + faq_html(faq) + '<p><a href="/lactosevrij/">Lactosevrij</a> · <a href="/glutenvrij/">Glutenvrij</a> · <a href="/eiwitrijk/">Eiwitrijk</a></p>')
    schrijf("/vegan/", page("/vegan/", f"Vegan boodschappen vergelijken: {_vg_n} producten bij {len(ww)} supermarkten", f"Plantaardige melk, vegan kaas, vleesvervangers, tofu en meer: {_vg_n} vegan producten bij {len(ww)} supermarkten naast elkaar op prijs per kilo of liter. Elke dag bijgewerkt.", head, body, [cld, faq_ld(faq)], og_title="Vegan boodschappen: waar is het goedkoopst?"))
    made.append(("/vegan/", "0.8"))
    print("/vegan/:", _vg_n, "producten in", len(VG_LIJST), "soorten:", {sl: len(VG_PER[sl]) for sl, _, _ in VG_LIJST})

# ---------- Halal en koosjer: producten, maaltijden en feestdagen ----------
HL_SOORTEN = [("vlees", "Halal kip en vlees", "🍗", ["kip", "vlees", "gehakt", "kalkoen", "merguez", "burger", "rund", "shoarma", "kebab", "tenders", "filet", "drumstick", "worst", "lams", "schnitzel", "nugget", "gyros"]),
              ("beleg", "Halal vleeswaren en spreads", "🥪", ["spread", "beleg", "plakjes", "rookvlees", "salami", "vleeswaren", "ham", "pastrami", "cervelaat"]),
              ("overig", "Overige halal producten", "🛒", [])]
HL_PER = {}
for p in prods:
    if not stores[p[0]].get("count") or not HALAL_RE.search(p[1]): continue
    n = p[1].lower(); sl = next((sl for sl, _, _, ws in HL_SOORTEN if ws and any(w in n for w in ws)), "overig")
    HL_PER.setdefault(sl, []).append(p)
_hl_n = sum(len(v) for v in HL_PER.values())
if _hl_n >= 5:
    _hl_lijst = [(sl, nm_, ic) for sl, nm_, ic, _ in HL_SOORTEN if HL_PER.get(sl)]
    # Per soort een eigen pagina, net als bij de gewone categorieën, vegan en glutenvrij.
    for sl, naam_, ic in _hl_lijst:
        arr = sorted(HL_PER[sl], key=_gv_sort)
        best = {}
        for p in arr: best.setdefault(p[0], p)
        bestl = sorted(best.values(), key=_gv_sort); w = bestl[0]
        path = f"/halal/{sl}/"
        ch, cld = crumbs(("Halal", "/halal/"), (naam_, None))
        head = (ch + f'<h1>{ic} {esc(naam_)}: waar is het goedkoopst?</h1><p class="lead">{len(arr)} halal producten bij {len(best)} supermarkten, van goedkoop naar duur op prijs per kilo. Nu het voordeligst: <b>{esc(w[1])}</b> bij <b>{esc(nm(w[0]))}</b>.</p>'
                + '<ul class="chips">' + "".join(f'<li><a href="/halal/{s2}/"{" aria-current=\"page\"" if s2 == sl else ""}>{i2} {esc(n2)}</a></li>' for s2, n2, i2 in _hl_lijst) + '</ul>')
        faq = [(f"Waar koop je {naam_.lower()} het goedkoopst?", f"Op {DATUM} is {w[1]} bij {nm(w[0])} het voordeligst: {eur(eff(w))}" + (f" ({_ut(w)})" if _ut(w) else "") + "."),
               ("Hoe weten jullie dat het halal is?", "We tonen producten met halal in de productnaam. Kijk voor zekerheid naar het halal-keurmerk op de verpakking.")]
        body = (f'<div class="tblwrap"><table class="ptable"><tbody>' + "".join(_vrij(p, naam_) for p in arr) + "</tbody></table></div>"
                + f'<p class="note">Bijgewerkt op {DATUM}. Controleer altijd het keurmerk op de verpakking.</p>'
                + '<h2>Meer halal</h2><ul class="links">' + "".join(f'<li><a href="/halal/{s2}/">{i2} {esc(n2)}</a></li>' for s2, n2, i2 in _hl_lijst if s2 != sl)
                + '<li><a href="/maaltijden/halal/">Halal maaltijden met prijs per supermarkt</a></li><li><a href="/maaltijden/weekmenu-halal/">📅 Halal weekmenu</a></li></ul>' + faq_html(faq))
        schrijf(path, page(path, f"{naam_} vergelijken: goedkoopst bij {nm(w[0])} ({MAAND})", f"{len(arr)} producten: {naam_.lower()} bij {len(best)} supermarkten naast elkaar, op prijs per kilo. Nu het voordeligst: {w[1]} bij {nm(w[0])} voor {eur(eff(w))}.", head, body, [cld, faq_ld(faq)]))
        made.append((path, "0.6"))
    blok = '<ul class="links">' + "".join(f'<li><a href="/halal/{sl}/"><b>{ic} {esc(naam_)}</b></a> <span class="sub">{len(HL_PER[sl])} producten bij {len({p[0] for p in HL_PER[sl]})} supermarkten · voordeligst: {esc(min(HL_PER[sl], key=_gv_sort)[1])} bij {esc(nm(min(HL_PER[sl], key=_gv_sort)[0]))}, {eur(eff(min(HL_PER[sl], key=_gv_sort)))}</span></li>' for sl, naam_, ic in _hl_lijst) + '</ul>'
    _hlw = sorted({p[0] for v in HL_PER.values() for p in v})
    ch, cld = crumbs(("Halal", None))
    faq = [("Welke supermarkten verkopen halal vlees?", ", ".join(nm(si) for si in _hlw) + ". Het meeste halal vlees is van het merk Wahid of het eigen halal-assortiment van de supermarkt."),
           ("Hoe weten jullie dat het halal is?", "We tonen producten met halal in de productnaam. Kijk voor zekerheid naar het halal-keurmerk op de verpakking."),
           ("Is vegetarisch eten altijd halal?", "Producten zonder vlees zijn meestal geschikt, maar let op gelatine (in snoep en toetjes), alcohol (in sommige sauzen en desserts) en E-nummers van dierlijke oorsprong. Vegan producten bevatten geen gelatine.")]
    head = ch + f'<h1>Halal boodschappen: waar is het goedkoopst?</h1><p class="lead">{_hl_n} halal producten bij {len(_hlw)} supermarkten naast elkaar, met de prijs per kilo. Plus halal maaltijden en een halal weekmenu met boodschappenlijst.</p>'
    body = (blok + '<h2>Halal koken</h2><ul class="links"><li><a href="/maaltijden/halal/">Halal maaltijden met prijs per supermarkt</a>: zonder varkensvlees en alcohol</li><li><a href="/maaltijden/weekmenu-halal/">📅 Halal weekmenu met boodschappenlijst</a></li><li><a href="/ramadan/">🌙 Ramadan en Suikerfeest: iftar-boodschappen vergelijken</a></li><li><a href="/vegan/">🌱 Vegan producten</a> (zonder vlees en gelatine)</li></ul>'
            + f'<p class="note">Producten met halal in de naam, bijgewerkt op {DATUM}. Controleer altijd het keurmerk op de verpakking.</p>' + faq_html(faq))
    schrijf("/halal/", page("/halal/", f"Halal boodschappen vergelijken: {_hl_n} producten bij {len(_hlw)} supermarkten", f"Halal kip, gehakt, vleeswaren en meer bij {len(_hlw)} supermarkten naast elkaar op prijs per kilo. Met halal maaltijden en een halal weekmenu. Elke dag bijgewerkt.", head, body, [cld, faq_ld(faq)]))
    made.append(("/halal/", "0.7"))
    print("/halal/:", _hl_n, "producten")
# Koosjer: supermarkten zetten het hechsjer zelden online; daarom eerlijke uitleg, matzes en koosjere maaltijden.
_mz = sorted([p for p in prods if stores[p[0]].get("count") and re.search(r"\bmatze|matzes", p[1], re.I)], key=_gv_sort)
ch, cld = crumbs(("Koosjer", None))
faq = [("Kun je koosjer kopen in de supermarkt?", "Ja, maar supermarkten zetten het hechsjer (koosjer-keurmerk) bijna nooit in hun webshop. Veel gewone producten hebben wel een hechsjer op de verpakking; de lijsten daarvan worden bijgehouden door het Nederlands-Israëlitisch Kerkgenootschap (NIK). Koosjer vlees koop je bij een koosjere slager."),
       ("Wat betekent koosjer koken?", "Geen varkensvlees, schaaldieren of andere niet-koosjere dieren, vlees en zuivel niet samen in één maaltijd, en vlees dat koosjer geslacht is. Vis met schubben en vinnen, groente, fruit, eieren en granen zijn neutraal (parve)."),
       ("Hoe zijn de koosjere maaltijden gekozen?", "Het zijn recepten zonder varkensvlees, zonder schaaldieren en zonder vlees samen met zuivel. Kies voor vlees en bewerkte producten een variant met hechsjer.")]
head = ch + '<h1>Koosjer boodschappen en maaltijden</h1><p class="lead">Koosjer koken met boodschappen uit de supermarkt: maaltijden zonder varkensvlees en zonder vlees met zuivel, matzes voor Pesach en de prijzen per supermarkt.</p>'
body = ('<div class="panel"><p style="margin:0">Eerlijk is eerlijk: supermarkten zetten het koosjer-keurmerk (hechsjer) bijna nooit online. Wij kunnen dus geen product als koosjer markeren. Wel tonen we maaltijden die bij de koosjere regels passen, en producten die je voor de Joodse feestdagen nodig hebt.</p></div>'
        + '<h2>Koosjer koken</h2><ul class="links"><li><a href="/maaltijden/koosjer/">Koosjere maaltijden met prijs per supermarkt</a></li><li><a href="/maaltijden/weekmenu-koosjer/">📅 Koosjer weekmenu met boodschappenlijst</a></li><li><a href="/chanoeka/">🕎 Chanoeka</a> · <a href="/pesach/">Pesach</a></li></ul>'
        + (f'<h2>Matzes per supermarkt</h2><div class="tblwrap"><table class="ptable"><tbody>' + "".join(f'<tr><td><span class="shop">{esc(nm(p[0]))}</span> <a href="{esc(plink(p))}" rel="nofollow noopener" target="_blank" data-out="{stores[p[0]]["id"]}"><b>{esc(p[1])}</b></a><span class="sub">{esc(p[4] or "")}</span>{addbtn(p, "matzes")}</td><td class="p">{tag(eff(p))}<span class="sub">{esc(_ut(p))}</span></td></tr>' for p in _mz[:20]) + '</tbody></table></div><p class="note">Voor Pesach heb je matzes nodig die koosjer voor Pesach zijn; kijk op de verpakking.</p>' if _mz else "")
        + faq_html(faq))
schrijf("/koosjer/", page("/koosjer/", "Koosjer boodschappen: maaltijden, matzes en prijzen per supermarkt", "Koosjer koken met supermarktboodschappen: maaltijden zonder varkensvlees en zonder vlees met zuivel, matzes voor Pesach en de prijzen bij 11 supermarkten.", head, body, [cld, faq_ld(faq)]))
made.append(("/koosjer/", "0.6"))

# ---------- Aanbiedingen per product: "krat bier aanbieding", "gehakt aanbieding" ----------
AANB_PRODUCT = [  # (slug, naam, zoekpatroon in de actienaam, uitsluiten, vaste soorten om te vergelijken)
    ("krat-bier", "Krat bier", r"\bkrat\b|24 ?x ?30 ?cl|24 flesjes", r"alcoholvrij|0[.,]0|radler", ["pils krat 24 flesjes", "pils blikjes 33 cl tray 24", "pils blikken 50 cl tray 24"]),
    ("pils", "Bier", r"\bpils|\bbier\b|heineken|grolsch|hertog jan|amstel|bavaria|jupiler|brand\b", r"alcoholvrij|0[.,]0|radler|krat|glas|kaas", ["pils flesjes 6 pack", "pils blikjes 33 cl tray 24", "pils krat 24 flesjes"]),
    ("gehakt", "Gehakt", r"gehakt", r"vega|plantaardig|balletjes|gehaktbal|roasted|rode biet|kruim|soep|saus|pizza|lasagne|ovenschotel|burger|slavink|frikandel|kroket|nasi|bami|maaltijd", ["gehakt", "rundergehakt", "kipgehakt"]),
    ("kipfilet", "Kipfilet", r"kipfilet|kipdij", r"vega|beleg|plakjes|gerookt|salade|soep|wrap|kat|hond|krokant|schnitzel|burger|nugget|cordon|gepaneerd|spies|saté|sate", ["kipfilet", "kipdijfilet", "kipfiletblokjes"]),
    ("koffie", "Koffie", r"koffie|douwe egberts|nespresso|senseo|dolce gusto|lavazza|jacobs|cups|pads|bonen", r"koffiemelk|koffiecreamer|ijskoffie|koek|chocolade|zetapparaat|machine|filters?\b|ontkalker", ["koffiebonen", "filterkoffie", "koffiepads", "koffiecups"]),
    ("wasmiddel", "Wasmiddel", r"wasmiddel|waspoeder|wascapsules|caps\b|pods|ariel|persil|omo|robijn|dreft", r"afwas|vaatwas|hand|wasverzachter|wasparfum|parfum|droogtrommel|doekjes|vlekverwijderaar|spray|reiniger|toilet|kalk", ["wasmiddel vloeibaar", "waspoeder", "wascapsules", "wasmiddel"]),
    ("luiers", "Luiers", r"luier|pampers|huggies|billendoekjes", r"zalf|crème|creme|tas|wasverzachter", ["luiers", "billendoekjes"]),
    ("cola", "Cola en frisdrank", r"\bcola\b|coca|pepsi|fanta|sprite|7up|frisdrank|\bsinas\b|fernandes|ice tea|lipton", r"cola ?kaas|snoep|drop|zuurtjes|gum|chips|cookie|bakery|water|kies & mix|kies en mix|vla\b|ijs\b|yoghurt|dubbelfris|chocolade", ["coca-cola", "cola", "fanta", "sinas", "ice tea"]),
    ("toiletpapier", "Toiletpapier", r"toiletpapier|wc-?papier|keukenpapier|edet|page\b|lotus", r"reiniger|blok|eend|houder", ["toiletpapier", "keukenpapier"]),
    ("kaas", "Kaas", r"\bkaas\b|belegen|jong belegen|gouda|leerdammer|old amsterdam|beemster|milner|parrano", r"kaasstengels|kaasbroodje|chips|saus|stengels|croissant|soep|pizza|salade|snack|soufflé|souffle|kroket|tosti", ["jong belegen kaas", "belegen kaas", "oude kaas", "geraspte kaas"]),
    ("eieren", "Eieren", r"\beieren\b|scharrelei|vrije uitloop", r"chocolade|paas|salade|gekookt|gevuld|noedel|spread", ["eieren", "scharreleieren"]),
    ("chips", "Chips", r"chips|lay'?s|pringles|doritos|croky|smiths|hamka", r"stokbrood|chocolade", ["chips naturel", "chips paprika", "chips"]),
    ("wijn", "Wijn", r"\bwijn\b|rode wijn|witte wijn|rosé|merlot|chardonnay|sauvignon|cabernet|prosecco|cava", r"azijn|saus|glas|kurk", ["rode wijn", "witte wijn", "rosé"]),
    ("boter", "Boter en margarine", r"roomboter|boter\b|margarine|blue band|becel|halvarine|bak en braad", r"pinda|koek|cake|croissant|ham|sprits|speculaas|taart|brood", ["roomboter", "margarine", "halvarine"]),
    ("coca-cola", "Coca-Cola", r"coca-?cola", r"chips|snoep|gum", ["coca-cola", "coca-cola zero"], True),
    ("pepsi-max", "Pepsi Max", r"pepsi", r"chips|snoep", ["pepsi max"], True),
    ("red-bull", "Red Bull", r"red ?bull", r"", ["red bull"], True),
    ("ben-jerrys", "Ben & Jerry's", r"ben ?(&|en|and) ?jerry", r"", [], True),
    ("ijs", "IJs", r"\bijs\b|magnum|cornetto|ben ?(&|en) ?jerry|haagen|häagen|carte d'or|\bola\b", r"ijsberg|ijsthee|ice ?tea|ijsklont|ijskoffie|ijsblok|ijzer", ["roomijs", "ijs"], True),
    ("hertog-jan", "Hertog Jan", r"hertog jan", r"alcoholvrij|0[.,]0", [], True),
    ("heineken", "Heineken", r"heineken", r"alcoholvrij|0[.,]0", [], True),
    ("dolce-gusto", "Dolce Gusto", r"dolce gusto", r"machine|apparaat", [], True),
    ("koffiecups", "Koffiecups (Nespresso)", r"nespresso|koffiecups|capsules|l'or espresso", r"machine|apparaat|dolce gusto", ["koffiecups"], True),
    ("douwe-egberts", "Douwe Egberts", r"douwe egberts", r"machine|apparaat", [], True),
    ("mosselen", "Mosselen", r"mossel", r"saus|kruiden", ["mosselen"], True),
    ("pizza", "Pizza", r"pizza", r"saus|kruiden|deeg|bodem|snijder|steen|chips|tomaten", ["pizza"], True),
    ("pampers", "Pampers", r"pampers", r"", ["luiers"], True),
    ("ariel", "Ariel", r"\bariel\b", r"", ["wasmiddel"], True),
    ("lays", "Lay's chips", r"lay'?s\b", r"", ["chips naturel"], True),
]
def _o_unit(o):
    return o.get("pp") if o.get("pp") else None
_wk = datetime.date.fromisoformat(VANDAAG).isocalendar()[1]
AP_LIJST = []
for sl, naam_, pat, uit, termen, *merk in AANB_PRODUCT:
    rx, rxu = re.compile(pat, re.I), re.compile(uit, re.I)
    acts = [o for o in OFFERS if rx.search(o["n"]) and not rxu.search(o["n"])]
    ts = [t for t in termen if t in PICKED]
    if len(acts) < 3 and not ts and not merk: continue
    nu_ = [o for o in acts if not o.get("v") or o["v"] <= VANDAAG]; straks = [o for o in acts if o.get("v") and o["v"] > VANDAAG]
    met_eh = [o for o in nu_ if _o_unit(o)]
    nu_.sort(key=lambda o: (_o_unit(o) if _o_unit(o) else 1e9, o["p"]))
    winkels_ = sorted({o["s"] for o in nu_}, key=lambda w: NAMEN.get(w, w))
    path = f"/aanbieding/{sl}/"
    goed = nu_[0] if nu_ else None
    title = f"{naam_} aanbieding week {_wk}: " + (f"{len(nu_)} acties, goedkoopst bij {NAMEN.get(goed['s'], goed['s'])}" if goed else "prijzen per supermarkt")
    if not nu_:
        desc = (f"Is {naam_} deze week in de aanbieding? Nu is er geen {naam_.lower()}-actie" + (f"; vanaf {kortdag(straks[0]['v'])} wel bij {NAMEN.get(straks[0]['s'], straks[0]['s'])}" if straks else "")
                + f". Bekijk de gewone prijzen per supermarkt en zie meteen wanneer er een nieuwe aanbieding is. Elke dag bijgewerkt.")
    else: desc = (f"Alle {len(nu_)} {naam_.lower()}-aanbiedingen van {', '.join(NAMEN.get(w, w) for w in winkels_)} naast elkaar" + (f", op prijs per {'liter' if goed and goed.get('eh') == 'l' else 'kilo'}" if met_eh else "")
            + (f". Nu het voordeligst: {goed['n'][:60]} voor {eur(goed['p'])}" if goed else "") + ". Elke dag bijgewerkt.")
    ch, cld = crumbs(("Aanbiedingen", "/aanbiedingen/"), (f"{naam_} aanbieding", None))
    head = ch + (f'<h1>{esc(naam_)} aanbieding deze week</h1><p class="lead">Week {_wk}: <b>{len(nu_)}</b> acties bij {len(winkels_)} supermarkten'
                 + (f", de voordeligste per {'liter' if goed and goed.get('eh') == 'l' else 'kilo'} eerst" if met_eh else ", de goedkoopste eerst") + ". Elke dag bijgewerkt met de nieuwe acties.</p>")
    faq = []
    if goed: faq.append((f"Waar is {naam_.lower()} deze week in de aanbieding?", f"In week {_wk} hebben {', '.join(NAMEN.get(w, w) for w in winkels_)} {naam_.lower()} in de aanbieding. Het voordeligst is nu {goed['n']} bij {NAMEN.get(goed['s'], goed['s'])} voor {eur(goed['p'])}" + (f" ({goed['lbl']})" if goed.get('lbl') else "") + "."))
    if ts:
        top_, n_ = winnaar(ts)
        faq.append((f"Waar is {naam_.lower()} zonder aanbieding het goedkoopst?", f"Zonder actie is {nm(top_)} bij {n_} van de {len(ts)} vergeleken soorten het goedkoopst. Zie de tabel op deze pagina."))
    faq.append(("Hoe vaak wordt dit bijgewerkt?", "Elke ochtend, met de acties van de webshops en folders van de supermarkten. De meeste weekacties lopen van maandag of woensdag tot en met zondag of dinsdag."))
    body = ((f'<h2>Aanbiedingen deze week</h2><ul class="offers" id="grid">' + "".join(offer_card(o) for o in nu_[:60]) + "</ul>" if nu_ else '<p class="note">Op dit moment zijn er geen acties. Hieronder de vaste prijzen.</p>')
            + (f'<h2>Binnenkort in de aanbieding</h2><ul class="offers">' + "".join(offer_card(o) for o in straks[:20]) + "</ul>" if straks else "")
            + (f'<h2>Vaste prijzen: waar is {esc(naam_.lower())} altijd het goedkoopst?</h2>{cat_tabel(ts)}' if ts else "")
            + '<h2>Meer aanbiedingen per product en merk</h2><ul class="links">' + "".join(f'<li><a href="/aanbieding/{s2}/">{esc(n2)} aanbieding</a></li>' for s2, n2, *_ in AANB_PRODUCT if s2 != sl)
            + '<li><a href="/aanbiedingen/">Alle aanbiedingen van deze week</a></li></ul>' + faq_html(faq))
    schrijf(path, page(path, title, desc, head, body, [cld, faq_ld(faq)], actief="/aanbiedingen/", og_title=f"{naam_} aanbieding week {_wk}"))
    made.append((path, "0.8")); AP_LIJST.append((sl, naam_, len(nu_)))
print(len(AP_LIJST), "aanbieding-per-productpagina's:", ", ".join(f"{a} ({c})" for a, _, c in AP_LIJST))

# ---------- Besparen op boodschappen: tips onderbouwd met de prijzen van vandaag ----------
_AM = (set(AMERK) | {"calvé", "calve", "jif", "skippy", "venz", "de ruijter", "douwe", "lavazza", "coca-cola", "coca", "pepsi", "fanta", "hellmann's", "hellmanns", "heinz", "remia",
       "zaanse", "campina", "arla", "melkunie", "lurpak", "président", "lay's", "lays", "croky", "pringles", "ariel", "omo", "robijn", "dreft", "persil", "unox", "honig", "knorr",
       "conimex", "barilla", "hero", "optimel", "danone", "becel", "blue", "lipton", "pickwick", "page", "edet", "verkade", "lu", "mutti", "bertolli", "grand'italia", "lassie", "jacobs", "senseo", "nescafé", "nescafe"}) - HUISMERK_W
def _unit(p):
    v = vgl_unit(p); return v if v else None
_huis_vb = []
for t in ["pindakaas", "hagelslag", "koffiebonen", "filterkoffie", "chips naturel", "toiletpapier", "mayonaise", "ketchup", "jam", "appelsap", "spaghetti", "macaroni",
          "tomatenpuree", "halfvolle melk", "vla", "cornflakes", "appelmoes", "wasmiddel vloeibaar", "keukenpapier", "frituursaus"]:
    if t not in PICKED: continue
    goed = [p for p in matches(t) if id(p) not in BAD and _unit(p) and not re.search(r"loempia|rozenbottel|met |minder zoet|light|zero|halfvol|0%|bio|lactosevrij|zoetzuur|dille|nacho", p[1].lower())]
    if len(goed) >= 4:
        _md = statistics.median(_unit(p) for p in goed); goed = [p for p in goed if _md / 3 <= _unit(p) <= _md * 3]
    huis = [p for p in goed if eerste_woord(p[1]) in HUISMERK_W]
    am = [p for p in goed if eerste_woord(p[1]) in _AM]
    if not huis or not am: continue
    h, a_ = min(huis, key=_unit), min(am, key=_unit)
    if _unit(a_) <= 0: continue
    pct = 1 - _unit(h) / _unit(a_)
    if 0.05 <= pct <= 0.85 and h[6] == a_[6]: _huis_vb.append((t, h, a_, pct))
_huis_vb = sorted({v[0]: v for v in _huis_vb}.values(), key=lambda v: -v[3])
if PAK and _huis_vb:
    w, l = PAK[0], PAK[-1]
    med = statistics.median(v[3] for v in _huis_vb)
    acts_nu = [o for o in NU_GELDIG if o.get("pct")]
    gem_k = statistics.mean(o["pct"] for o in acts_nu) if acts_nu else 0
    wm = WEEKMENU_PRIJS.get("weekmenu")
    tips = [
        ("Kies de goedkoopste supermarkt", f"Een vast mandje van {len(PAKTERMEN)} basisboodschappen kost nu {eur(w['tot'])} bij {nm(w['si'])} en {eur(l['tot'])} bij {nm(l['si'])}: {eur(l['tot'] - w['tot'])} verschil voor precies dezelfde boodschappen. Doe je elke week zo'n mandje, dan scheelt dat ruim {eur((l['tot'] - w['tot']) * 52)} per jaar.", "/goedkoopste-supermarkt/", "Bekijk de ranglijst"),
        ("Neem het huismerk", f"Bij {len(_huis_vb)} gewone boodschappen vergeleken we het goedkoopste huismerk met het goedkoopste A-merk, per kilo of liter. Het huismerk is gemiddeld {round(med * 100)}% goedkoper. De grootste verschillen staan in de tabel hieronder.", None, None),
        ("Vergelijk op prijs per kilo of liter", "Een grotere verpakking is vaak goedkoper per kilo, maar niet altijd; en een actie met 'tweede halve prijs' is soms duurder dan het huismerk zonder actie. Kijk daarom naar de prijs per kilo of liter: die staat op deze site bij elk product.", "/vergelijk/", "Alle producten vergelijken"),
        ("Gebruik de aanbiedingen, maar slim", f"Deze week lopen er {len(acts_nu)} acties met gemiddeld {round(gem_k * 100)}% korting. Koop vooral dingen die je toch al nodig hebt en lang houdbaar zijn, zoals koffie, wasmiddel en toiletpapier.", "/aanbiedingen/", "Aanbiedingen van deze week"),
        ("Plan je maaltijden", (f"Met een weekmenu koop je alleen wat je nodig hebt en gooi je minder weg. Ons goedkope weekmenu: 5 avondmaaltijden voor 4 personen voor {eur(wm[0])} bij {nm(wm[1])}, dat is {eur(wm[0] / 20)} per persoon per maaltijd." if wm else "Met een weekmenu koop je alleen wat je nodig hebt en gooi je minder weg."), "/maaltijden/weekmenu/", "Bekijk het weekmenu"),
        ("Maak een boodschappenlijst", "Met een lijst koop je minder op impuls. Zet hem op deze site en je ziet meteen bij welke supermarkt je hele lijst het goedkoopst is, en of het loont om een deel ergens anders te halen.", "/", "Maak je lijst"),
        ("Zet een prijsalarm", "Koop je vaak hetzelfde, zoals koffiebonen of luiers? Zet een prijsalarm en krijg een mail als de prijs per kilo onder jouw grens komt.", "/", "Zoek een product"),
        ("Kook met goedkope basis", "Aardappelen, rijst, pasta, linzen en bonen zijn per portie veel goedkoper dan vlees. Een paar keer per week vegetarisch of met minder vlees scheelt snel een paar euro.", "/maaltijden/goedkoop-avondeten/", "De 10 goedkoopste maaltijden"),
    ]
    tiphtml = "".join(f'<h2>{i + 1}. {esc(t)}</h2><p>{esc(x)}</p>' + (f'<p><a href="{h}">{esc(lt)} →</a></p>' if h else "") + ("HUISTABEL" if i == 1 else "") for i, (t, x, h, lt) in enumerate(tips))
    tab = ('<div class="tblwrap"><table class="ptable"><thead><tr><th>Product</th><th>Huismerk</th><th>A-merk</th><th style="text-align:right">Scheelt</th></tr></thead><tbody>'
           + "".join(f'<tr><td><a href="/vergelijk/{slug(t)}/">{esc(cap(t))}</a></td><td>{esc(h[1])}<span class="sub">{esc(nm(h[0]))} · {eur(_unit(h))} per {"liter" if h[6] == "l" else "kilo" if h[6] == "kg" else "stuk"}</span></td><td>{esc(a_[1])}<span class="sub">{esc(nm(a_[0]))} · {eur(_unit(a_))}</span></td><td class="p"><b>{round(pct * 100)}%</b></td></tr>' for t, h, a_, pct in _huis_vb[:15])
           + "</tbody></table></div>")
    tiphtml = tiphtml.replace("HUISTABEL", tab)
    faq = [("Hoeveel bespaar je met huismerken?", f"Bij de producten die we vergeleken is het goedkoopste huismerk gemiddeld {round(med * 100)}% goedkoper dan het goedkoopste A-merk, per kilo of liter ({DATUM})."),
           ("Welke supermarkt is het goedkoopst?", f"Op {DATUM} is {nm(w['si'])} het goedkoopst voor een vast mandje basisboodschappen: {eur(w['tot'])}, tegen {eur(l['tot'])} bij {nm(l['si'])}."),
           ("Hoe bespaar je het meest op boodschappen?", "Kies een goedkope supermarkt, neem huismerken, vergelijk op prijs per kilo, plan je maaltijden en koop aanbiedingen alleen als je ze toch nodig hebt. Samen scheelt dat al snel tientallen euro's per maand.")]
    ch, cld = crumbs(("Besparen op boodschappen", None))
    title = f"Besparen op boodschappen: 8 tips met echte prijzen ({MAAND})"
    desc = f"Hoe bespaar je op boodschappen? Huismerken zijn nu gemiddeld {round(med * 100)}% goedkoper en {nm(w['si'])} scheelt {eur(l['tot'] - w['tot'])} per mandje met {nm(l['si'])}. 8 tips, onderbouwd met de prijzen van vandaag."
    head = ch + f'<h1>Besparen op boodschappen: 8 tips met echte prijzen</h1><p class="lead">Geen algemene tips, maar wat het vandaag écht scheelt, uitgerekend met de prijzen van {len([s_ for s_ in stores if s_.get("count")])} supermarkten. Bijgewerkt op {DATUM}.</p>'
    body = tiphtml + '<h2>Meer weten</h2><ul class="links"><li><a href="/eten-voor-50-euro-per-week/">Eten voor 50 euro per week</a></li><li><a href="/studentenboodschappen/">Studentenboodschappen</a></li><li><a href="/prijsrapport/">Prijsrapport van deze maand</a></li><li><a href="/huismerk-of-a-merk/">Huismerk of A-merk: per product vergeleken</a></li><li><a href="/boodschappen-per-week/">Wat kosten boodschappen per week?</a></li><li><a href="/prijsindex/">Worden boodschappen duurder? De prijsindex</a></li></ul>' + faq_html(faq) + '<a class="cta" href="/">Bereken het voor je eigen lijst</a>'
    schrijf("/besparen/", page("/besparen/", title, desc, head, body, [cld, faq_ld(faq)], og_title="Besparen op boodschappen: 8 tips met echte prijzen"))
    made.append(("/besparen/", "0.9"))
    print("/besparen/:", len(_huis_vb), "huismerkvergelijkingen, mediaan", round(med * 100), "%")

# ---------- Huismerk of A-merk ----------
if _huis_vb:
    med = statistics.median(v[3] for v in _huis_vb)
    ch, cld = crumbs(("Besparen", "/besparen/"), ("Huismerk of A-merk", None))
    rij = "".join(f'<tr><td><a href="/vergelijk/{slug(t)}/"><b>{esc(cap(t))}</b></a><span class="sub">Huismerk: {esc(h[1])} ({esc(nm(h[0]))}), {eur(_unit(h))} per {"liter" if h[6] == "l" else "kilo" if h[6] == "kg" else "stuk"}</span><span class="sub">A-merk: {esc(a_[1])} ({esc(nm(a_[0]))}), {eur(_unit(a_))}</span></td><td class="p"><b>{round(pct * 100)}%</b><span class="sub">goedkoper</span></td></tr>' for t, h, a_, pct in _huis_vb)
    faq = [("Is een huismerk goedkoper dan een A-merk?", f"Ja, bijna altijd. Bij de {len(_huis_vb)} producten die we vandaag vergeleken is het goedkoopste huismerk gemiddeld {round(med * 100)}% goedkoper dan het goedkoopste A-merk, per kilo of liter."),
           ("Is een huismerk slechter?", "Niet per se. Huismerken worden vaak in dezelfde fabrieken gemaakt, en de Consumentenbond vindt huismerken in tests regelmatig even goed of beter. Smaak en samenstelling verschillen per product; probeer het gewoon eens."),
           ("Wat zijn huismerken?", "Producten onder de naam van de supermarkt zelf, zoals AH, Jumbo, PLUS, 1 de Beste (Dirk), G'woon (Hoogvliet, DekaMarkt, SPAR) en de eigen merken van Lidl en Aldi.")]
    head = ch + f'<h1>Huismerk of A-merk: hoeveel scheelt het?</h1><p class="lead">Het goedkoopste huismerk is vandaag gemiddeld <b>{round(med * 100)}% goedkoper</b> dan het goedkoopste A-merk, per kilo of liter. Hieronder per product.</p>'
    body = (f'<div class="tblwrap"><table class="ptable"><thead><tr><th>Product</th><th style="text-align:right">Scheelt</th></tr></thead><tbody>{rij}</tbody></table></div>'
            f'<p class="note">Vergeleken op {DATUM}: per product het goedkoopste huismerk en het goedkoopste A-merk bij alle supermarkten, op prijs per kilo, liter of stuk. Lopende aanbiedingen tellen mee.</p>'
            + faq_html(faq) + '<p><a href="/besparen/">Meer bespaartips →</a></p><a class="cta" href="/">Vergelijk je eigen lijst</a>')
    schrijf("/huismerk-of-a-merk/", page("/huismerk-of-a-merk/", f"Huismerk of A-merk: gemiddeld {round(med * 100)}% goedkoper ({MAAND})", f"Huismerk vs A-merk: bij {len(_huis_vb)} producten is het huismerk vandaag gemiddeld {round(med * 100)}% goedkoper per kilo of liter. Per product vergeleken, elke dag bijgewerkt.", head, body, [cld, faq_ld(faq)]))
    made.append(("/huismerk-of-a-merk/", "0.8"))

# ---------- Wat kosten boodschappen per week? ----------
# Een duidelijk, zelf samengesteld weekpakket per persoon (ontbijt en lunch) plus 7 avondmaaltijden uit het goedkope weekmenu.
WEEK_PP = [("volkoren brood", 1.5, "st", "Volkorenbrood (1,5 brood)"), ("halfvolle melk", 2, "l", "Halfvolle melk (2 liter)"), ("yoghurt", 1, "l", "Yoghurt (1 liter)"),
           ("jonge kaas", .15, "kg", "Kaas (150 gram)"), ("pindakaas", .1, "kg", "Pindakaas (100 gram)"), ("roomboter", .1, "kg", "Boter (100 gram)"),
           ("eieren", 4, "st", "Eieren (4)"), ("appels", 1, "kg", "Appels (1 kilo)"), ("bananen", .7, "kg", "Bananen (700 gram)"), ("filterkoffie", .1, "kg", "Koffie (100 gram)")]
def _itemprijs(t, q, u, si):
    rows = PICKED.get(t, [])
    p = next((p for s_, p in rows if s_ == si), None)
    if not p: return None, None
    v = vgl_unit(p) if p[6] == u and vgl_unit(p) else None
    return (v * q if v else eff(p)), p
_wk_items = {si: [_itemprijs(t, q, u, si) for t, q, u, _ in WEEK_PP] for si, st_ in enumerate(stores) if st_.get("count")}
_wk_med = [statistics.median([v[i][0] for v in _wk_items.values() if v[i][0]] or [0]) for i in range(len(WEEK_PP))]
def _weekprijs(si):
    """Kosten van het weekpakket per persoon bij winkel si; ontbreken er hoogstens 2 producten, dan telt daarvoor de middenprijs."""
    it = _wk_items[si]; mist = sum(1 for k, p in it if k is None)
    if mist > 2: return None, []
    return sum(k if k is not None else _wk_med[i] for i, (k, p) in enumerate(it)), it
_wm = WEEKMENU_PRIJS.get("weekmenu")
_wk_rij = []
for si, st_ in enumerate(stores):
    if not st_.get("count"): continue
    t, r = _weekprijs(si)
    if t: _wk_rij.append((si, t, r))
_wk_rij.sort(key=lambda x: x[1])
print("weekpakket:", "weekmenu" if _wm else "geen weekmenu", len(_wk_rij), "winkels compleet")
if _wm and len(_wk_rij) >= 3:
    avond_pp = _wm[0] / 20 * 7  # 7 avondmaaltijden per persoon, uit het weekmenu (5 maaltijden voor 4 personen)
    lo, hi = _wk_rij[0], _wk_rij[-1]
    def bedrag(pers, si_t): return si_t * pers + avond_pp * pers
    rows = "".join(f'<tr><td><b>{n} {"persoon" if n == 1 else "personen"}</b></td><td class="p">{eur(bedrag(n, lo[1]))}<span class="sub">per week</span></td><td class="p">{eur(bedrag(n, lo[1]) * 52 / 12)}<span class="sub">per maand</span></td></tr>' for n in (1, 2, 3, 4))
    lijst = "".join(f"<li>{esc(lbl)}</li>" for _, _, lbl in [(0, 0, x[3]) for x in WEEK_PP])
    perw = "".join(f'<tr{" class=win" if i == 0 else ""}><td><b>{i + 1}. {esc(nm(si))}</b></td><td class="p">{eur(t)}</td></tr>' for i, (si, t, r) in enumerate(_wk_rij))
    ch, cld = crumbs(("Besparen", "/besparen/"), ("Boodschappen per week", None))
    faq = [("Hoeveel geef je uit aan boodschappen per week?", f"Kook je zuinig en doe je boodschappen bij de goedkoopste supermarkt, dan kom je met ons rekenvoorbeeld op ongeveer {eur(bedrag(1, lo[1]))} per persoon per week, en {eur(bedrag(4, lo[1]))} voor een gezin van 4 ({DATUM}). Met A-merken, vlees elke dag en snacks ligt het bedrag al snel een stuk hoger."),
           ("Hoeveel geld voor boodschappen per maand?", f"Volgens hetzelfde voorbeeld ongeveer {eur(bedrag(1, lo[1]) * 52 / 12)} per maand voor 1 persoon en {eur(bedrag(2, lo[1]) * 52 / 12)} voor 2 personen. Het Nibud geeft eigen richtbedragen per huishouden; dit is wat het met de echte prijzen van vandaag kost."),
           ("Hoe is dit berekend?", f"Per persoon per week: een vast pakket voor ontbijt en lunch (zie de lijst) bij de goedkoopste supermarkt, plus 7 avondmaaltijden van het goedkope weekmenu ({eur(_wm[0] / 20)} per persoon per maaltijd). Drinken, snacks, verzorging en schoonmaakmiddelen tellen niet mee.")]
    head = ch + f'<h1>Wat kosten boodschappen per week?</h1><p class="lead">Met de echte prijzen van vandaag: zuinig eten kost ongeveer <b>{eur(bedrag(1, lo[1]))} per persoon per week</b>, bij {esc(nm(lo[0]))}. Voor een gezin van 4 is dat {eur(bedrag(4, lo[1]))}.</p>'
    body = (f'<div class="tblwrap"><table class="ptable"><thead><tr><th>Huishouden</th><th style="text-align:right">Week</th><th style="text-align:right">Maand</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<h2>Wat zit erin?</h2><p>Per persoon per week, voor ontbijt en lunch:</p><ul class="links">{lijst}</ul><p>Plus 7 avondmaaltijden uit het <a href="/maaltijden/weekmenu/">goedkope weekmenu</a> ({eur(avond_pp)} per persoon per week).</p>'
            f'<h2>Ontbijt en lunch per supermarkt</h2><p class="note">Het weekpakket voor 1 persoon, zonder avondeten.</p><div class="tblwrap"><table class="ptable"><tbody>{perw}</tbody></table></div>'
            + faq_html(faq) + '<p><a href="/besparen/">Zo bespaar je nog meer →</a></p><a class="cta" href="/">Bereken het voor je eigen lijst</a>')
    schrijf("/boodschappen-per-week/", page("/boodschappen-per-week/", f"Wat kosten boodschappen per week? Vanaf {eur(bedrag(1, lo[1]))} per persoon ({MAAND})", f"Hoeveel geld kwijt aan boodschappen per week of maand? Met de echte prijzen van vandaag: ongeveer {eur(bedrag(1, lo[1]))} per persoon per week, {eur(bedrag(4, lo[1]))} voor 4 personen. Zo is het berekend.", head, body, [cld, faq_ld(faq)]))
    made.append(("/boodschappen-per-week/", "0.8"))
    print("/boodschappen-per-week/:", eur(bedrag(1, lo[1])), "pp")
    # Budgetpagina's: eten voor 50 euro per week en studentenboodschappen (zelfde rekenvoorbeeld, echte prijzen van vandaag)
    _wm_si = _wm[1]
    _tips = ('<h2>Zo blijf je binnen je budget</h2><ul><li><b>Kook met een weekmenu</b> en koop alles in één keer: ingrediënten die in meer gerechten zitten koop je maar één keer. <a href="/maaltijden/weekmenu/">Bekijk het goedkope weekmenu met boodschappenlijst</a>.</li>'
             '<li><b>Kies huismerken</b>: die zijn vaak een derde goedkoper. <a href="/huismerk-of-a-merk/">Huismerk of A-merk per product</a>.</li>'
             '<li><b>Kook voor meer dagen</b> en vries porties in; dat scheelt geld en tijd.</li>'
             '<li><b>Let op de prijs per kilo</b>, niet op de prijs van het pak. En check of een aanbieding echt goedkoper is: daarvoor tonen we bij elk product of de prijs lager of hoger is dan normaal.</li>'
             '<li><b>Vergelijk je eigen lijst</b>: in de app zie je in één keer welke supermarkt voor jouw boodschappen het goedkoopst is.</li></ul>')
    b1, b2 = bedrag(1, lo[1]), bedrag(2, lo[1])
    past = "past" if b2 <= 50 else "past net niet"
    ch, cld = crumbs(("Besparen", "/besparen/"), ("Eten voor 50 euro per week", None))
    faq = [("Kun je met 2 personen eten voor 50 euro per week?", f"Ja, als je zuinig kookt: met de prijzen van {DATUM} kost ons rekenvoorbeeld voor 2 personen {eur(b2)} per week bij {nm(lo[0])}. Dat is ontbijt, lunch en 7 avondmaaltijden."),
           ("Hoeveel kost eten per persoon per week?", f"Ongeveer {eur(b1)} per persoon per week bij de goedkoopste supermarkt, met het goedkope weekmenu als avondeten."),
           ("Wat is het goedkoopste avondeten?", f"Bekijk de 10 goedkoopste maaltijden: die kosten soms minder dan 2 euro per persoon.")]
    head = ch + f'<h1>Eten voor 50 euro per week: zo doe je het</h1><p class="lead">Met de echte prijzen van vandaag kost zuinig eten voor <b>2 personen {eur(b2)} per week</b> bij {esc(nm(lo[0]))}: ontbijt, lunch en 7 avondmaaltijden. Dat {past} binnen 50 euro.</p>'
    body = (f'<div class="tblwrap"><table class="ptable"><thead><tr><th>Huishouden</th><th style="text-align:right">Per week</th></tr></thead><tbody>'
            + "".join(f'<tr><td><b>{n} {"persoon" if n == 1 else "personen"}</b></td><td class="p">{eur(bedrag(n, lo[1]))}{" ✓ onder € 50" if bedrag(n, lo[1]) <= 50 else ""}</td></tr>' for n in (1, 2, 3, 4))
            + f'</tbody></table></div><p class="note">Ontbijt en lunch: een vast weekpakket (brood, melk, yoghurt, kaas, pindakaas, boter, eieren, fruit en koffie) bij {esc(nm(lo[0]))}. Avondeten: het <a href="/maaltijden/weekmenu/">goedkope weekmenu</a>, {eur(_wm[0] / 20)} per persoon per maaltijd. Prijzen van {DATUM}.</p>'
            + _tips + faq_html(faq) + '<p><a href="/boodschappen-per-week/">Wat kosten boodschappen per week?</a> · <a href="/maaltijden/goedkoop-avondeten/">De 10 goedkoopste maaltijden</a> · <a href="/studentenboodschappen/">Studentenboodschappen</a></p>')
    schrijf("/eten-voor-50-euro-per-week/", page("/eten-voor-50-euro-per-week/", f"Eten voor 50 euro per week (2 personen): kan dat? ({MAAND})", f"Boodschappen voor 50 euro per week: met de echte prijzen van vandaag kost zuinig eten voor 2 personen {eur(b2)} per week. Met weekmenu, boodschappenlijst en tips.", head, body, [cld, faq_ld(faq)]))
    made.append(("/eten-voor-50-euro-per-week/", "0.7"))
    ch, cld = crumbs(("Besparen", "/besparen/"), ("Studentenboodschappen", None))
    faq = [("Hoeveel geeft een student uit aan boodschappen?", f"Met ons rekenvoorbeeld kost zuinig eten voor 1 persoon {eur(b1)} per week, ongeveer {eur(b1 * 52 / 12)} per maand, bij {nm(lo[0])}."),
           ("Welke supermarkt is het goedkoopst voor studenten?", f"Voor dit weekpakket is {nm(lo[0])} nu het goedkoopst. Voor je eigen lijst kan het anders uitvallen; vergelijk die in de app."),
           ("Hoe kook je goedkoop voor 1 persoon?", "Kook voor 4 porties en vries de rest in, of eet het de volgende dag. Een weekmenu voor 4 personen is voor 1 persoon goed voor bijna 3 weken avondeten uit de vriezer.")]
    head = ch + f'<h1>Studentenboodschappen: goedkoop eten op kamers</h1><p class="lead">Zuinig eten kost met de prijzen van vandaag ongeveer <b>{eur(b1)} per week</b> ({eur(b1 * 52 / 12)} per maand) bij {esc(nm(lo[0]))}. Zo houd je geld over.</p>'
    body = (f'<h2>Wat kost het?</h2><ul class="links"><li>Ontbijt en lunch: {eur(lo[1])} per week</li><li>7 avondmaaltijden uit het <a href="/maaltijden/weekmenu/">goedkope weekmenu</a>: {eur(avond_pp)} per week</li></ul>'
            + '<h2>Goedkope studentenmaaltijden</h2><ul class="links"><li><a href="/maaltijden/goedkoop-avondeten/">De 10 goedkoopste maaltijden</a></li><li><a href="/maaltijden/vegan/">🌱 Vegan maaltijden</a> (vaak extra goedkoop)</li><li><a href="/maaltijden/eiwitrijk/">💪 Eiwitrijk voor sporters</a></li><li><a href="/maaltijden/pasta/">Pasta</a> en <a href="/maaltijden/rijst-en-noedels/">rijst en noedels</a></li></ul>'
            + _tips + faq_html(faq) + '<p><a href="/eten-voor-50-euro-per-week/">Eten voor 50 euro per week</a> · <a href="/goedkoopste-supermarkt/">Goedkoopste supermarkt</a></p>')
    schrijf("/studentenboodschappen/", page("/studentenboodschappen/", f"Studentenboodschappen: goedkoop eten vanaf {eur(b1)} per week ({MAAND})", f"Goedkoop eten als student: met de echte prijzen van vandaag ongeveer {eur(b1)} per week bij {nm(lo[0])}. Met goedkope maaltijden, weekmenu en bespaartips.", head, body, [cld, faq_ld(faq)]))
    made.append(("/studentenboodschappen/", "0.7"))

# ---------- Prijsindex: worden boodschappen duurder? (uit data/historie.json) ----------
def pct_nl(x, d=1): return (f"{x:+.{d}f}".replace(".", ",")) + "%"
try:
    _dg = HIST.get("dagen", []); _tm = HIST.get("termen", {})
    def _dagmed(t):
        out = []
        for i in range(len(_dg)):
            vals = sorted(v[i] for v in _tm.get(t, {}).values() if i < len(v) and v[i])
            out.append(statistics.median(vals) if len(vals) >= 3 else None)
        return out
    _bt = [(t, q) for t, q, u in PAKKET if t in _tm]
    _reeks = {t: _dagmed(t) for t, _ in _bt}
    _bt = [(t, q) for t, q in _bt if any(_reeks[t])]  # producten zonder metingen bij 3+ winkels vallen af
    _mand = []
    _laatst = {}
    for i, d in enumerate(_dg):  # ontbreekt een product op een dag, dan telt de vorige meting
        for t, _ in _bt:
            if _reeks[t][i]: _laatst[t] = _reeks[t][i]
        if len(_laatst) == len(_bt): _mand.append((d, sum(_laatst[t] * q for t, q in _bt)))
    print("prijsindex:", len(_mand), "dagen;", [t for t, _ in _bt if t not in _laatst])
    if len(_mand) >= 20:
        per_m = {}
        for d, v in _mand: per_m.setdefault(d[:7], []).append(v)
        mnd = [(m, statistics.mean(v)) for m, v in sorted(per_m.items())]
        basis = mnd[0][1]; laatst = mnd[-1][1]; verschil = (laatst / basis - 1) * 100
        # stijgers en dalers per product: eerste 14 meetdagen tegen de laatste 14
        bew = []
        for t, st_ in _tm.items():
            r = _dagmed(t); a0 = [x for x in r[:14] if x]; a1 = [x for x in r[-14:] if x]
            if len(a0) >= 7 and len(a1) >= 7 and t in PICKED:
                ch_ = statistics.median(a1) / statistics.median(a0) - 1
                if abs(ch_) < .4 and len(st_) >= 4: bew.append((t, ch_))
        stijg = sorted(bew, key=lambda x: -x[1])[:10]; daal = sorted(bew, key=lambda x: x[1])[:10]
        # grafiek (inline SVG)
        W, H = 640, 220; vs = [v for _, v in _mand]; lo_, hi_ = min(vs) * .98, max(vs) * 1.02
        pts = " ".join(f"{20 + i * (W - 40) / (len(_mand) - 1):.1f},{H - 20 - (v - lo_) / (hi_ - lo_) * (H - 40):.1f}" for i, (_, v) in enumerate(_mand))
        svg = (f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Prijs van het boodschappenmandje per dag" style="max-width:640px;display:block"><polyline fill="none" stroke="#0e7c4a" stroke-width="3" points="{pts}"/>'
               f'<text x="20" y="14" font-size="13" fill="currentColor">{eur(hi_ / 1.02)}</text><text x="20" y="{H - 4}" font-size="13" fill="currentColor">{kortdag(_mand[0][0])}</text><text x="{W - 20}" y="{H - 4}" font-size="13" text-anchor="end" fill="currentColor">{kortdag(_mand[-1][0])}</text></svg>')
        MN = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]
        mrows = "".join(f'<tr><td>{MN[int(m[5:]) - 1]} {m[:4]}</td><td class="p">{eur(v)}</td><td class="p">{pct_nl((v / basis - 1) * 100)}</td></tr>' for m, v in mnd)
        lijstje = lambda xs: "".join(f'<li><a href="/vergelijk/{slug(t)}/">{esc(cap(t))}</a>: <b>{pct_nl(c * 100, 0)}</b></li>' for t, c in xs)
        richting = "duurder" if verschil > 0.5 else "goedkoper" if verschil < -0.5 else "ongeveer even duur"
        ch, cld = crumbs(("Besparen", "/besparen/"), ("Prijsindex", None))
        faq = [("Worden boodschappen duurder?", f"Ons vaste mandje van {len(_bt)} basisboodschappen kostte in {MN[int(mnd[0][0][5:]) - 1]} gemiddeld {eur(basis)} en in {MN[int(mnd[-1][0][5:]) - 1]} {eur(laatst)}: {pct_nl(verschil)}. Boodschappen zijn in die periode dus {richting} geworden."),
               ("Hoe meten jullie dit?", "Elke dag slaan we per product de prijs per kilo, liter of stuk op bij alle supermarkten. Voor de index nemen we per product de middelste prijs van alle supermarkten en rekenen we een vast mandje uit. Aanbiedingen tellen niet mee, zodat je de gewone prijzen ziet."),
               ("Wat zegt het CBS?", "Het CBS meet de inflatie voor alle uitgaven, ook voedsel. Onze index is kleiner (alleen basisboodschappen) maar wordt elke dag bijgewerkt.")]
        head = ch + f'<h1>Worden boodschappen duurder? Prijsindex {MAAND}</h1><p class="lead">Een vast mandje van {len(_bt)} basisboodschappen kost nu gemiddeld <b>{eur(laatst)}</b>, {pct_nl(verschil)} ten opzichte van {MN[int(mnd[0][0][5:]) - 1]}. Elke dag gemeten bij alle supermarkten.</p>'
        body = (f'<h2>Het mandje per dag</h2>{svg}<div class="tblwrap"><table class="ptable"><thead><tr><th>Maand</th><th style="text-align:right">Gemiddeld</th><th style="text-align:right">Verschil</th></tr></thead><tbody>{mrows}</tbody></table></div>'
                f'<h2>Het meest duurder geworden</h2><ul class="links">{lijstje(stijg)}</ul><h2>Het meest goedkoper geworden</h2><ul class="links">{lijstje(daal)}</ul>'
                f'<p class="note">Vergelijking van de eerste 14 meetdagen ({kortdag(_dg[0])} en verder) met de laatste 14. Middelste prijs per kilo, liter of stuk van alle supermarkten, zonder aanbiedingen.</p>'
                + faq_html(faq) + '<p><a href="/besparen/">Zo bespaar je toch →</a></p>')
        schrijf("/prijsindex/", page("/prijsindex/", f"Worden boodschappen duurder? Prijsindex {MAAND}: {pct_nl(verschil)}", f"Onze dagelijkse prijsindex van {len(_bt)} basisboodschappen bij alle supermarkten: nu {eur(laatst)}, {pct_nl(verschil)} sinds {MN[int(mnd[0][0][5:]) - 1]}. Met de grootste stijgers en dalers.", head, body, [cld, faq_ld(faq)]))
        made.append(("/prijsindex/", "0.8"))
        print("/prijsindex/:", f"{pct_nl(verschil)}", len(_mand), "dagen")
except Exception as e:
    print("prijsindex overgeslagen:", e)

# ---------- Prijsrapport van de maand: wat werd de afgelopen 30 dagen duurder en goedkoper? ----------
try:
    _dg = HIST.get("dagen", []); _tm = HIST.get("termen", {})
    if len(_dg) >= 40:
        _nu_d = datetime.date.fromisoformat(_dg[-1])
        _i0 = max(i for i, d in enumerate(_dg) if datetime.date.fromisoformat(d) <= _nu_d - datetime.timedelta(days=30))
        def _venster(r, i, n=5):
            v = [x for x in r[max(0, i - n + 1):i + 1] if x]
            return statistics.median(v) if len(v) >= 3 else None
        bew, perw = [], {}
        for t, st_ in _tm.items():
            if t not in PICKED or len(st_) < 4: continue
            r = _dagmed(t); a0, a1 = _venster(r, _i0), _venster(r, len(_dg) - 1)
            if a0 and a1:
                c = a1 / a0 - 1
                if abs(c) < .4: bew.append((t, c, a0, a1))
        # per winkel: het vaste mandje (zelfde producten als de prijsindex) toen en nu
        for w_ in {w for t, _ in _bt for w in _tm.get(t, {})}:
            s0 = s1 = 0; ok = True
            for t, q in _bt:
                r = _tm.get(t, {}).get(w_) or []
                v0, v1 = _venster(r, _i0), _venster(r, len(_dg) - 1)
                if not v0 or not v1: ok = False; break
                s0 += v0 * q; s1 += v1 * q
            if ok and s0: perw[w_] = (s0, s1)
        if len(bew) >= 20:
            stijg = sorted([b_ for b_ in bew if b_[1] > .02], key=lambda x: -x[1])[:12]
            daal = sorted([b_ for b_ in bew if b_[1] < -.02], key=lambda x: x[1])[:12]
            gem = statistics.median(c for _, c, _, _ in bew) * 100
            n_op = sum(1 for b_ in bew if b_[1] > .02); n_af = sum(1 for b_ in bew if b_[1] < -.02)
            MN = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]
            mnd_naam = f"{MN[_nu_d.month - 1]} {_nu_d.year}"
            van = kortdatum(_dg[_i0]); tot = kortdatum(_dg[-1])
            rij = lambda xs: "".join(f'<tr><td><a href="/vergelijk/{slug(t)}/">{esc(cap(t))}</a></td><td class="p">{eur(a0)}</td><td class="p">{eur(a1)}</td><td class="p"><b>{pct_nl(c * 100, 0)}</b></td></tr>' for t, c, a0, a1 in xs)
            tab = lambda xs: f'<div class="tblwrap"><table class="ptable"><thead><tr><th>Product</th><th style="text-align:right">{van}</th><th style="text-align:right">{tot}</th><th style="text-align:right">Verschil</th></tr></thead><tbody>{rij(xs)}</tbody></table></div>'
            wr = sorted(perw.items(), key=lambda kv: kv[1][1] / kv[1][0])
            wtab = ("<h2>Per supermarkt: het vaste mandje</h2><div class=\"tblwrap\"><table class=\"ptable\"><thead><tr><th>Supermarkt</th><th style=\"text-align:right\">Verschil</th></tr></thead><tbody>"
                    + "".join(f'<tr><td>{esc(NAMEN.get(w_, w_))}</td><td class="p"><b>{pct_nl((v[1] / v[0] - 1) * 100)}</b></td></tr>' for w_, v in wr)
                    + "</tbody></table></div><p class=\"note\">Zelfde vaste boodschappen als in de <a href=\"/prijsindex/\">prijsindex</a>, per winkel het voordeligste vergelijkbare product.</p>") if len(perw) >= 3 else ""
            lead = (f"Hoe veranderden de boodschappenprijzen de afgelopen 30 dagen ({van} tot {tot})? Van {len(bew)} producten werden er <b>{n_op} duurder</b> en <b>{n_af} goedkoper</b>; "
                    f"de middelste verandering is {pct_nl(gem)}.")
            body = (f'<h2>Duurder geworden</h2>{tab(stijg)}' if stijg else "") + (f'<h2>Goedkoper geworden</h2>{tab(daal)}' if daal else "") + wtab + (
                f'<p class="note">Per product de middelste prijs per kilo, liter of stuk van alle supermarkten (het voordeligste vergelijkbare product per winkel), gemiddeld over een paar meetdagen om toevallige uitschieters weg te halen. '
                f'Aanbiedingen tellen mee. Bijgewerkt op {DATUM}. <a href="/zo-vergelijken-wij/">Zo vergelijken wij</a></p>'
                '<h2>Meer</h2><ul class="links"><li><a href="/prijsindex/">Prijsindex: worden boodschappen duurder?</a></li><li><a href="/goedkoopste-supermarkt/">Goedkoopste supermarkt</a></li><li><a href="/besparen/">Besparen op boodschappen</a></li></ul>'
                '<p class="note">Je mag dit rapport vrij overnemen met een bronvermelding en link naar boodschappenvergelijk.nl.</p>')
            faq = [("Werden boodschappen de afgelopen maand duurder?", f"Van {len(bew)} vergeleken producten werden er {n_op} duurder en {n_af} goedkoper; de middelste verandering is {pct_nl(gem)}."),
                   ("Wat werd het meest duurder?", f"{cap(stijg[0][0])}: {pct_nl(stijg[0][1] * 100, 0)}." if stijg else "Geen product werd duidelijk duurder."),
                   ("Wat werd het meest goedkoper?", f"{cap(daal[0][0])}: {pct_nl(daal[0][1] * 100, 0)}." if daal else "Geen product werd duidelijk goedkoper.")]
            ch, cld = crumbs(("Prijsindex", "/prijsindex/"), (f"Prijsrapport {mnd_naam}", None))
            schrijf("/prijsrapport/", page("/prijsrapport/", f"Prijsrapport {mnd_naam}: wat werd duurder en goedkoper?",
                    f"Boodschappen in {mnd_naam}: {n_op} producten duurder, {n_af} goedkoper (middelste verandering {pct_nl(gem)}). De grootste stijgers en dalers bij 11 supermarkten.",
                    ch + f"<h1>Prijsrapport {esc(mnd_naam)}: wat werd duurder?</h1><p class=\"lead\">{lead}</p>", body + faq_html(faq), [cld, faq_ld(faq)], og_title=f"Prijsrapport {mnd_naam}"))
            made.append(("/prijsrapport/", "0.7"))
            print("/prijsrapport/:", len(bew), "producten,", n_op, "duurder,", n_af, "goedkoper")
except Exception as e:
    print("prijsrapport overgeslagen:", e)

# ---------- Seizoen: Sinterklaas en kerst ----------
def seizoenpagina(path, kort, h1, title, lead, termen, woorden, faq, extra=""):
    ts = [t for t in termen if t in PICKED]
    if len(ts) < 4: return
    acties = sorted([o for o in OFFERS if any(re.search(r"\b" + w, o["n"].lower()) for w in woorden)], key=lambda o: -o.get("pct", 0))[:24]
    top, n_top = winnaar(ts)
    ch, cld = crumbs(("Feestdagen", "/feestdagen/"), (kort, None))
    head = ch + f'<h1>{esc(h1)}</h1><p class="lead">{lead} Per product de goedkoopste supermarkt, elke dag bijgewerkt. <b>{esc(nm(top))}</b> is nu bij {n_top} van de {len(ts)} producten het goedkoopst.</p>'
    faq = [(f"Waar zijn {kort.lower()}-boodschappen het goedkoopst?", f"Op {DATUM} is {nm(top)} bij {n_top} van de {len(ts)} vergeleken producten het voordeligst."), *faq,
           ("Hoe actueel zijn de prijzen?", "Elke dag bijgewerkt met de prijzen en aanbiedingen van de webshops van de supermarkten.")]
    # Allergievriendelijk: per product een glutenvrije en/of lactosevrije variant (als die er is), en alle zulke feestproducten.
    def _var(rx, kw):
        arr = [p for p in prods if stores[p[0]].get("count") and rx.search(p[1]) and re.search(r"\b" + re.escape(kw), p[1].lower())]
        return sorted(arr, key=lambda p: eff(p))[:2]
    def _vtxt(arr): return "".join(f'<span class="sub">{esc(p[1])} · {esc(nm(p[0]))} · {eur(eff(p))}</span>{addbtn(p, p[1])}' for p in arr) or '<span class="sub">nog niet gevonden</span>'
    arij, alle_v = "", {}
    class _VGZ:  # zelfde vorm als een regex: .search(naam)
        search = staticmethod(lambda n: is_vegan(n))
    for t in ts:
        kws = [w for w in norm(t) if len(w) > 3 and w not in ("gevulde", "roomboter", "naturel")] or norm(t)[:1]
        def _var2(rx): 
            arr = [p for p in prods if stores[p[0]].get("count") and rx.search(p[1]) and all(re.search(r"\b" + re.escape(w), p[1].lower()) for w in kws) and not re.search(r"\bfish\b|\bburger\b", p[1].lower())]
            return sorted(arr, key=lambda p: eff(p))[:2]
        g_, l_, v_ = _var2(GV_RE), _var2(LV_RE), _var2(_VGZ)
        for p in g_ + l_ + v_: alle_v[id(p)] = p
        if g_ or l_ or v_: arij += f'<tr><td><b>{esc(cap(t))}</b></td><td>🌾 {_vtxt(g_)}</td><td>🥛 {_vtxt(l_)}</td><td>🌱 {_vtxt(v_)}</td></tr>'
    # Hoofdgerechten voor wie geen vlees, zuivel of gluten eet: complete maaltijden met prijs per supermarkt.
    def _mli(m): return f'<li><a href="/maaltijden/{m["slug"]}/"><b>{esc(m["naam"])}</b></a> <span class="sub">{eur(m["rang"][0][1]["tot"])} voor 4 personen bij {esc(nm(m["rang"][0][0]))} · {m["kcal"]} kcal p.p.</span></li>'
    _feestvoorkeur = ("stoof", "curry", "massaman", "shepherd", "linzenstoof", "ratatouille", "aubergine", "risotto", "paella", "lasagne", "jachtschotel", "ovenschotel", "zalm", "bolognese", "puttanesca", "quinoa", "pompoen")
    _fv = lambda m: (0 if any(w in m["slug"] for w in _feestvoorkeur) else 1, m["rang"][0][1]["tot"])
    _vgm = sorted([m for m in MAAL if m.get("vegan")], key=_fv)[:5]
    _lvm = sorted([m for m in MAAL if m.get("lactosevrij") and not m.get("vegan")], key=_fv)[:5]
    _gvm = sorted([m for m in MAAL if m.get("glutenvrij") and m not in _vgm and m not in _lvm], key=_fv)[:4]
    _feestmaal = ((f'<h3>Een feestelijk hoofdgerecht zonder vlees, zuivel of gluten</h3>'
                   + (f'<p><b>🌱 Vegan</b> <a href="/maaltijden/vegan/">alle vegan maaltijden</a></p><ul class="links">' + "".join(_mli(m) for m in _vgm) + '</ul>' if _vgm else "")
                   + (f'<p><b>🥛 Lactosevrij</b> <a href="/maaltijden/lactosevrij/">alle lactosevrije maaltijden</a></p><ul class="links">' + "".join(_mli(m) for m in _lvm) + '</ul>' if _lvm else "")
                   + (f'<p><b>🌾 Glutenvrij</b> <a href="/maaltijden/glutenvrij/">alle glutenvrije maaltijden</a></p><ul class="links">' + "".join(_mli(m) for m in _gvm) + '</ul>' if _gvm else "")))
    extra_v = [p for p in prods if stores[p[0]].get("count") and (GV_RE.search(p[1]) or LV_RE.search(p[1]) or is_vegan(p[1])) and any(re.search(r"\b" + w, p[1].lower()) for w in woorden) and id(p) not in alle_v][:30]
    allerg = ((f'<h2>Glutenvrij, lactosevrij of vegan vieren</h2><p class="note">Per product een glutenvrije (🌾), lactosevrije (🥛) of vegan (🌱) variant, de goedkoopste eerst. Controleer bij een allergie altijd het etiket.</p>'
               f'<div class="tblwrap"><table class="ptable"><thead><tr><th>Product</th><th>Glutenvrij</th><th>Lactosevrij</th><th>Vegan</th></tr></thead><tbody>{arij}</tbody></table></div>' if arij else "")
              + (f'<h3>Meer glutenvrije, lactosevrije en vegan feestproducten</h3><div class="tblwrap"><table class="ptable"><tbody>' + "".join(f'<tr><td>{labels(p[1])}<b>{esc(p[1])}</b><span class="sub">{esc(nm(p[0]))} · {esc(p[4] or "")}</span>{addbtn(p, p[1])}</td><td class="p">{tag(eff(p))}</td></tr>' for p in sorted(extra_v, key=eff)) + '</tbody></table></div>' if extra_v else "")
              + _feestmaal + '<p><a href="/glutenvrij/">Alle glutenvrije boodschappen</a> · <a href="/lactosevrij/">Alle lactosevrije boodschappen</a> · <a href="/vegan/">Alle vegan boodschappen</a></p>')
    body = (f'<h2>Prijzen per product</h2>{cat_tabel(ts)}' + allerg
            + (f'<h2>{kort}-aanbiedingen</h2><p class="note">{len(acties)} acties die nu of binnenkort lopen.</p><ul class="offers" id="grid">' + "".join(offer_card(o) for o in acties) + "</ul>" if acties else "")
            + extra + faq_html(faq) + '<a class="cta" href="/">Maak je boodschappenlijst</a>')
    schrijf(path, page(path, title, re.sub(r"<[^>]+>", "", lead)[:150], head, body, [cld, faq_ld(faq)], og_title=h1))
    made.append((path, "0.8"))
    print(path, len(ts), "producten,", len(acties), "acties")
seizoenpagina("/sinterklaas/", "Sinterklaas", "Sinterklaas: pepernoten, chocoladeletters en speculaas vergelijken",
    f"Pepernoten en chocoladeletters: waar het goedkoopst? ({MAAND})",
    "Pepernoten, kruidnoten, chocoladeletters, speculaas, marsepein en taai taai bij alle supermarkten naast elkaar, op prijs per kilo.",
    ["pepernoten", "kruidnoten", "chocolade kruidnoten", "chocoladeletter", "speculaas", "gevulde speculaas", "speculaasbrokken", "taai taai", "marsepein",
     "schuimpjes", "amandelstaaf", "chocolade munten", "borstplaat", "speculaaspasta", "gemberkoek"],
    ["pepernot", "kruidnot", "chocoladeletter", "chocolade letter", "speculaas", "marsepein", "taai", "schuimpjes", "sint", "amandelsta", "borstplaat"],
    [("Wat is het verschil tussen pepernoten en kruidnoten?", "Kruidnoten zijn de kleine, harde, ronde koekjes met speculaaskruiden. Echte pepernoten zijn zachter en taaier, gemaakt met roggemeel en anijs. In de winkel heten kruidnoten vaak ook pepernoten."),
     ("Hoe vergelijk je pepernoten eerlijk?", "Op prijs per kilo: zakken verschillen veel in gewicht. Op deze pagina staat per product de voordeligste verpakking per kilo.")])
seizoenpagina("/kerst/", "Kerst", "Kerst: kerstdiner en kersthapjes per supermarkt vergelijken",
    f"Goedkoop kerstdiner: gourmet, wild en champagne vergeleken ({MAAND})",
    "Gourmetschotels, rollade, hertenbiefstuk, kaasfondue, zalm, garnalen, kerststol en bubbels bij alle supermarkten naast elkaar.",
    ["gourmetschotel", "rollade", "hertenbiefstuk", "kaasfondue", "zalmfilet", "garnalen", "paté", "kerststol", "amandelstaaf", "oliebollen", "appelflappen",
     "champagne", "cava", "prosecco", "glühwein", "advocaat"],
    ["kerst", "gourmet", "fondue", "rollade", "hert", "wild", "kalkoen", "stol", "champagne", "cava", "prosecco", "glühwein", "oliebol"],
    [("Wat kost gourmetten per persoon?", "Een gourmetschotel kost bij de supermarkt meestal tussen de 4 en 8 euro per persoon. Hierboven zie je per supermarkt de voordeligste schotel."),
     ("Wanneer komen de kerstaanbiedingen?", "De meeste supermarkten starten de kerstacties in de weken voor kerst; de grootste kortingen op vlees, vis en drank zie je meestal in de laatste week. Deze pagina werkt dagelijks bij.")],
    extra='<h2>Kerstmenu met prijs per supermarkt</h2><p>Liever een compleet menu? Bekijk de <a href="/maaltijden/">complete maaltijden</a> of het <a href="/maaltijden/weekmenu/">goedkope weekmenu</a> met boodschappenlijst.</p>')
seizoenpagina("/oud-en-nieuw/", "Oud en nieuw", "Oud en nieuw: oliebollen, champagne en krat bier vergelijken",
    f"Oliebollen, champagne en krat bier: waar het goedkoopst? ({MAAND})",
    "Oliebollen, appelflappen, champagne, cava, prosecco, krat bier, chips en borrelhapjes bij alle supermarkten naast elkaar.",
    ["oliebollen", "appelflappen", "champagne", "cava", "prosecco", "pils krat 24 flesjes", "pils blikjes 33 cl tray 24", "chips naturel", "chips paprika", "nootjes", "bitterballen", "kaasstengels", "advocaat"],
    ["oliebol", "appelflap", "champagne", "cava", "prosecco", "krat", "bitterbal", "kaasstengel", "borrel"],
    [("Waar koop je oliebollen het goedkoopst?", "Oliebollen uit de supermarkt verschillen veel in prijs per stuk. Hierboven zie je per supermarkt de voordeligste zak; vlak voor oud en nieuw komen er vaak extra acties bij."),
     ("Wanneer zijn de oud-en-nieuwacties?", "De meeste supermarkten hebben hun oud-en-nieuwacties in de laatste week van december. Deze pagina werkt dagelijks bij.")])

seizoenpagina("/ramadan/", "Ramadan", "Ramadan en Suikerfeest: iftar-boodschappen vergelijken",
    f"Ramadan boodschappen: dadels, linzen en halal vlees goedkoop ({MAAND})",
    "Dadels, linzen, kikkererwten, bulgur, couscous, lamsvlees, merguez, hummus, Turks brood, filodeeg en noten voor de iftar en het Suikerfeest, bij alle supermarkten naast elkaar.",
    ["dadels", "medjoul dadels", "rode linzen", "kikkererwten", "bulgur", "couscous", "vermicelli", "lamsrack", "lamskotelet", "merguez", "hummus", "tahin", "olijven",
     "turks brood", "filodeeg", "griekse yoghurt", "verse munt", "honing", "pistachenoten", "amandelen", "walnoten", "rozijnen"],
    ["dadel", "linzen", "kikkererwt", "bulgur", "couscous", "lams", "merguez", "halal", "hummus", "tahin", "filo", "turks", "pistache", "baklava"],
    [("Wanneer is de Ramadan in 2027?", "De Ramadan begint naar verwachting rond 8 februari 2027 en duurt ongeveer 30 dagen; het Suikerfeest valt dan rond 10 maart 2027. De precieze data hangen af van de maan."),
     ("Waar koop je halal vlees in de supermarkt?", "Halal kip, gehakt en vleeswaren vind je onder andere bij Albert Heijn, Jumbo, Lidl, Dirk en PLUS. Op onze pagina halal boodschappen staan ze naast elkaar."),
     ("Wat eet je bij de iftar?", "Traditioneel breek je het vasten met dadels en water, gevolgd door soep (zoals linzensoep of harira) en een hoofdgerecht. Hierboven zie je waar de ingrediënten het goedkoopst zijn.")],
    extra='<h2>Halal koken tijdens de Ramadan</h2><ul class="links"><li><a href="/halal/">Halal boodschappen vergelijken</a></li><li><a href="/maaltijden/halal/">Halal maaltijden met prijs per supermarkt</a></li><li><a href="/maaltijden/weekmenu-halal/">📅 Halal weekmenu met boodschappenlijst</a></li><li><a href="/maaltijden/turkse-linzensoep/">Turkse linzensoep</a> · <a href="/maaltijden/linzendahl/">Dahl met rode linzen</a></li></ul>')
seizoenpagina("/chanoeka/", "Chanoeka", "Chanoeka: donuts, latkes en feestboodschappen vergelijken",
    f"Chanoeka boodschappen: donuts, rösti en appelmoes goedkoop ({MAAND})",
    "Voor Chanoeka eet je traditioneel gerechten met olie: sufganiot (donuts) en latkes (aardappelkoekjes) met appelmoes of zure room. Alle producten bij de supermarkten naast elkaar.",
    ["donuts", "rösti", "aardappelen", "uien", "eieren", "zonnebloemolie", "appelmoes", "zure room", "kaas", "zalmfilet"],
    ["donut", "rösti", "rosti", "appelmoes", "zure room"],
    [("Wanneer is Chanoeka in 2026?", "Chanoeka begint in 2026 op de avond van 4 december en duurt acht dagen, tot en met 12 december."),
     ("Wat eet je met Chanoeka?", "Gerechten die in olie gebakken zijn, als herinnering aan het wonder van de olie: sufganiot (gevulde donuts) en latkes (aardappelkoekjes), vaak met appelmoes of zure room.")],
    extra='<h2>Koosjer koken</h2><p><a href="/koosjer/">Koosjer boodschappen en maaltijden</a> · <a href="/maaltijden/koosjer/">Koosjere maaltijden met prijs per supermarkt</a> · <a href="/maaltijden/weekmenu-koosjer/">Koosjer weekmenu</a></p>')
seizoenpagina("/pesach/", "Pesach", "Pesach: matzes en seiderboodschappen vergelijken",
    f"Pesach boodschappen: matzes en meer goedkoop ({MAAND})",
    "Matzes, eieren, aardappelen, appels, walnoten en kip voor de seideravond en de week van Pesach, bij alle supermarkten naast elkaar.",
    ["matzes", "matze crackers", "eieren", "aardappelen", "appels", "walnoten", "hele kip", "kippensoep", "zalmfilet", "uien", "winterpeen"],
    ["matze", "matzes", "matzo"],
    [("Wanneer is Pesach in 2027?", "Pesach begint in 2027 op de avond van 21 april (seideravond) en duurt tot en met 29 april."),
     ("Welke matzes zijn koosjer voor Pesach?", "Voor Pesach heb je matzes nodig met een hechsjer voor Pesach. Kijk op de verpakking; gewone matzes en matzecrackers zijn dat niet altijd.")],
    extra='<h2>Koosjer koken</h2><p><a href="/koosjer/">Koosjer boodschappen en maaltijden</a> · <a href="/maaltijden/koosjer/">Koosjere maaltijden</a> · <a href="/maaltijden/weekmenu-koosjer/">Koosjer weekmenu</a></p>')
seizoenpagina("/pasen/", "Pasen", "Pasen: paasontbijt en paasbrunch vergelijken",
    f"Paasontbijt goedkoop: eieren, croissants en meer ({MAAND})",
    "Eieren, croissants, krentenbollen, roomboter, jus d'orange, zalm, kaas, asperges en lamsvlees voor het paasontbijt en paasdiner, bij alle supermarkten naast elkaar.",
    ["eieren", "croissants", "krentenbollen", "roomboter", "sinaasappelsap", "zalmfilet", "jong belegen kaas", "hagelslag", "asperges", "lamsrack", "volkoren brood"],
    ["paas", "pasen", "eitjes", "croissant", "asperge"],
    [("Wanneer is Pasen in 2027?", "Eerste paasdag valt in 2027 op zondag 28 maart, tweede paasdag op maandag 29 maart."),
     ("Wanneer komen de paasaanbiedingen?", "De meeste supermarkten starten hun paasacties in de twee weken voor Pasen. Deze pagina werkt dagelijks bij.")])
seizoenpagina("/bbq/", "Barbecue", "Barbecue: BBQ-vlees, worstjes en houtskool vergelijken",
    f"BBQ goedkoop: vlees, worstjes en houtskool per supermarkt ({MAAND})",
    "Hamburgers, spareribs, saté, spiesjes, worstjes, stokbrood, kruidenboter, sauzen en houtskool voor de barbecue, bij alle supermarkten naast elkaar.",
    ["hamburgers", "spareribs", "kipsaté", "kipspiesjes", "braadworst", "merguez", "stokbrood", "kruidenboter", "maiskolven", "knoflooksaus", "barbecuesaus", "satesaus", "houtskool", "chips naturel"],
    ["bbq", "barbecue", "spies", "saté", "sate", "burger", "spareribs", "worst", "houtskool", "briket"],
    [("Wat kost een barbecue per persoon?", "Met vlees, stokbrood, sauzen en salade ben je in de supermarkt meestal 6 tot 10 euro per persoon kwijt. Hierboven zie je per product waar het het goedkoopst is."),
     ("Is een BBQ-pakket goedkoper?", "Niet altijd. Vergelijk de prijs per kilo: losse hamburgers, worstjes en saté zijn vaak voordeliger dan een kant-en-klaar pakket.")],
    extra='<h2>Vegan of halal barbecueën</h2><p><a href="/vegan/vlees/">🌱 Vegan burgers en worstjes</a> · <a href="/halal/">Halal vlees</a></p>')
seizoenpagina("/lunchtrommel/", "Lunchtrommel", "Lunchtrommel en schoolontbijt: goedkoop en gezond",
    f"Lunchtrommel goedkoop: brood, beleg en fruit vergeleken ({MAAND})",
    "Volkoren brood, krentenbollen, kaas, pindakaas, fruit, komkommer, rijstwafels en drinken voor het schoolontbijt en de lunchtrommel, bij alle supermarkten naast elkaar.",
    ["volkoren brood", "krentenbollen", "jong belegen kaas", "pindakaas", "hagelslag", "appels", "bananen", "komkommer", "halfvolle melk", "ontbijtkoek", "rijstwafels", "capri sun", "fruitbiscuit"],
    ["lunch", "ontbijt", "krentenbol", "rijstwafel", "capri", "brood"],
    [("Wanneer is het Nationaal Schoolontbijt?", "Het Nationaal Schoolontbijt is elk jaar begin november. Basisscholen in heel Nederland ontbijten dan samen in de klas."),
     ("Wat is een gezonde lunchtrommel?", "Volgens het Voedingscentrum: volkoren brood met mager beleg, een stuk groente of fruit en water of melk. Zoete drinkpakjes en koek kun je beter af en toe geven.")])

# ---------- Feestdagen: overzicht van de seizoenspagina's, het huidige feest bovenaan ----------
_md = int(VANDAAG[5:7]) * 100 + int(VANDAAG[8:10])
FEESTEN = [("/sinterklaas/", "🎁", "Sinterklaas", "Pepernoten, kruidnoten, chocoladeletters, speculaas, marsepein en taai taai per supermarkt.", 1001 <= _md <= 1205),
           ("/kerst/", "🎄", "Kerst", "Gourmetschotels, rollade, hertenbiefstuk, kaasfondue, zalm en bubbels voor het kerstdiner.", 1115 <= _md <= 1226),
           ("/oud-en-nieuw/", "🎆", "Oud en nieuw", "Oliebollen, appelflappen, champagne, krat bier en borrelhapjes.", _md >= 1210 or _md <= 101),
           ("/chanoeka/", "🕎", "Chanoeka", "Donuts, latkes (rösti), appelmoes en zure room voor het lichtjesfeest.", 1115 <= _md <= 1213),
           ("/ramadan/", "🌙", "Ramadan en Suikerfeest", "Dadels, linzen, halal vlees, Turks brood en noten voor de iftar.", 115 <= _md <= 312),
           ("/pasen/", "🐣", "Pasen", "Eieren, croissants, zalm en asperges voor het paasontbijt en paasdiner.", 301 <= _md <= 406),
           ("/pesach/", "🫓", "Pesach", "Matzes, eieren, appels en walnoten voor de seideravond.", 401 <= _md <= 430),
           ("/bbq/", "🍖", "Barbecue", "Hamburgers, spareribs, saté, worstjes en houtskool.", 501 <= _md <= 831),
           ("/lunchtrommel/", "🍎", "Lunchtrommel en schoolontbijt", "Brood, beleg, fruit en drinken voor school.", 815 <= _md <= 915 or 1015 <= _md <= 1110)]
FEESTEN = [f for f in FEESTEN if os.path.exists(os.path.join(OUT, f[0].strip("/"), "index.html"))]
FEESTEN.sort(key=lambda f: not f[4])
ch, cld = crumbs(("Feestdagen", None))
head = ch + '<h1>Feestdagen: waar zijn de feestboodschappen het goedkoopst?</h1><p class="lead">Per feest de producten die je nodig hebt, bij alle supermarkten naast elkaar, met de acties die nu lopen. Elke dag bijgewerkt.</p>'
body = ('<ul class="feesten">' + "".join(f'<li class="{"nu" if f[4] else ""}"><a href="{f[0]}"><span class="fi">{f[1]}</span><b>{esc(f[2])}</b>{"<span class=pill>nu</span>" if f[4] else ""}<span class="sub">{esc(f[3])}</span></a></li>' for f in FEESTEN) + "</ul>"
        + '<h2>Ook handig</h2><ul class="links"><li><a href="/maaltijden/weekmenu/">Goedkoop weekmenu met boodschappenlijst</a></li><li><a href="/aanbieding/krat-bier/">Krat bier aanbieding</a></li><li><a href="/aanbiedingen/">Alle aanbiedingen van deze week</a></li><li><a href="/goedkoopste-supermarkt/">De goedkoopste supermarkt</a></li></ul>')
schrijf("/feestdagen/", page("/feestdagen/", f"Feestdagen: Sinterklaas, kerst, Ramadan, Pasen en meer goedkoop ({MAAND})", "Sinterklaas, kerst, oud en nieuw, Chanoeka, Ramadan, Pasen, Pesach en de barbecue: per feest de boodschappen bij alle supermarkten naast elkaar, met de acties van nu. Elke dag bijgewerkt.", head, body, [cld], actief="/feestdagen/"))
made.append(("/feestdagen/", "0.8"))

# ---------- 404, sitemap, robots ----------
schrijf("/404.html", page("/404.html", "Pagina niet gevonden | Goedkope Boodschappen", "Deze pagina bestaat niet (meer).", "<h1>Deze pagina bestaat niet</h1><p class=\"lead\">Misschien is het product verplaatst. Zoek het gewoon opnieuw.</p>",
    '<form action="/" class="tools" style="max-width:520px"><label><span class="sr">Zoek een product</span><input type="search" name="q" placeholder="Bijvoorbeeld pindakaas"></label></form><a class="cta" href="/">Naar de startpagina</a>'))
_beeld = lambda p: "".join(f"<image:image><image:loc>{u}</image:loc></image:image>" for u in MAAL_BEELDEN.get(p, []))
open(os.path.join(OUT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' +
    "".join(f"  <url><loc>{BASE}{p}</loc><lastmod>{VANDAAG}</lastmod><changefreq>daily</changefreq><priority>{pr}</priority>{_beeld(p)}</url>\n" for p, pr in made) + "</urlset>\n")
open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
print(len(made), "pagina's in de sitemap")
