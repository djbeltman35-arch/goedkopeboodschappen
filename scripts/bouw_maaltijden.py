"""Pagina's voor complete maaltijden. Wordt met exec() in bouw_paginas.py gedraaid (gebruikt diens sjabloon-functies)."""
from maaltijd_kosten import MAAL, SOORTEN, NOTITIE, I

def hoev(q, eenheid_):
    if eenheid_ == "l": return f"{round(q * 1000)} ml" if q < 1 else f"{str(round(q, 2)).replace('.', ',')} liter"
    return f"{round(q * 1000)} g" if q < 1 else f"{str(round(q, 2)).replace('.', ',')} kg"
def pp(v): return eur(v / 4)

MCSS = ""
MJS = """<script>document.addEventListener("click",e=>{const b=e.target.closest(".addall");if(!b)return;let q=[];try{q=JSON.parse(localStorage.getItem("lijst-erbij")||"[]")}catch(x){}
const os=JSON.parse(b.dataset.os);for(const o of os)if(!q.some(x=>x.u===o.u))q.push(o);try{localStorage.setItem("lijst-erbij",JSON.stringify(q));b.textContent="✓ Klaar voor je lijst";b.classList.add("on");window.mark&&mark();
try{window.goatcounter&&goatcounter.count({path:"maaltijd/lijst/"+b.dataset.m,title:"Maaltijd op lijst",event:true})}catch(x){}}catch(x){b.textContent="Bewaren lukt niet in deze browser"}});</script>"""

def wnaam(si): return NAMEN.get(stores[si]["id"], stores[si]["name"])
def kaart(m):
    si, r = m["rang"][0]
    return (f'<li class="mcard"><a class="mt" href="/maaltijden/{m["slug"]}/">{esc(m["naam"])}</a>'
            f'<span class="mm">{m["kcal"]} kcal per persoon · {m["tijd"]} min · 4 personen</span>'
            f'<span class="mw">{tag(r["tot"])}<span>bij <b>{esc(wnaam(si))}</b><br><span class="mm">{pp(r["tot"])} per persoon</span></span></span></li>')

maal_paden = []
for m in MAAL:
    path = f"/maaltijden/{m['slug']}/"
    top3 = m["rang"][:3]
    (s1, r1) = top3[0]; (sN, rN) = m["rang"][-1]
    naam = m["naam"]; kl = naam[0].lower() + naam[1:]
    title = f"{naam}: wat kost het? Goedkoopst bij {wnaam(s1)} ({eur(r1['tot'])} voor 4)"
    desc = (f"{naam} voor 4 personen kost nu {eur(r1['tot'])} bij {wnaam(s1)} ({pp(r1['tot'])} per persoon), daarna {wnaam(top3[1][0])} en {wnaam(top3[2][0])}. "
            f"{m['kcal']} kcal per persoon. Prijzen van {len(m['rang'])} supermarkten, elke dag bijgewerkt.")
    ch, cld = crumbs(("Complete maaltijden", "/maaltijden/"), (naam, None))
    # top 3
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
    head = (ch + f"<h1>{esc(naam)}: waar is het goedkoopst?</h1><p class=\"lead\">Alle ingrediënten voor 4 personen kosten nu <b>{eur(r1['tot'])}</b> bij <b>{esc(wnaam(s1))}</b>. "
            f"Bij {esc(wnaam(sN))} betaal je {eur(rN['tot'] - r1['tot'])} meer.</p>"
            f'<p class="feiten"><span><b>{m["kcal"]}</b> kcal per persoon</span><span><b>{m["tijd"]}</b> minuten</span><span><b>4</b> personen</span><span>Recept: <a href="{esc(burl)}" rel="noopener" target="_blank">{esc(bnaam)}</a></span></p>')
    andere = [x for x in MAAL if x["soort"] == m["soort"] and x is not m] + [x for x in MAAL if x["soort"] != m["soort"]]
    body = (f'<h2>De 3 goedkoopste supermarkten</h2><ul class="mtop">{tops}</ul>'
            f'<h2>Wat heb je nodig?</h2><div class="tblwrap"><table class="ptable"><thead><tr><th>Ingrediënt</th>{kop}</tr></thead><tbody>{rijen}</tbody></table></div>'
            f'<p class="note">Prijzen van {DATUM}, naar gebruikte hoeveelheid: in de winkel koop je vaak een heel pak, de rest heb je over voor een volgende keer. Tik op een prijs voor het product. {esc(noot)}</p>'
            f'<h2>Bereiding</h2><p>De bereiding staat in het originele recept op <a href="{esc(burl)}" rel="noopener" target="_blank">{esc(bnaam)}</a>. Daar vind je ook de stappen en tips.</p>'
            f'<h2>Alle supermarkten</h2><div class="tblwrap"><table class="ptable"><thead><tr><th>Supermarkt</th><th style="text-align:right">4 personen</th><th style="text-align:right">Per persoon</th></tr></thead><tbody>{alle}</tbody></table></div>'
            f'<p class="note">Supermarkten waar we een ingrediënt niet online vinden, staan niet in de lijst.</p>'
            + faq_html(faq) + '<h2>Meer complete maaltijden</h2><ul class="mgrid">' + "".join(kaart(x) for x in andere[:6]) + '</ul><a class="cta" href="/maaltijden/">Alle complete maaltijden</a>' + MJS)
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
        secties += f'<section class="msoort" id="{key}"><h2>{emo} {esc(titel)}</h2><ul class="mgrid">' + "".join(kaart(m) for m in ms) + "</ul></section>"
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
    body = (secties + f'<p class="note" style="margin-top:20px">Prijzen van {DATUM}, naar gebruikte hoeveelheid, aanbiedingen inbegrepen. Olie, zout en kruiden uit de voorraadkast tellen niet mee.</p>' + faq_html(faq))
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
                 + "".join(kaart(m) for m in keuze) + f'</ul><a class="cta" href="/maaltijden/">Alle {len(MAAL)} maaltijden: aardappel, pasta, rijst, salades en meer</a></section>')
else:
    MAAL_HOME = ""
print(len(MAAL), "maaltijdpagina's")
