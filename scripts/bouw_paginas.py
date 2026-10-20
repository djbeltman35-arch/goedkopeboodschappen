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
NAV = [("/aanbiedingen/", "Aanbiedingen", ""), ("/maaltijden/", "Maaltijden", ""), ("/goedkoopste-supermarkt/", "Goedkoopste<span class=lg> supermarkt</span>", ""), ("/categorie/", "Categorieën", "wide")]
def header(actief=""):
    links = "".join(f'<a href="{h}"{" class=" + c if c else ""}{" aria-current=page" if h == actief else ""}>{t}</a>' for h, t, c in NAV)
    return f'<header class="top"><div class="wrap bar"><a class="brand" href="/"><img src="/icons/icon.svg" alt="" width="34" height="34"><span>Goedkope Boodschappen</span></a><nav class="nav" aria-label="Menu">{links}</nav></div></header>'
FOOTER = f'''<footer class="foot"><div class="wrap"><p class="free">Goedkope Boodschappen is gratis en onafhankelijk. Geen reclame, geen betaalde plekken, geen commissie: ik verdien er geen cent aan.</p>
<nav aria-label="Over"><a href="/over/">Over deze site</a><a href="/privacy/">Privacy</a><a href="/aanbiedingen/">Aanbiedingen</a><a href="/maaltijden/">Complete maaltijden</a><a href="/glutenvrij/">Glutenvrij</a><a href="/sinterklaas/">Sinterklaas</a><a href="/kerst/">Kerst</a><a href="/goedkoopste-supermarkt/">Goedkoopste supermarkt</a><a href="/vergelijk/">Alle producten</a><a href="mailto:goedkopeboodschappen@proton.me">Contact: goedkopeboodschappen@proton.me</a></nav>
<p class="small">Gemaakt door Erik. Prijzen van de webshops van de supermarkten, bijgewerkt op {DATUM}. De prijs aan de kassa is leidend.</p><p class="small">Meer gratis van Erik: <a href="https://goedkopertanken.netlify.app/">Tankwijzer (goedkoper tanken)</a> · <a href="https://vluchtwijzer.netlify.app/">Vluchtwijzer</a> · <a href="https://vakantietoppers.netlify.app/">Vakantiewijzer</a></p></div></footer>'''
# Knoppen "+ Op mijn lijst" op losse pagina's: bewaren in de browser en op de startpagina aan de lijst toevoegen.
LISTJS = '''<div class="dock" id="dock" hidden><span id="dockt"></span><a class="btn" href="/#lijst">Mijn lijst</a></div>
<script>(()=>{const K="lijst-erbij",get=()=>{try{return JSON.parse(localStorage.getItem(K)||"[]")}catch(e){return []}},put=v=>{try{localStorage.setItem(K,JSON.stringify(v));return true}catch(e){return false}},
cnt=()=>{try{return (JSON.parse(localStorage.getItem("lijst-v3")||"[]")||[]).length}catch(e){return 0}};
window.mark=()=>{const q=get(),u=new Set(q.map(x=>x.u));document.querySelectorAll(".add[data-o]").forEach(b=>{const o=JSON.parse(b.dataset.o);if(u.has(o.u)){b.textContent="✓ Klaar voor je lijst";b.classList.add("on")}});
const n=q.length,m=cnt(),d=document.getElementById("dock");if(!d)return;d.hidden=false;document.body.classList.add("hasdock");document.getElementById("dockt").innerHTML=n?"<b>"+n+(n===1?" artikel":" artikelen")+"</b> klaar voor je lijst":m?"<b>Mijn lijst</b>: "+m+(m===1?" artikel":" artikelen"):"<b>Mijn lijst</b> is nog leeg"};
const gc=(p,t)=>{try{window.goatcounter&&goatcounter.count&&goatcounter.count({path:p,title:t||p,event:true})}catch(e){}};
document.addEventListener("click",ev=>{const out=ev.target.closest("[data-out]");if(out){gc("naar/"+out.dataset.out,"Doorklik");return}const b=ev.target.closest(".add[data-o]");if(!b)return;const o=JSON.parse(b.dataset.o),q=get();if(!q.some(x=>x.u===o.u)){q.push(o);if(!put(q)){b.textContent="Bewaren lukt niet in deze browser";return}gc("lijst/"+(o.term||o.n).toLowerCase(),"Op lijst")}mark()});mark()})()</script>'''
def page(path, title, desc, head_html, body_html, ld=None, actief="", extra_css="", og_title=None, og_img=None):
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
def labels(naam, kt=""):
    return (('<span class="lbl gv">🌾 Glutenvrij</span>' if GV_RE.search(naam or "") else "")
            + ('<span class="lbl arm">🥗 Caloriearm</span>' if kcal_arm(kt) else ""))

