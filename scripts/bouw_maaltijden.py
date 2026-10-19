"""Pagina's voor complete maaltijden. Wordt met exec() in bouw_paginas.py gedraaid (gebruikt diens sjabloon-functies)."""
from maaltijd_kosten import MAAL, SOORTEN, NOTITIE, I

def hoev(q, eenheid_):
    if eenheid_ == "l": return f"{round(q * 1000)} ml" if q < 1 else f"{str(round(q, 2)).replace('.', ',')} liter"
    return f"{round(q * 1000)} g" if q < 1 else f"{str(round(q, 2)).replace('.', ',')} kg"
def pp(v): return eur(v / 4)

MCSS = ""
# Toont alleen de supermarkten die de bezoeker bij "Mijn supermarkten" heeft aangevinkt (bewaard als "winkels-uit" in de browser).
# Zonder keuze blijft de pagina zoals hij gebouwd is (alle winkels); zo ziet Google ook de volledige vergelijking.
MKJS = ("<script>(()=>{const N=" + json.dumps({s_["id"]: NAMEN.get(s_["id"], s_["name"]) for s_ in stores}, ensure_ascii=False) + ",K=" + json.dumps({s_["id"]: KORT.get(s_["id"], NAMEN.get(s_["id"], s_["name"])) for s_ in stores}, ensure_ascii=False) + r""";
const e=v=>"€ "+v.toFixed(2).replace(".",","),tg=(v,c)=>`<span class="tag ${c||""}"><span class="e">€</span>${v.toFixed(2).replace(".",",")}</span>`,h=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const uit=()=>{try{return new Set(JSON.parse(localStorage.getItem("winkels-uit")||"[]")||[])}catch(x){return new Set()}};
const best=(p,off)=>{let b=null;for(const [s,v] of Object.entries(p))if(!off.has(s)&&(!b||v<b[1]))b=[s,v];return b};
function kaarten(off){document.querySelectorAll("[data-p]").forEach(el=>{const p=JSON.parse(el.dataset.p),b=best(p,off);el.dataset.best=b?b[1]:1e9;
 const k=el.querySelector(".kp"),w=el.querySelector(".kw"),q=el.querySelector(".kpp");if(!k)return;
 if(!b){k.innerHTML="";w.textContent="geen van jouw winkels";if(q)q.textContent="niet alle ingrediënten gevonden";return}
 k.innerHTML=tg(b[1]);w.textContent=N[b[0]]||b[0];if(q)q.textContent=e(b[1]/4)+(q.dataset.kort?" p.p.":" per persoon")});
 document.querySelectorAll("[data-sorteer]").forEach(tb=>{const rs=[...tb.children].sort((a,b)=>a.dataset.best-b.dataset.best);rs.forEach((r,i)=>{tb.appendChild(r);r.classList.toggle("win",i===0);const n=r.querySelector(".rn");if(n)n.textContent=(i+1)+"."})})}
function maaltijd(off){const el=document.getElementById("mdata");if(!el)return;const D=JSON.parse(el.textContent),ban=document.getElementById("mkeus");
 const ord=Object.keys(D.st).filter(s=>!off.has(s)).sort((a,b)=>D.st[a].t-D.st[b].t);const n=Object.keys(N).filter(s=>!off.has(s)).length;
 ban.hidden=false;const mist=Object.keys(N).filter(x=>!off.has(x)&&!D.st[x]);
 ban.innerHTML=`Vergeleken bij <b>jouw ${n} supermarkten</b>.`+(mist.length?` Bij ${mist.map(x=>h(N[x])).join(", ").replace(/, ([^,]*)$/," en $1")} vinden we niet alle ingrediënten online.`:"")+` <a href="/#mystores">Wijzig je supermarkten</a>`;
 if(!ord.length){document.getElementById("mlead").innerHTML="Bij jouw supermarkten vinden we niet alle ingrediënten online. Kies meer supermarkten om deze maaltijd te vergelijken.";
  ["mtop","mtab","malle"].forEach(i=>{const x=document.getElementById(i);if(x)x.innerHTML=""});return}
 const t3=ord.slice(0,3),b=D.st[ord[0]],l=D.st[ord[ord.length-1]];
 document.getElementById("mlead").innerHTML=`Bij jouw supermarkten kosten alle ingrediënten voor 4 personen het minst bij <b>${h(N[ord[0]])}</b>: <b>${e(b.t)}</b>.`+(ord.length>1?` Bij ${h(N[ord[ord.length-1]])} betaal je ${e(l.t-b.t)} meer.`:"");
 document.getElementById("mtoph").textContent=t3.length===3?"De 3 goedkoopste supermarkten":t3.length===2?"Jouw 2 supermarkten":"Jouw supermarkt";document.getElementById("mtop").innerHTML=t3.map((s,i)=>`<li class="${i?"":"w"}"><span class="rk">${i+1}e goedkoopst</span><b style="font-size:19px">${h(N[s])}</b>${tg(D.st[s].t,i?"":"big")}<span class="muted">${e(D.st[s].t/4)} per persoon</span><button type="button" class="add addall" data-m="${D.slug}" data-os="${h(JSON.stringify(D.st[s].os))}">+ Alles op mijn lijst</button></li>`).join("");
 let j=0,rows="";for(const g of D.ing){if(g[2]){rows+=`<tr class="vk"><td>${h(g[0])}<span class="sub">uit de voorraadkast, niet meegeteld</span></td>${t3.map(()=>'<td class="c">–</td>').join("")}</tr>`;continue}
  rows+=`<tr><td><b>${h(g[0])}</b><span class="sub">${h(g[1])}${g[3]?" · optioneel":""}</span></td>${t3.map(s=>{const c=D.st[s].c[j];return c?`<td class="c"><a href="${h(c[2])}" rel="nofollow noopener" target="_blank" data-out="${s}" title="${h(c[1])}">${e(c[0])}</a></td>`:'<td class="c"><span class="muted">niet gevonden</span></td>'}).join("")}</tr>`;j++}
 rows+=`<tr class="win"><td><b>Totaal voor 4 personen</b></td>${t3.map(s=>`<td class="c"><b>${e(D.st[s].t)}</b></td>`).join("")}</tr>`;
 document.getElementById("mtab").innerHTML=`<thead><tr><th>Ingrediënt</th>${t3.map(s=>`<th style="text-align:right">${h(K[s]||N[s])}</th>`).join("")}</tr></thead><tbody>${rows}</tbody>`;
 document.getElementById("malle").innerHTML=ord.map((s,i)=>`<tr${i?"":' class="win"'}><td><b>${i+1}. ${h(N[s])}</b></td><td class="p">${tg(D.st[s].t)}</td><td class="p">${e(D.st[s].t/4)}</td></tr>`).join("")}
function alles(){const off=uit();if(!off.size&&!document.querySelector("[data-best]"))return;kaarten(off);if(off.size)maaltijd(off)}
alles();document.addEventListener("winkels",alles);window.addEventListener("storage",ev=>{if(ev.key==="winkels-uit")alles()})})()</script>""")
MJS = """<script>document.addEventListener("click",e=>{const b=e.target.closest(".addall");if(!b)return;let q=[];try{q=JSON.parse(localStorage.getItem("lijst-erbij")||"[]")}catch(x){}
const os=JSON.parse(b.dataset.os);for(const o of os)if(!q.some(x=>x.u===o.u))q.push(o);try{localStorage.setItem("lijst-erbij",JSON.stringify(q));b.textContent="✓ Klaar voor je lijst";b.classList.add("on");window.mark&&mark();
try{window.goatcounter&&goatcounter.count({path:"maaltijd/lijst/"+b.dataset.m,title:"Maaltijd op lijst",event:true})}catch(x){}}catch(x){b.textContent="Bewaren lukt niet in deze browser"}});</script>"""

