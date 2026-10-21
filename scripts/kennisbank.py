# Kennisbank: korte, duidelijke uitlegartikelen over slim boodschappen doen.
# Wordt vanuit bouw_paginas.py uitgevoerd (exec), dus page(), crumbs(), schrijf() enz. zijn beschikbaar.
_g = globals()
_huis_pct = round(statistics.median(v[3] for v in _g["_huis_vb"]) * 100) if _g.get("_huis_vb") else 30
_pp_week = eur(bedrag(1, lo[1])) if all(k in _g for k in ("bedrag", "lo")) else None

def _l(href, tekst): return f'<a href="{href}">{tekst}</a>'

KB = [
 ("prijs-per-kilo", "Prijs per kilo of liter: zo vergelijk je eerlijk", "📏",
  "Een groot pak lijkt duur, maar is vaak goedkoper. Kijk daarom naar de prijs per kilo of liter.",
  [("Waarom de prijs per kilo?", "<p>Verpakkingen verschillen in grootte. Een pak van 500 gram voor € 2 is even duur als een pak van 1 kilo voor € 4. De prijs per kilo laat dat meteen zien.</p>"),
   ("Zo reken je het uit", "<p>Deel de prijs door het gewicht in kilo. Voorbeeld: € 1,80 voor 300 gram is € 1,80 ÷ 0,3 = <b>€ 6 per kilo</b>.</p><p>Bij drinken deel je door het aantal liter. Bij wc-papier of eieren kijk je naar de prijs per stuk.</p>"),
   ("Let op bij grote pakken", "<p>Groot is niet altijd goedkoper. Soms is een aanbieding op een klein pak voordeliger. En koop alleen groot als je het ook opmaakt.</p>")],
  [("Waar staat de prijs per kilo?", "In de winkel staat hij klein op het prijskaartje. Op deze site staat bij elk product de prijs per kilo, liter of stuk."),
   ("Is een grote verpakking altijd goedkoper?", "Nee. Meestal wel, maar niet altijd. Vergelijk daarom de prijs per kilo of liter.")],
  [("/", "Vergelijk je boodschappen"), ("/vergelijk/", "Alle producten")]),
 ("huismerk-of-a-merk", "Huismerk of A-merk: wat is het verschil?", "🏷️",
  f"Huismerken zijn vandaag gemiddeld {_huis_pct}% goedkoper dan A-merken. Vaak is de kwaliteit vergelijkbaar.",
  [("Wat is een huismerk?", "<p>Een huismerk is het eigen merk van de supermarkt, zoals AH, Jumbo, G’woon of 1 de Beste. Een A-merk is een bekend merk, zoals Calvé, Coca-Cola of Lay’s.</p>"),
   ("Waarom is een huismerk goedkoper?", "<p>De supermarkt hoeft weinig reclame te maken. Ook worden huismerken vaak in dezelfde fabrieken gemaakt als A-merken.</p>"),
   ("Is een huismerk slechter?", "<p>Niet per se. De Consumentenbond vindt huismerken in tests regelmatig even goed of beter. De smaak kan wel verschillen. Probeer het gewoon eens.</p>")],
  [("Hoeveel bespaar je met huismerken?", f"Vandaag gemiddeld {_huis_pct}% per kilo of liter. Per product verschilt het."),
   ("Welke huismerken zijn er?", "Bijvoorbeeld AH, Jumbo, PLUS, Spar, G’woon (Hoogvliet, DekaMarkt), 1 de Beste (Dirk) en de eigen merken van Lidl en Aldi.")],
  [("/huismerk-of-a-merk/", "Huismerk of A-merk per product vergeleken")]),
 ("aanbiedingen-uitgelegd", "1+1 gratis, 2e halve prijs: hoeveel korting is het echt?", "🔥",
  "Niet elke actie is evenveel waard. Hier zie je in één oogopslag hoeveel korting je echt krijgt.",
  [("Korting per actie", '<div class="tblwrap"><table class="ptable"><thead><tr><th>Actie</th><th style="text-align:right">Echte korting</th></tr></thead><tbody>'
    "<tr><td>1+1 gratis</td><td class=p><b>50%</b></td></tr><tr><td>2+1 gratis</td><td class=p><b>33%</b></td></tr><tr><td>3+1 gratis</td><td class=p><b>25%</b></td></tr>"
    "<tr><td>2e halve prijs</td><td class=p><b>25%</b></td></tr><tr><td>2 voor de prijs van 1,5</td><td class=p><b>25%</b></td></tr><tr><td>2e gratis bij 3 stuks (3 voor 2)</td><td class=p><b>33%</b></td></tr></tbody></table></div>"
    "<p class=note>De korting geldt alleen als je het volle aantal koopt.</p>"),
   ("Is een aanbieding altijd goedkoper?", "<p>Nee. Soms is hetzelfde product bij een andere supermarkt zonder actie nog goedkoper. Of een huismerk is goedkoper dan het A-merk in de aanbieding. Daarom tonen wij bij aanbiedingen of het een <b>echte korting</b> is.</p>"),
   ("Slim omgaan met acties", "<ul><li>Koop alleen wat je echt gebruikt.</li><li>Let op de houdbaarheid bij 1+1 gratis.</li><li>Sla houdbare producten in als ze in de aanbieding zijn.</li></ul>")],
  [("Hoeveel is 1+1 gratis?", "50% korting, als je er twee koopt."), ("Hoeveel is 2e halve prijs?", "25% korting op het totaal, als je er twee koopt.")],
  [("/aanbiedingen/", "Aanbiedingen van deze week")]),
 ("weekmenu-maken", "Een weekmenu maken: zo bespaar je tijd en geld", "📅",
  "Met een weekmenu doe je één keer boodschappen en gooi je minder weg.",
  [("Waarom een weekmenu?", "<ul><li>Je koopt alleen wat je nodig hebt.</li><li>Ingrediënten die in meer gerechten zitten, koop je één keer.</li><li>Je hoeft niet elke dag na te denken over eten.</li></ul>"),
   ("Zo maak je een weekmenu", "<ol><li>Kijk wat je nog in huis hebt.</li><li>Kies 5 tot 7 gerechten. Wissel af: aardappels, pasta, rijst.</li><li>Maak één boodschappenlijst.</li><li>Kijk welke supermarkt voor die lijst het goedkoopst is.</li></ol>"),
   ("Liever kant-en-klaar?", f"<p>Wij maken elke dag een {_l('/maaltijden/weekmenu/', 'goedkoop weekmenu met boodschappenlijst')}. Er zijn ook weekmenu’s voor glutenvrij, vegan, halal en meer.</p>")],
  [("Hoeveel bespaar je met een weekmenu?", "Je koopt minder los en gooit minder weg. Dat scheelt al snel tientallen euro’s per maand."),
   ("Wat zijn goedkope gerechten?", "Stamppot, pasta, rijst met groente, soep en ovenschotels met aardappel zijn vaak het goedkoopst.")],
  [("/maaltijden/weekmenu/", "Goedkoop weekmenu"), ("/maaltijden/goedkoop-avondeten/", "De 10 goedkoopste maaltijden")]),
 ("klein-budget", "Boodschappen doen met een klein budget", "💶",
  "Weinig geld voor boodschappen? Met deze stappen kom je verder." + (f" Zuinig eten kan nu al vanaf {_pp_week} per persoon per week." if _pp_week else ""),
  [("1. Weet wat je uitgeeft", "<p>Schrijf een week lang op wat je aan boodschappen uitgeeft. Dan weet je waar je kunt besparen.</p>"),
   ("2. Maak een lijst en houd je eraan", "<p>Zonder lijst koop je meer. Zet alles op je lijst en koop niets extra.</p>"),
   ("3. Kies de goedkoopste winkel voor jouw lijst", f"<p>Elke supermarkt is ergens goedkoop in. {_l('/', 'Vergelijk je eigen lijst')} en zie waar je het minst betaalt.</p>"),
   ("4. Kies huismerken en basisproducten", "<p>Huismerken, aardappels, rijst, pasta, peulvruchten en seizoensgroente zijn goedkoop en voedzaam.</p>"),
   ("5. Kook zelf en vries in", "<p>Kook voor meer dagen en vries porties in. Kant-en-klaar is bijna altijd duurder.</p>"),
   ("Hulp nodig?", "<p>Kom je niet rond? Je gemeente kan helpen, bijvoorbeeld met gratis budgetcoaching of schuldhulpverlening. Ook de Voedselbank kan helpen als het echt niet lukt.</p>")],
  [("Hoeveel geld heb je nodig voor boodschappen?", f"Zuinig eten kost nu ongeveer {_pp_week} per persoon per week bij de goedkoopste supermarkt." if _pp_week else "Dat hangt af van je huishouden. Bekijk onze pagina over boodschappen per week."),
   ("Waar vind ik hulp bij geldzorgen?", "Bij je gemeente. Die biedt gratis hulp, zoals budgetcoaching en schuldhulpverlening.")],
  [("/boodschappen-per-week/", "Wat kosten boodschappen per week?"), ("/eten-voor-50-euro-per-week/", "Eten voor 50 euro per week"), ("/voor-hulpverleners/", "Voor budgetcoaches en hulpverleners")]),
 ("tht-en-tgt", "THT en TGT: wat is het verschil?", "📆",
  "Veel eten wordt weggegooid terwijl het nog goed is. Het verschil tussen THT en TGT helpt je besparen.",
  [("Tenminste houdbaar tot (THT)", "<p>Na deze datum is het product meestal nog goed. Kijk, ruik en proef. Denk aan rijst, pasta, koek en conserven.</p>"),
   ("Te gebruiken tot (TGT)", "<p>Na deze datum niet meer eten. Dit staat op bederfelijke producten zoals vers vlees, vis en sommige zuivel.</p>"),
   ("Zo gooi je minder weg", "<ul><li>Zet nieuwe boodschappen achter de oude.</li><li>Vries brood, vlees en restjes op tijd in.</li><li>Koop niet meer dan je nodig hebt.</li></ul>")],
  [("Mag je eten na de THT-datum?", "Meestal wel. Kijk, ruik en proef eerst."), ("Mag je eten na de TGT-datum?", "Nee, dat kan ongezond zijn.")],
  [("/besparen/", "Meer bespaartips")]),
 ("statiegeld", "Statiegeld: hoeveel krijg je terug?", "♻️",
  "Op flessen en blikjes betaal je statiegeld. Lever ze in, dan krijg je het terug.",
  [("Hoeveel statiegeld?", '<div class="tblwrap"><table class="ptable"><tbody><tr><td>Blikje</td><td class=p><b>€ 0,15</b></td></tr><tr><td>Plastic fles tot 1 liter</td><td class=p><b>€ 0,15</b></td></tr><tr><td>Plastic fles groter dan 1 liter</td><td class=p><b>€ 0,25</b></td></tr><tr><td>Glazen bierflesje</td><td class=p><b>€ 0,10</b></td></tr><tr><td>Bierkrat (met flesjes)</td><td class=p><b>€ 3,90</b></td></tr></tbody></table></div>'),
   ("Waar lever je ze in?", "<p>Bij bijna elke supermarkt, in de inleverautomaat. Je krijgt een bon die je bij de kassa verrekent.</p>"),
   ("Telt statiegeld mee in de prijs?", "<p>Op deze site vergelijken we de prijs zonder statiegeld, zoals de supermarkten die tonen. Je krijgt het statiegeld terug als je inlevert.</p>")],
  [("Hoeveel statiegeld op een blikje?", "15 cent."), ("Hoeveel statiegeld op een grote fles?", "25 cent voor plastic flessen groter dan 1 liter.")],
  [("/categorie/frisdrank-en-sap/", "Frisdrank en sap vergelijken")]),
 ("seizoensgroente", "Seizoensgroente: wat is nu goedkoop?", "🥕",
  "Groente uit het seizoen is vaak goedkoper en lekkerder. Hier zie je wat er per seizoen veel is.",
  [("Lente (maart – mei)", "<p>Asperges, spinazie, radijs, rabarber, bosui.</p>"),
   ("Zomer (juni – augustus)", "<p>Tomaten, komkommer, courgette, sperziebonen, paprika, aardbeien.</p>"),
   ("Herfst (september – november)", "<p>Pompoen, champignons, rode kool, prei, appels, peren.</p>"),
   ("Winter (december – februari)", "<p>Boerenkool, zuurkool, spruitjes, winterpeen, knolselderij, witlof.</p>"),
   ("Tip", "<p>Diepvriesgroente is het hele jaar goedkoop en net zo gezond. Handig als iets niet in het seizoen is.</p>")],
  [("Waarom is seizoensgroente goedkoper?", "Er is dan veel van, en het hoeft niet van ver te komen of in een kas te groeien."),
   ("Is diepvriesgroente gezond?", "Ja. Het wordt vers ingevroren en houdt zijn vitamines goed.")],
  [("/categorie/groente-en-aardappelen/", "Groente en aardappelen vergelijken")]),
 ("dieet-op-het-etiket", "Glutenvrij, lactosevrij, vegan, halal: wat betekent het?", "🔎",
  "Wat betekenen de woorden op de verpakking? Kort uitgelegd.",
  [("Glutenvrij", "<p>Zonder gluten uit tarwe, rogge en gerst. Belangrijk bij coeliakie. Glutenvrij betekent hoogstens 20 mg gluten per kilo.</p>"),
   ("Lactosevrij", "<p>Zonder melksuiker. Het is wel gewoon koemelk. Niet geschikt bij een koemelkallergie.</p>"),
   ("Vegan", "<p>Helemaal plantaardig: geen vlees, vis, melk, ei of honing. Ook geschikt bij een koemelk- of ei-allergie, maar check ‘kan sporen bevatten’.</p>"),
   ("Vegetarisch", "<p>Geen vlees en vis, maar wel melk en ei.</p>"),
   ("Halal", "<p>Toegestaan volgens de islam: geen varkensvlees en geen alcohol. Vlees moet halal geslacht zijn.</p>"),
   ("Koosjer", "<p>Volgens de joodse spijswetten: geen varkensvlees of schaaldieren, en vlees en zuivel niet samen.</p>")],
  [("Is lactosevrij hetzelfde als zuivelvrij?", "Nee. Lactosevrije melk is koemelk zonder melksuiker. Zuivelvrij betekent helemaal zonder melk."),
   ("Is vegan ook glutenvrij?", "Nee, niet vanzelf. Vegan brood bevat bijvoorbeeld vaak gluten.")],
  [("/dieet/", "Dieet en leefstijl"), ("/allergie/", "Boodschappen bij een allergie")]),
 ("goedkoopste-supermarkt-uitleg", "Welke supermarkt is het goedkoopst?", "🏆",
  "Dat hangt af van wat je koopt. Elke supermarkt is ergens goedkoop in.",
  [("Geen vaste winnaar", "<p>De ene winkel is goedkoop in zuivel, de andere in vlees of drinken. Daarom verschilt de goedkoopste winkel per boodschappenlijst.</p>"),
   ("Zo vind je jouw goedkoopste winkel", f"<ol><li>Zet je vaste boodschappen op je lijst.</li><li>Kies de winkels bij jou in de buurt.</li><li>Zie welke winkel voor jouw lijst het goedkoopst is.</li></ol><p>{_l('/', 'Probeer het nu')}.</p>"),
   ("Ons vaste mandje", f"<p>Elke maand vergelijken we een vast mandje met dezelfde producten. {_l('/goedkoopste-supermarkt/', 'Bekijk de uitslag')}.</p>")],
  [("Is Lidl of Aldi altijd het goedkoopst?", "Vaak wel voor basisproducten, maar niet altijd. Andere winkels hebben soms goedkopere huismerken of aanbiedingen."),
   ("Krijgt een supermarkt een betere plek als hij betaalt?", "Nee. Geen enkele supermarkt betaalt voor een plek. De volgorde is puur uitgerekend.")],
  [("/goedkoopste-supermarkt/", "Goedkoopste supermarkt van deze maand"), ("/zo-vergelijken-wij/", "Zo vergelijken wij")]),
 ("invriezen", "Invriezen: zo bespaar je op boodschappen", "🧊",
  "Met de vriezer gooi je minder weg en kun je aanbiedingen slim gebruiken.",
  [("Wat kun je goed invriezen?", "<ul><li>Brood (in plakken)</li><li>Vlees en vis, zo vers mogelijk</li><li>Soep, saus en restjes</li><li>Geraspte kaas</li><li>Gesneden groente en fruit</li></ul>"),
   ("Wat kun je beter niet invriezen?", "<ul><li>Sla en komkommer</li><li>Gekookte aardappelen (worden melig)</li><li>Rauwe eieren in de schaal</li></ul>"),
   ("Tips", "<ul><li>Schrijf de datum op de zak.</li><li>Vries plat in: dat ontdooit sneller.</li><li>Ontdooi vlees in de koelkast.</li></ul>")],
  [("Hoe lang kun je vlees invriezen?", "Meestal 3 tot 6 maanden. Gehakt korter, ongeveer 3 maanden."),
   ("Mag je ontdooid eten opnieuw invriezen?", "Rauw ontdooid vlees niet. Als je het eerst kookt, mag het gerecht wel weer de vriezer in.")],
  [("/besparen/", "Meer bespaartips"), ("/maaltijden/", "Goedkope maaltijden")]),
]