def crumbs(*items):
    # Duidelijk terug kunnen: een knop naar de bovenliggende pagina en naar Home, met daaronder het kruimelpad.
    ouder = [(t, h) for t, h in items if h]
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
            f'<span><a class="on" href="{esc(o["u"])}" rel="nofollow noopener" target="_blank" data-out="{o["s"]}">{esc(o["n"])}</a> <span class="sz">{esc(o.get("sz") or "")}</span>{labels(o["n"], o.get("kc"))}</span>'
            + (f'<span class="kc">{esc(o["kc"])}</span>' if o.get("kc") else "") +
            f'<span class="prow">{tag(o["p"], "deal")}{was}{pp}</span>{t}{offerbtn(o)}</li>')
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
    return (f'<h2>Prijsverloop van {esc(t)}</h2><div class="panel">{svg}<p class="note" style="margin:8px 0 0"><span style="color:var(--green);font-weight:700">━</span> laagste prijs per {esc(eh)} &nbsp; '
            f'<span style="color:var(--muted);font-weight:700">┅</span> middelste prijs van alle supermarkten</p></div><p>{esc(tekst)}</p>')

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
                f'<a href="{esc(plink(p))}" rel="nofollow noopener" target="_blank" data-out="{stores[si]["id"]}"><b>{esc(p[1])}</b></a><span class="sub">{esc(p[4] or "")}</span>{labels(p[1], kcal_txt(t))}{fout_knop(t, si, p)}{addbtn(p, t)}</td>'
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
    return (f'<tr><td><a href="/vergelijk/{slug(t)}/"><b>{esc(cap(t))}</b></a><span class="sub">{esc(p[1])}</span>' + (f'<span class="kc">{esc(kt)}</span>' if kt else "") + labels(p[1], kt) + winkels_txt(t) + fout_knop(t, si, p) + f'{addbtn(p, t)}</td>'
            + f'<td><b>{esc(NAMEN.get(stores[si]["id"]))}</b></td><td class="p">{tag(eff(p))}<br><span class="unit">{esc(per(*toon_unit(p)) or "inhoud onbekend")}</span></td></tr>')
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
    kop = '<div class="tblwrap"><table class="ptable"><thead><tr><th>Product</th><th>Goedkoopst bij</th><th style="text-align:right">Prijs</th></tr></thead><tbody>'
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
        body = (cat_tabel(items) + (f'<h2>Meer in {esc(g.lower())}</h2><ul class="chips">' + "".join(f'<li><a href="/categorie/{slug(x[0])}/">{x[1]} {esc(x[0])}</a></li>' for x in broers) + "</ul>" if broers else "")
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
    return bool(c)
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
        title = f"{'AH Bonus' if cur == 'ah' else nm + ' aanbiedingen'} deze week: {len(nu_)} acties" + (f" t/m {kortdag(eind)}" if eind else "")
        desc = f"Alle {len(nu_)} {naam_actie} van {nm} op een rij, de grootste korting eerst" + (f", zoals {beste['n']} voor {eur(beste['p'])}" if beste else "") + ". Elke dag bijgewerkt, met directe links naar het product."
        h1 = f"{'AH Bonus' if cur == 'ah' else nm + ' aanbiedingen'} deze week"
        lead = f"<span id=\"cnt\">{len(nu_)}</span> acties van {esc(nm)}, de grootste korting eerst." + (f" Plus {len(straks)} acties die binnenkort beginnen." if straks else "")
    else:
        title = f"Alle supermarktaanbiedingen deze week: {len(nu_)} acties bij {len(winkels_o)} winkels"
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
    title = f"Goedkoopste supermarkt van Nederland: {nm(w['si'])} ({MAAND})"
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
    paren = [(a, b) for a, b in itertools.combinations([r["si"] for r in PAK[:8]], 2)]
    body = (f'<div class="tblwrap"><table class="ptable"><thead><tr><th>Supermarkt</th><th style="text-align:right">Totaal</th><th style="text-align:right">Verschil</th></tr></thead><tbody>{trs}</tbody></table></div>'
            f'<p class="note">Bijgewerkt op {DATUM}. Supermarkten met te weinig producten online (zoals Vomar en Poiesz) staan alleen in de lijst als we genoeg van deze boodschappen vinden.</p>'
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
over = f'''<div class="panel"><h2 style="margin-top:0">Ik verdien er niets aan</h2><p>Goedkope Boodschappen is een hobbyproject van Erik. Er staat geen reclame op, supermarkten kunnen geen plek kopen en er zitten geen affiliatelinks in: als je doorklikt naar een supermarkt, krijg ik daar niets voor. De volgorde is altijd gewoon: goedkoopste eerst.</p></div>
<h2>Waarom deze site?</h2><p>Boodschappen zijn duur en iedere supermarkt is ergens anders goedkoop. Met deze site zie je in een paar seconden waar jouw lijst het minst kost, zonder dat je zelf tien folders hoeft door te bladeren.</p>
<h2>Waar komen de prijzen vandaan?</h2><p>Elke dag halen we automatisch de prijzen en aanbiedingen op van de webshops van {AANTAL} supermarkten: {", ".join(NAMEN[s] for s in ACTIEF if s in NAMEN)}. De gewone prijzen komen deels uit de open dataset van <a href="https://www.checkjebon.nl/" rel="noopener">Checkjebon</a> (MIT-licentie). Vomar, SPAR, Jan Linders en Nettorama zetten hun acties niet als losse prijzen online; daarvan tonen we alleen de gewone prijzen waar die beschikbaar zijn. Coop is inmiddels PLUS geworden.</p>
<p>Supermarkten kunnen in de winkel een andere prijs hanteren dan online. De prijs aan de kassa is altijd leidend.</p>
<h2>Hoe vergelijken we?</h2><p>Per product zoeken we bij elke supermarkt het voordeligste vergelijkbare product en vergelijken we de prijs per kilo, liter of stuk. Varianten als lactosevrij of biologisch tellen alleen mee als je ernaar zoekt. Lopende aanbiedingen rekenen we mee.</p>
<h2>Contact</h2><p>Een fout gezien of een idee? Mail naar <a href="mailto:goedkopeboodschappen@proton.me">goedkopeboodschappen@proton.me</a>.</p>'''
schrijf("/over/", page("/over/", "Over Goedkope Boodschappen: gratis, onafhankelijk en zonder reclame", "Goedkope Boodschappen is een gratis hobbyproject zonder reclame of commissie. Lees waar de prijzen vandaan komen en hoe we vergelijken.",
    crumbs(("Over deze site", None))[0] + "<h1>Over deze site</h1><p class=\"lead\">Gratis, onafhankelijk en zonder reclame. Gemaakt om je geld te besparen, niet om aan je te verdienen.</p>", over))
privacy = '''<h2>Je boodschappenlijst</h2><p>Je lijst en je gekozen supermarkten worden alleen in je eigen browser bewaard. Ze worden niet naar ons verstuurd. Wis je je browsergegevens, dan is je lijst weg.</p>
<h2>Meldingen</h2><p>Zet je meldingen aan, dan bewaren we alleen wat nodig is om je een bericht te sturen: het anonieme adres dat je browser daarvoor maakt, de productnamen op je lijst en je gekozen supermarkten. Geen naam, geen e-mailadres. Zet je meldingen uit, dan wissen we dit meteen.</p>
<h2>E-mail bij aanbiedingen</h2><p>Meld je je aan voor e-mail, dan bewaren we je e-mailadres, de productnamen op je lijst en je gekozen supermarkten. Je krijgt eerst een mail om te bevestigen; zonder bevestiging sturen we niets en wissen we je adres na 7 dagen. Je krijgt hoogstens één mail per dag, en alleen als er iets nieuws in de aanbieding is. Elke mail heeft een afmeldlink; afmelden wist je adres meteen. We gebruiken je adres nergens anders voor en geven het aan niemand.</p>
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
app = (app.replace("{{VERFIJN}}", json.dumps(VERFIJN, ensure_ascii=False)).replace("{{VARIANT}}", json.dumps(VARIANT, ensure_ascii=False)).replace("{{VERSIE}}", VERSIE).replace("{{AANTAL}}", str(AANTAL)).replace("{{CATS}}", json.dumps(cats_app, ensure_ascii=False)).replace("{{KCAL}}", json.dumps({t: kcal_txt(t) for t in PICKED if kcal_txt(t)}, ensure_ascii=False)).replace("{{GROEPEN}}", json.dumps([gg for gg in GROEPEN if any(c[3] == gg[0] for c in cats_app)], ensure_ascii=False))
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
            + '<h2>Glutenvrij koken</h2><p><a href="/maaltijden/glutenvrij/">Glutenvrije maaltijden met prijs per supermarkt</a>: gewone avondmaaltijden zonder pasta, brood of bloem, met de goedkoopste winkel voor alle ingrediënten. In de app kun je ook bij elke categorie op <b>🌾 Alleen glutenvrij</b> tikken.</p>'
            + faq_html(faq) + '<a class="cta" href="/">Vergelijk je hele boodschappenlijst</a>')
    schrijf("/glutenvrij/", page("/glutenvrij/", title, desc, head, body, [cld, faq_ld(faq)], og_title="Glutenvrije boodschappen: waar is het goedkoopst?"))
    made.append(("/glutenvrij/", "0.8"))
    print(len(GV_LIJST), "glutenvrij-pagina's,", totaal, "producten")

# ---------- Seizoen: Sinterklaas en kerst ----------
def seizoenpagina(path, kort, h1, title, lead, termen, woorden, faq, extra=""):
    ts = [t for t in termen if t in PICKED]
    if len(ts) < 4: return
    acties = sorted([o for o in OFFERS if any(re.search(r"\b" + w, o["n"].lower()) for w in woorden)], key=lambda o: -o.get("pct", 0))[:24]
    top, n_top = winnaar(ts)
    ch, cld = crumbs((kort, None))
    head = ch + f'<h1>{esc(h1)}</h1><p class="lead">{lead} Per product de goedkoopste supermarkt, elke dag bijgewerkt. <b>{esc(nm(top))}</b> is nu bij {n_top} van de {len(ts)} producten het goedkoopst.</p>'
    faq = [(f"Waar zijn {kort.lower()}-boodschappen het goedkoopst?", f"Op {DATUM} is {nm(top)} bij {n_top} van de {len(ts)} vergeleken producten het voordeligst."), *faq,
           ("Hoe actueel zijn de prijzen?", "Elke dag bijgewerkt met de prijzen en aanbiedingen van de webshops van de supermarkten.")]
    body = (f'<h2>Prijzen per product</h2>{cat_tabel(ts)}'
            + (f'<h2>{kort}-aanbiedingen</h2><p class="note">{len(acties)} acties die nu of binnenkort lopen.</p><ul class="cards" id="grid">' + "".join(offer_card(o) for o in acties) + "</ul>" if acties else "")
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

# ---------- 404, sitemap, robots ----------
schrijf("/404.html", page("/404.html", "Pagina niet gevonden | Goedkope Boodschappen", "Deze pagina bestaat niet (meer).", "<h1>Deze pagina bestaat niet</h1><p class=\"lead\">Misschien is het product verplaatst. Zoek het gewoon opnieuw.</p>",
    '<form action="/" class="tools" style="max-width:520px"><label><span class="sr">Zoek een product</span><input type="search" name="q" placeholder="Bijvoorbeeld pindakaas"></label></form><a class="cta" href="/">Naar de startpagina</a>'))
_beeld = lambda p: "".join(f"<image:image><image:loc>{u}</image:loc></image:image>" for u in MAAL_BEELDEN.get(p, []))
open(os.path.join(OUT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' +
    "".join(f"  <url><loc>{BASE}{p}</loc><lastmod>{VANDAAG}</lastmod><changefreq>daily</changefreq><priority>{pr}</priority>{_beeld(p)}</url>\n" for p, pr in made) + "</urlset>\n")
open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
print(len(made), "pagina's in de sitemap")