def wnaam(si): return NAMEN.get(stores[si]["id"], stores[si]["name"])
def kaart(m):
    si, r = m["rang"][0]
    return (f'<li class="mcard" data-p="{esc(prijzen_json(m))}"><a class="mt" href="/maaltijden/{m["slug"]}/">{esc(m["naam"])}</a>'
            f'<span class="mm">{m["kcal"]} kcal per persoon · {m["tijd"]} min · 4 personen</span>'
            f'<span class="mw"><span class="kp">{tag(r["tot"])}</span><span>bij <b class="kw">{esc(wnaam(si))}</b><br><span class="mm kpp">{pp(r["tot"])} per persoon</span></span></span></li>')
def prijzen_json(m): return json.dumps({stores[si]["id"]: round(r["tot"], 2) for si, r in m["rang"]}, separators=(",", ":"))

SOORT_PAD = {"aardappel": ("aardappelgerechten", "Aardappelgerechten"), "pasta": ("pasta", "Pasta"), "rijst": ("rijst-en-noedels", "Rijst en noedels"), "salade": ("salades", "Salades")}
maal_paden = []
for m in MAAL:
    path = f"/maaltijden/{m['slug']}/"
    top3 = m["rang"][:3]
    (s1, r1) = top3[0]; (sN, rN) = m["rang"][-1]
    naam = m["naam"]; kl = naam[0].lower() + naam[1:]
    title = f"{naam}: wat kost het? Goedkoopst bij {wnaam(s1)} ({eur(r1['tot'])} voor 4)"
    desc = (f"{naam} voor 4 personen kost nu {eur(r1['tot'])} bij {wnaam(s1)} ({pp(r1['tot'])} per persoon), daarna {wnaam(top3[1][0])} en {wnaam(top3[2][0])}. "
            f"{m['kcal']} kcal per persoon. Prijzen van {len(m['rang'])} supermarkten, elke dag bijgewerkt.")
    sp = SOORT_PAD.get(m["soort"])
    ch, cld = crumbs(("Complete maaltijden", "/maaltijden/"), *([(sp[1], f"/maaltijden/{sp[0]}/")] if sp else []), (naam, None))
    # top 3
    ingdata = [[g["naam"], hoev(g["q"], "l" if g["sleutel"] in ("halfvolle melk", "kookroom", "mayonaise") else "kg"), 1 if g["voorraad"] else 0, 1 if g["optioneel"] else 0] for g in m["regels"]]
    stdata = {}
    for si, r in m["rang"]:
        stdata[stores[si]["id"]] = {"t": round(r["tot"], 2),
            "c": [[round(k * 4 / m.get("porties", 4), 2), p[1], plink(p)] if p else None for n, k, p in r["regels"]],
            "os": [{"s": stores[si]["id"], "n": p[1], "sz": p[4] or "", "p": round(eff(p), 2), "u": plink(p), "r": 1, "term": n.lower()} for n, k, p in r["regels"] if p]}
    mdata = json.dumps({"slug": m["slug"], "ing": ingdata, "st": stdata}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tops = ""
    for i, (si, r) in enumerate(top3):
        os_ = [{"s": stores[si]["id"], "n": p[1], "sz": p[4] or "", "p": round(eff(p), 2), "u": plink(p), "r": 1, "term": n.lower()} for n, k, p in r["regels"] if p]
        tops += (f'<li class="{"w" if i == 0 else ""}"><span class="rk">{i + 1}e goedkoopst</span><b style="font-size:19px">{esc(wnaam(si))}</b>{tag(r["tot"], "big" if i == 0 else "")}'
                 f'<span class="muted">{pp(r["tot"])} per persoon</span>'
                 f'<button type="button" class="add addall" data-m="{m["slug"]}" data-os="{esc(json.dumps(os_, ensure_ascii=False))}">+ Alles op mijn lijst</button></li>')
    # ingrediënten x top 3
    kop = "".join(f'<th style="text-align:right">{esc(KORT.get(stores[si]["id"], wnaam(si)))}</th>' for si, _ in top3)
    rijen = ""
    for g in m["regels"]:
        r_ = next(x for x in m["ing"] if x[0] == g["sleutel"] and x[2] == g["naam"])
        eh = "l" if I.get(g["sleutel"], ("",))[0] and g["sleutel"] in ("halfvolle melk", "kookroom", "mayonaise") else "kg"
        hv = hoev(g["q"], eh)
        if g["voorraad"]:
            rijen += f'<tr class="vk"><td>{esc(g["naam"])}<span class="sub">uit de voorraadkast, niet meegeteld</span></td>' + '<td class="c">–</td>' * len(top3) + "</tr>"; continue
        cellen = ""
        for si, _ in top3:
            if si in g["prijzen"]:
                k, p = g["prijzen"][si]
                cellen += f'<td class="c"><a href="{esc(plink(p))}" rel="nofollow noopener" target="_blank" data-out="{stores[si]["id"]}" title="{esc(p[1])}">{eur(k)}</a></td>'
            else: cellen += '<td class="c"><span class="muted">niet gevonden</span></td>'
        rijen += f'<tr><td><b>{esc(g["naam"])}</b><span class="sub">{hv}{" · optioneel" if g["optioneel"] else ""}</span></td>{cellen}</tr>'
    rijen += '<tr class="win"><td><b>Totaal voor 4 personen</b></td>' + "".join(f'<td class="c"><b>{eur(r["tot"])}</b></td>' for _, r in top3) + "</tr>"
    alle = "".join(f'<tr{" class=win" if i == 0 else ""}><td><b>{i + 1}. {esc(wnaam(si))}</b></td><td class="p">{tag(r["tot"])}</td><td class="p">{pp(r["tot"])}</td></tr>' for i, (si, r) in enumerate(m["rang"]))
    bnaam, burl = m["bron"]
    noot = NOTITIE.get(m["slug"], "")
    faq = [(f"Wat kost {kl}?", f"{naam} voor 4 personen kost nu {eur(r1['tot'])} bij {wnaam(s1)}, dat is {pp(r1['tot'])} per persoon. Bij {wnaam(sN)} betaal je {eur(rN['tot'])}."),
           (f"Waar is {kl} het goedkoopst?", f"De ingrediënten zijn samen het goedkoopst bij {wnaam(s1)} ({eur(r1['tot'])}), gevolgd door {wnaam(top3[1][0])} ({eur(top3[1][1]['tot'])}) en {wnaam(top3[2][0])} ({eur(top3[2][1]['tot'])})."),
           (f"Hoeveel calorieën heeft {kl}?", f"Ongeveer {m['kcal']} kcal per persoon, berekend uit de ingrediënten van het recept voor 4 personen."),
           ("Hoe wordt de prijs berekend?", "Per supermarkt zoeken we voor elk ingrediënt het voordeligste passende product en rekenen we met de prijs per kilo, liter of stuk voor de hoeveelheid die in het recept gaat. Aanbiedingen die nu lopen tellen mee. Olie, zout, kruiden en andere voorraadkastspullen tellen niet mee.")]
    head = (ch + f"<h1>{esc(naam)}: waar is het goedkoopst?</h1><p class=\"lead\" id=\"mlead\">Alle ingrediënten voor 4 personen kosten nu <b>{eur(r1['tot'])}</b> bij <b>{esc(wnaam(s1))}</b>. "
            f"Bij {esc(wnaam(sN))} betaal je {eur(rN['tot'] - r1['tot'])} meer.</p>"
            f'<p class="feiten"><span><b>{m["kcal"]}</b> kcal per persoon</span><span><b>{m["tijd"]}</b> minuten</span><span><b>4</b> personen</span><span>Recept: <a href="{esc(burl)}" rel="noopener" target="_blank">{esc(bnaam)}</a></span></p>')
    andere = [x for x in MAAL if x["soort"] == m["soort"] and x is not m] + [x for x in MAAL if x["soort"] != m["soort"]]
    body = (f'<p class="note" id="mkeus" hidden></p><h2 id="mtoph">De 3 goedkoopste supermarkten</h2><ul class="mtop" id="mtop">{tops}</ul>'
            f'<h2>Wat heb je nodig?</h2><div class="tblwrap"><table class="ptable" id="mtab"><thead><tr><th>Ingrediënt</th>{kop}</tr></thead><tbody>{rijen}</tbody></table></div>'
            f'<p class="note">Prijzen van {DATUM}, naar gebruikte hoeveelheid: in de winkel koop je vaak een heel pak, de rest heb je over voor een volgende keer. Tik op een prijs voor het product. {esc(noot)}</p>'
            f'<h2>Bereiding</h2><p>De bereiding staat in het originele recept op <a href="{esc(burl)}" rel="noopener" target="_blank">{esc(bnaam)}</a>. Daar vind je ook de stappen en tips.</p>'
            f'<h2>Alle supermarkten</h2><div class="tblwrap"><table class="ptable"><thead><tr><th>Supermarkt</th><th style="text-align:right">4 personen</th><th style="text-align:right">Per persoon</th></tr></thead><tbody id="malle">{alle}</tbody></table></div>'
            f'<p class="note">Supermarkten waar we een ingrediënt niet online vinden, staan niet in de lijst.</p>'
            + faq_html(faq) + '<h2>Meer complete maaltijden</h2><ul class="mgrid">' + "".join(kaart(x) for x in andere[:6]) + '</ul><a class="cta" href="/maaltijden/">Alle complete maaltijden</a>' + MJS
            + f'<script type="application/json" id="mdata">{mdata}</script>' + MKJS)
    ing_lijst = [f'{hoev(x[1], "l" if x[0] in ("halfvolle melk", "kookroom", "mayonaise") else "kg")} {x[2].lower()}' for x in m["ing"]]
    recipe = {"@context": "https://schema.org", "@type": "Recipe", "name": naam, "description": desc, "recipeYield": "4 personen", "totalTime": f"PT{m['tijd']}M",
              "recipeCategory": "Hoofdgerecht", "recipeCuisine": "Nederlands", "inLanguage": "nl-NL", "recipeIngredient": ing_lijst,
              "nutrition": {"@type": "NutritionInformation", "calories": f"{m['kcal']} kcal", "servingSize": "1 persoon"},
              "isBasedOn": burl, "author": {"@type": "Organization", "name": bnaam}, "image": f"{BASE}/icons/og.png",
              "keywords": f"{kl}, goedkoop, prijs, {', '.join(wnaam(si) for si, _ in top3)}",
              "offers": {"@type": "AggregateOffer", "priceCurrency": "EUR", "lowPrice": f"{r1['tot']:.2f}", "highPrice": f"{rN['tot']:.2f}", "offerCount": len(m["rang"])}}
    recipe.pop("offers")  # Recipe ondersteunt geen offers; prijs staat in de tekst en de FAQ.
    schrijf(path, page(path, title, desc, head, body, [cld, recipe, faq_ld(faq)], actief="/maaltijden/", extra_css=MCSS, og_title=f"{naam}: {eur(r1['tot'])} bij {wnaam(s1)}"))
    made.append((path, "0.8")); maal_paden.append(path)

# ---------- overzicht ----------
if MAAL:
    goedkoopst = min(MAAL, key=lambda m: m["rang"][0][1]["tot"])
    winst = {}
    for m in MAAL: winst[m["rang"][0][0]] = winst.get(m["rang"][0][0], 0) + 1
    vaakst = max(winst, key=winst.get)
    secties = ""
    for key, titel, emo in SOORTEN:
        ms = sorted([m for m in MAAL if m["soort"] == key], key=lambda m: m["rang"][0][1]["tot"])
        if not ms: continue
        sp = SOORT_PAD.get(key)
        kop_ = f'<a href="/maaltijden/{sp[0]}/" style="text-decoration:none">{esc(titel)}</a>' if sp else esc(titel)
        secties += f'<section class="msoort" id="{key}"><h2>{emo} {kop_}</h2><ul class="mgrid">' + "".join(kaart(m) for m in ms) + "</ul></section>"
    sprong = " · ".join(f'<a href="#{k}">{esc(t)}</a>' for k, t, _ in SOORTEN if any(m["soort"] == k for m in MAAL))
    faq = [("Wat is de goedkoopste maaltijd?", f"Van de {len(MAAL)} maaltijden is {goedkoopst['naam'].lower()} het goedkoopst: {eur(goedkoopst['rang'][0][1]['tot'])} voor 4 personen bij {wnaam(goedkoopst['rang'][0][0])}, {pp(goedkoopst['rang'][0][1]['tot'])} per persoon."),
           ("Bij welke supermarkt kook je het goedkoopst?", f"{wnaam(vaakst)} is bij {winst[vaakst]} van de {len(MAAL)} maaltijden het goedkoopst. Per gerecht verschilt het, daarom staan bij elke maaltijd de 3 goedkoopste supermarkten."),
           ("Waar komen de recepten vandaan?", "Het zijn gangbare Nederlandse gerechten van bekende receptensites: Allerhande, Jumbo, Leukerecepten, 24Kitchen, Lekker en Simpel en Eef kookt zo. Bij elk gerecht staat een link naar het originele recept."),
           ("Hoe worden de calorieën berekend?", "Uit de ingrediënten van het recept, met de gemiddelde voedingswaarde per 100 gram uit de Nederlandse voedingsmiddelentabel. Het is een schatting per persoon bij 4 personen.")]
    ch, cld = crumbs(("Complete maaltijden", None))
    title = f"Goedkoop avondeten: {len(MAAL)} complete maaltijden met prijs per supermarkt ({MAAND})"
    desc = (f"Wat kost stamppot, spaghetti, nasi of een maaltijdsalade bij jouw supermarkt? {len(MAAL)} gangbare gerechten voor 4 personen met calorieën en de 3 goedkoopste supermarkten. "
            f"Vanaf {eur(goedkoopst['rang'][0][1]['tot'])}. Elke dag bijgewerkt.")
    head = (ch + f"<h1>Complete maaltijden: waar kook je het goedkoopst?</h1><p class=\"lead\">{len(MAAL)} gewone Nederlandse avondmaaltijden voor 4 personen, met calorieën en de supermarkt waar alle ingrediënten samen het minst kosten. "
            f"Goedkoopst: <a href=\"/maaltijden/{goedkoopst['slug']}/\">{esc(goedkoopst['naam'].lower())}</a> voor {eur(goedkoopst['rang'][0][1]['tot'])}.</p><p class=\"feiten\">{sprong}</p>")
    themalinks = ('<h2>Meer overzichten</h2><ul class="links"><li><a href="/maaltijden/goedkoop-avondeten/">De 10 goedkoopste maaltijden</a></li><li><a href="/maaltijden/stamppot/">Goedkope stamppotten</a></li>'
                  + "".join(f'<li><a href="/maaltijden/{v[0]}/">{esc(v[1])}</a></li>' for v in SOORT_PAD.values()) + '<li><a href="/goedkoopste-supermarkt/">Goedkoopste supermarkt</a></li><li><a href="/aanbiedingen/">Aanbiedingen van deze week</a></li></ul>')
    body = (MKJS + secties + themalinks + f'<p class="note" style="margin-top:20px">Prijzen van {DATUM}, naar gebruikte hoeveelheid, aanbiedingen inbegrepen. Olie, zout en kruiden uit de voorraadkast tellen niet mee.</p>' + faq_html(faq))
    il = {"@context": "https://schema.org", "@type": "ItemList", "name": "Complete maaltijden met prijs per supermarkt",
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE}/maaltijden/{m['slug']}/", "name": m["naam"]} for i, m in enumerate(MAAL)]}
    schrijf("/maaltijden/", page("/maaltijden/", title, desc, head, body, [cld, il, faq_ld(faq)], actief="/maaltijden/", extra_css=MCSS, og_title="Complete maaltijden: waar kook je het goedkoopst?"))
    made.append(("/maaltijden/", "0.9"))
    # Blok voor de startpagina: de 6 goedkoopste, verdeeld over de soorten.
    keuze = []
    for key, _, _ in SOORTEN:
        ms = sorted([m for m in MAAL if m["soort"] == key], key=lambda m: m["rang"][0][1]["tot"])
        keuze += ms[:2]
    keuze = sorted(keuze, key=lambda m: m["rang"][0][1]["tot"])[:6]
    MAAL_HOME = (f'<section class="wrap maal" aria-labelledby="mh"><h2 id="mh">🍽️ Complete maaltijden</h2>'
                 f'<p class="meta">Wat kost avondeten voor 4 personen? Gewone gerechten met calorieën en de goedkoopste supermarkt.</p><ul class="mgrid">'
                 + "".join(kaart(m) for m in keuze) + f'</ul><a class="cta" href="/maaltijden/">Alle {len(MAAL)} maaltijden: aardappel, pasta, rijst, salades en meer</a></section>' + MKJS)
else:
    MAAL_HOME = ""

# ---------- themapagina's ----------
def themapagina(slug_, kort, h1, title, lead, ms, faq_extra=()):
    path = f"/maaltijden/{slug_}/"
    ch, cld = crumbs(("Complete maaltijden", "/maaltijden/"), (kort, None))
    trs = "".join(f'<tr{" class=win" if i == 0 else ""} data-p="{esc(prijzen_json(m))}"><td><b><span class="rn">{i + 1}.</span> <a href="/maaltijden/{m["slug"]}/">{esc(m["naam"])}</a></b><span class="sub">{m["kcal"]} kcal per persoon · {m["tijd"]} min</span></td>'
                  f'<td class="kw">{esc(wnaam(m["rang"][0][0]))}</td><td class="p"><span class="kp">{tag(m["rang"][0][1]["tot"])}</span><br><span class="unit kpp" data-kort="1">{pp(m["rang"][0][1]["tot"])} p.p.</span></td></tr>' for i, m in enumerate(ms))
    g = ms[0]
    faq = [(f"Wat is de goedkoopste uit deze lijst?", f"{g['naam']}: {eur(g['rang'][0][1]['tot'])} voor 4 personen bij {wnaam(g['rang'][0][0])}, {pp(g['rang'][0][1]['tot'])} per persoon."), *faq_extra,
           ("Hoe actueel zijn de prijzen?", f"De prijzen worden elke dag bijgewerkt met de prijzen en aanbiedingen van de supermarkten. Deze pagina is van {DATUM}.")]
    andere = [(f"/maaltijden/{x}/", t) for x, t in [("goedkoop-avondeten", "De 10 goedkoopste maaltijden"), ("stamppot", "Goedkope stamppotten"), *SOORT_PAD.values()] if x != slug_]
    body = (f'<div class="tblwrap"><table class="ptable"><thead><tr><th>Maaltijd (4 personen)</th><th>Goedkoopst bij</th><th style="text-align:right">Prijs</th></tr></thead><tbody data-sorteer="1">{trs}</tbody></table></div>'
            f'<p class="note">Prijzen van {DATUM} voor alle ingrediënten, naar gebruikte hoeveelheid. Tik op een maaltijd voor de 3 goedkoopste supermarkten en wat elk ingrediënt kost.</p>'
            + faq_html(faq) + '<h2>Meer overzichten</h2><ul class="links">' + "".join(f'<li><a href="{h}">{esc(t)}</a></li>' for h, t in andere) + '<li><a href="/maaltijden/">Alle complete maaltijden</a></li></ul>' + MKJS)
    il = {"@context": "https://schema.org", "@type": "ItemList", "name": h1, "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE}/maaltijden/{m['slug']}/", "name": m["naam"]} for i, m in enumerate(ms)]}
    schrijf(path, page(path, title, lead_txt(lead), crumbs_head(ch, h1, lead), body, [cld, il, faq_ld(faq)], actief="/maaltijden/", og_title=h1))
    made.append((path, "0.8"))