ch, cld = crumbs(("Kennisbank", None))
_kb_body = '<p><a href="/kennisbank/wanneer-nieuwe-aanbiedingen/"><b>📅 Wanneer beginnen de nieuwe aanbiedingen?</b></a> Per supermarkt de startdag van de folder.</p><ul class="alkaart">' + "".join(f'<li><p class="alkop">{ic} <a href="/kennisbank/{sl}/"><b>{esc(t)}</b></a></p><p class="sub">{esc(i)}</p></li>' for sl, t, ic, i, *_ in KB) + '</ul>'
schrijf("/kennisbank/", page("/kennisbank/", "Kennisbank: slim en goedkoop boodschappen doen",
    "Korte uitleg over slim boodschappen doen: prijs per kilo, huismerk of A-merk, aanbiedingen, weekmenu, klein budget, THT en TGT, statiegeld en meer.",
    ch + "<h1>Kennisbank</h1><p class=\"lead\">Korte uitleg over slim en goedkoop boodschappen doen.</p>", _kb_body,
    [cld, {"@context": "https://schema.org", "@type": "ItemList", "name": "Kennisbank", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{BASE}/kennisbank/{k[0]}/", "name": k[1]} for i, k in enumerate(KB)]}]))
made.append(("/kennisbank/", "0.7"))
for sl, titel, ic, intro, secties, faq, links in KB:
    path = f"/kennisbank/{sl}/"
    ch, cld = crumbs(("Kennisbank", "/kennisbank/"), (titel.split(":")[0], None))
    body = "".join(f"<h2>{esc(h)}</h2>{b}" for h, b in secties)
    body += ('<h2>Handig</h2><ul class="links">' + "".join(f'<li><a href="{h}">{esc(t)}</a></li>' for h, t in links) + "</ul>") if links else ""
    andere = [k for k in KB if k[0] != sl][:4]
    body += faq_html(faq) + '<h2>Meer uitleg</h2><ul class="links">' + "".join(f'<li><a href="/kennisbank/{k[0]}/">{k[2]} {esc(k[1])}</a></li>' for k in andere) + '<li><a href="/kennisbank/">Alle artikelen</a></li></ul>'
    art = {"@context": "https://schema.org", "@type": "Article", "headline": titel, "description": intro, "inLanguage": "nl-NL",
           "author": {"@type": "Person", "name": "Erik"}, "publisher": {"@type": "Organization", "name": "Goedkope Boodschappen", "url": BASE},
           "dateModified": datetime.date.today().isoformat(), "mainEntityOfPage": f"{BASE}{path}"}
    desc = intro if len(intro) >= 110 else intro + " " + faq[0][1]
    desc = desc if len(desc) <= 158 else desc[:desc.rfind(" ", 0, 150)] + "…"
    schrijf(path, page(path, titel, desc, ch + f"<h1>{ic} {esc(titel)}</h1><p class=\"lead\">{esc(intro)}</p>", body, [cld, art, faq_ld(faq)]))
    made.append((path, "0.6"))
print("/kennisbank/:", len(KB), "artikelen")

# ---------- Wanneer beginnen de nieuwe aanbiedingen? (uitgerekend uit de echte einddatums) ----------
import collections as _col
_DAG = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
_start = {}
for _o in OFFERS:
    if _o.get("t"):
        try: _start.setdefault(_o["s"], _col.Counter())[(datetime.date.fromisoformat(_o["t"]).weekday() + 1) % 7] += 1
        except Exception: pass
_rij = [(w, c.most_common(1)[0][0]) for w, c in _start.items() if sum(c.values()) >= 10]
_rij.sort(key=lambda x: (x[1], NAMEN.get(x[0], x[0])))
if _rij:
    path = "/kennisbank/wanneer-nieuwe-aanbiedingen/"
    ch, cld = crumbs(("Kennisbank", "/kennisbank/"), ("Wanneer nieuwe aanbiedingen?", None))
    _tab = ('<div class="tblwrap"><table class="ptable"><thead><tr><th>Supermarkt</th><th>Nieuwe acties op</th></tr></thead><tbody>'
            + "".join(f'<tr><td><a href="/aanbiedingen/{w}/"><b>{esc(NAMEN.get(w, w))}</b></a></td><td>{_DAG[d]}</td></tr>' for w, d in _rij) + "</tbody></table></div>")
    _faq = [(f"Wanneer begint de nieuwe {'AH Bonus' if w == 'ah' else NAMEN.get(w, w) + ' folder'}?", f"De nieuwe weekacties van {NAMEN.get(w, w)} beginnen op {_DAG[d]}. Dat zien we aan de einddatums van de huidige acties.") for w, d in _rij[:6]]
    _faq.append(("Kan ik de aanbiedingen van volgende week al zien?", "Ja, zodra de supermarkt ze online zet. Albert Heijn doet dat meestal op vrijdag. Op onze pagina's 'volgende week' per supermarkt staan ze dan meteen."))
    _body = (_tab + '<p class="note">Uitgerekend uit de einddatums van alle aanbiedingen van deze week. Sommige acties lopen korter of langer.</p>'
             + '<h2>Aanbiedingen van volgende week</h2><ul class="links">' + "".join(f'<li><a href="/aanbiedingen/{w}/volgende-week/">{"AH Bonus" if w == "ah" else esc(NAMEN.get(w, w)) + " folder"} volgende week</a></li>' for w, d in _rij) + "</ul>"
             + faq_html(_faq))
    schrijf(path, page(path, "Wanneer beginnen de nieuwe aanbiedingen? Per supermarkt",
        "Op welke dag beginnen de nieuwe aanbiedingen van AH, Jumbo, Lidl, Aldi, Dirk en de andere supermarkten? Per supermarkt de startdag van de nieuwe folder.",
        ch + "<h1>📅 Wanneer beginnen de nieuwe aanbiedingen?</h1><p class=\"lead\">Per supermarkt de dag waarop de nieuwe folder begint.</p>", _body, [cld, faq_ld(_faq)]))
    made.append((path, "0.7"))
    print("/kennisbank/wanneer-nieuwe-aanbiedingen/:", _rij)