def lead_txt(h): return re.sub(r"<[^>]+>", "", h)
def crumbs_head(ch, h1, lead): return ch + f"<h1>{esc(h1)}</h1><p class=\"lead\">{lead}</p>"
pprs = lambda m: m["rang"][0][1]["tot"]
if MAAL:
    alle = sorted(MAAL, key=pprs)
    top = alle[:10]
    themapagina("goedkoop-avondeten", "Goedkoop avondeten", "Goedkoop avondeten: de 10 goedkoopste maaltijden",
                f"Goedkoop avondeten voor 4 personen: de 10 goedkoopste maaltijden ({MAAND})",
                f"De 10 goedkoopste gewone avondmaaltijden van dit moment, voor 4 personen. Al vanaf <b>{eur(pprs(top[0]))}</b> ({pp(pprs(top[0]))} per persoon), met de supermarkt waar je het minst betaalt.", top,
                [("Hoe kook je goedkoop?", "Kies gerechten met aardappelen, rijst, pasta of peulvruchten als basis, koop groente van het seizoen en let op de aanbiedingen. Rekenen met de prijs per kilo helpt: grote verpakkingen en huismerken zijn vaak het voordeligst.")])
    st = sorted([m for m in MAAL if any(w in m["slug"] for w in ("stamppot", "hutspot", "boerenkool"))], key=pprs)
    if len(st) >= 2:
        themapagina("stamppot", "Stamppot", "Goedkope stamppot: wat kost het per supermarkt?", f"Goedkope stamppot: boerenkool, hutspot, andijvie en zuurkool vergeleken ({MAAND})",
                    f"Wat kost een stamppot voor 4 personen? {len(st)} Hollandse klassiekers met de supermarkt waar alle ingrediënten samen het goedkoopst zijn. Vanaf <b>{eur(pprs(st[0]))}</b>.", st,
                    [("Welke stamppot is het goedkoopst?", f"Nu is {st[0]['naam'].lower()} het goedkoopst: {eur(pprs(st[0]))} voor 4 personen bij {wnaam(st[0]['rang'][0][0])}.")])
    for key, (sl_, kort) in SOORT_PAD.items():
        ms = sorted([m for m in MAAL if m["soort"] == key], key=pprs)
        if len(ms) < 2: continue
        themapagina(sl_, kort, f"{kort}: goedkope maaltijden per supermarkt", f"Goedkope {kort.lower()}: {len(ms)} maaltijden met prijs per supermarkt ({MAAND})",
                    f"{len(ms)} gewone {kort.lower()} voor 4 personen, met calorieën en de supermarkt waar je het minst betaalt. Vanaf <b>{eur(pprs(ms[0]))}</b> voor het hele gerecht.", ms)
print(len(MAAL), "maaltijdpagina's")
