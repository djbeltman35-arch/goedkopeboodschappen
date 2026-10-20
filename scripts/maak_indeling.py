"""Schrijft scripts/cats.json (subcategorieën: [naam, icoon, zoektermen, hoofdgroep]) en scripts/groepen.json ([hoofdgroep, icoon]).
Hoofdgroepen hebben dezelfde namen als de categorieën van de aanbiedingen (ophalen/categorie.mjs).
Termen die bij minder dan 3 supermarkten te vinden zijn, verdwijnen vanzelf uit de site."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = [
 ("Groente en aardappelen", "🥦", [
   ("Aardappelen", "🥔", ["aardappelen kruimig", "aardappelen vastkokend", "aardappelen", "krieltjes", "zoete aardappel", "aardappelpuree"]),
   ("Uien en knoflook", "🧅", ["uien", "rode uien", "sjalotten", "knoflook bollen", "gehakte knoflook"]),
   ("Verse groente", "🥕", ["tomaten", "trostomaten", "cherrytomaten", "komkommer", "paprika rood", "paprika mix", "puntpaprika", "winterpeen", "broccoli vers",
        "bloemkool vers", "sperziebonen vers", "spinazie vers", "andijvie", "boerenkool vers", "zuurkool", "prei", "witlof", "spruitjes vers", "rode kool vers",
        "courgette", "aubergine", "champignons vers", "pompoen", "bosui", "wokgroente vers"]),
   ("Sla en rauwkost", "🥬", ["sla", "ijsbergsla", "rucola", "veldsla", "worteltjes geraspt"]),
   ("Groente in pot en blik", "🫙", ["sperziebonen in pot", "rode kool in pot", "erwten en wortelen in pot", "champignons in pot", "mais", "spinazie in pot", "rode bieten"]),
 ]),
 ("Fruit", "🍎", [
   ("Vers fruit", "🍌", ["bananen", "appels", "peren", "sinaasappels", "mandarijnen", "druiven", "aardbeien vers", "blauwe bessen vers", "kiwi", "citroenen", "avocado", "mango", "ananas", "meloen"]),
 ]),
 ("Diepvries", "❄️", [
   ("Diepvriesgroente", "🥦", ["spinazie diepvries", "broccoli diepvries", "sperziebonen diepvries", "doperwten diepvries", "bloemkool diepvries", "boerenkool diepvries", "wokgroente diepvries"]),
   ("Diepvriessnacks", "🍟", ["friet", "kroketten", "frikandellen", "bitterballen", "kipnuggets", "loempia", "kaassoufflés", "mexicano"]),
   ("Pizza", "🍕", ["pizza"]),
   ("Diepvriesvis", "🐟", ["vissticks", "lekkerbekjes", "kibbeling"]),
   ("Diepvriesfruit", "🍓", ["aardbeien diepvries", "blauwe bessen diepvries", "frambozen diepvries"]),
   ("IJs", "🍦", ["ijs in bak", "ijsjes multipack"]),
 ]),
 ("Brood en ontbijt", "🍞", [
   ("Brood", "🍞", ["volkoren brood", "wit brood", "bruin brood", "stokbrood", "krentenbollen", "croissants", "pannenkoeken"]),
   ("Crackers, beschuit en ontbijtkoek", "🍘", ["beschuit", "crackers", "knackebrod", "rijstwafels", "ontbijtkoek"]),
   ("Ontbijtgranen", "🥣", ["cornflakes", "havermout", "muesli", "cruesli", "granola"]),
 ]),
 ("Broodbeleg", "🥜", [
   ("Zoet beleg", "🍯", ["pindakaas", "hagelslag", "chocoladevlokken", "vruchtenhagel", "jam", "appelstroop", "chocoladepasta", "hazelnootpasta", "speculoospasta", "honing"]),
 ]),
 ("Zuivel en eieren", "🥛", [
   ("Melk", "🥛", ["halfvolle melk", "volle melk", "magere melk", "karnemelk", "chocolademelk", "havermelk", "sojamelk"]),
   ("Yoghurt, kwark en vla", "🥣", ["yoghurt", "griekse yoghurt", "kwark", "skyr", "vla"]),
   ("Room", "🍶", ["slagroom", "kookroom", "creme fraiche"]),
   ("Boter en margarine", "🧈", ["roomboter", "margarine", "halvarine"]),
   ("Eieren", "🥚", ["eieren"]),
 ]),
 ("Kaas", "🧀", [
   ("Hollandse kaas", "🧀", ["jonge kaas", "jong belegen kaas", "belegen kaas", "oude kaas", "plakken kaas", "geraspte kaas"]),
   ("Smeer- en roomkaas", "🫕", ["smeerkaas", "roomkaas"]),
   ("Buitenlandse kaas", "🧀", ["mozzarella", "feta", "brie", "parmigiano", "grana padano"]),
 ]),
 ("Vleeswaren en tapas", "🥓", [
   ("Vleeswaren", "🥪", ["ham", "kipfilet beleg", "salami", "leverworst", "boterhamworst", "cervelaat", "filet americain", "rookvlees"]),
   ("Tapas", "🫒", ["olijven", "hummus"]),
 ]),
 ("Vlees en vis", "🍗", [
   ("Kip", "🍗", ["kipfilet", "kipdijfilet", "kippendijen", "kipdrumsticks", "kipgehakt"]),
   ("Gehakt en burgers", "🍔", ["gehakt", "rundergehakt", "half om half gehakt", "gehaktballen", "hamburgers"]),
   ("Varken en rund", "🥩", ["speklappen", "spekreepjes", "spekblokjes", "varkenshaas", "biefstuk", "shoarma"]),
   ("Worst", "🌭", ["rookworst", "braadworst"]),
   ("Vis", "🐟", ["zalmfilet", "gerookte zalm", "tonijn in water", "tonijn in olie", "kabeljauw", "garnalen", "haring", "makreel"]),
 ]),
 ("Pasta, rijst en wereldkeuken", "🍝", [
   ("Rijst", "🍚", ["rijst", "basmati rijst", "pandan rijst", "zilvervliesrijst"]),
   ("Pasta", "🍝", ["spaghetti", "macaroni", "penne", "fusilli", "lasagne"]),
   ("Wereldkeuken", "🌍", ["noedels", "mie", "couscous", "tortilla wraps"]),
 ]),
 ("Soep, conserven en bakken", "🥫", [
   ("Soep", "🍲", ["soep"]),
   ("Tomaat in blik en pak", "🍅", ["tomatenpuree", "passata", "tomatenblokjes"]),
   ("Peulvruchten en appelmoes", "🫘", ["kidneybonen", "kikkererwten", "linzen", "appelmoes"]),
   ("Bakken", "🧁", ["tarwebloem", "suiker"]),
 ]),
 ("Sauzen, olie en kruiden", "🧂", [
   ("Sauzen", "🥫", ["pastasaus", "pesto", "mayonaise", "fritessaus", "ketchup", "curry", "mosterd", "satesaus", "knoflooksaus", "barbecuesaus", "slasaus"]),
   ("Oosterse sauzen", "🌶️", ["sambal", "ketjap", "sojasaus"]),
   ("Olie en bakboter", "🫒", ["olijfolie", "zonnebloemolie", "bakboter"]),
   ("Kruiden en bouillon", "🧂", ["keukenzout", "peper", "bouillonblokjes"]),
 ]),
 ("Koffie en thee", "☕", [
   ("Koffie", "☕", ["koffiebonen", "filterkoffie", "koffiepads", "koffiecups", "koffiecups dolce gusto", "oploskoffie"]),
   ("Thee", "🍵", ["zwarte thee", "groene thee", "rooibos thee", "pepermuntthee", "kamillethee", "vruchtenthee"]),
 ]),
 ("Frisdrank en sap", "🥤", []),   # gevuld uit varianten.json
 ("Bier en wijn", "🍺", []),
 ("Koek en snoep", "🍫", [
   ("Chocolade", "🍫", ["chocolade reep", "melkchocolade", "pure chocolade"]),
   ("Snoep en drop", "🍬", ["drop", "winegums", "snoep"]),
   ("Koek", "🍪", ["eierkoeken", "stroopwafels", "koekjes", "speculaas", "biscuits"]),
 ]),
 ("Chips en noten", "🥨", [
   ("Chips en popcorn", "🥔", ["naturel chips", "paprika chips", "chips", "tortilla chips", "popcorn"]),
   ("Noten", "🥜", ["pinda", "nootjes", "cashewnoten"]),
 ]),
 ("Huishouden", "🧻", [
   ("Wassen", "🧺", ["wasmiddel vloeibaar", "waspoeder", "wascapsules", "wasverzachter"]),
   ("Afwassen", "🍽️", ["vaatwastabletten", "afwasmiddel"]),
   ("Schoonmaken", "🧽", ["allesreiniger", "wc reiniger", "schoonmaakazijn"]),
   ("Papier", "🧻", ["toiletpapier", "keukenrol", "tissues"]),
   ("Zakken, folie en batterijen", "🗑️", ["vuilniszakken", "aluminiumfolie", "vershoudfolie", "batterijen"]),
 ]),
 ("Verzorging en baby", "🧴", [
   ("Mond", "🪥", ["tandpasta", "tandenborstel"]),
   ("Haar", "🧴", ["shampoo", "conditioner"]),
   ("Lichaam", "🧼", ["douchegel", "zeep", "handzeep", "deodorant", "bodylotion", "zonnebrand", "scheermesjes"]),
   ("Maandverband en tampons", "🩸", ["maandverband", "tampons", "inlegkruisjes"]),
   ("Baby", "👶", ["luiers", "billendoekjes"]),
 ]),
 ("Huisdieren", "🐾", [
   ("Kat", "🐈", ["kattenvoer", "kattenbrokken", "kattenbakvulling"]),
   ("Hond", "🐕", ["hondenvoer", "hondenbrokken", "hondensnacks"]),
 ]),
]
V = json.load(open(os.path.join(ROOT, "scripts", "varianten.json")))
def met(*pref): return [k for k in V if k.startswith(pref)]
DRANK = {
 "Frisdrank en sap": [
   ("Cola", "🥤", met("Coca-Cola fles", "Coca-Cola flesje", "Coca-Cola los", "Coca-Cola sixpack", "Coca-Cola blikjes", "Coca-Cola mini", "Coca-Cola flessen", "Pepsi ", "Cola (alle merken)")),
   ("Cola zero en light", "🥤", met("Coca-Cola Zero", "Cola zero en light")),
   ("Overige frisdrank", "🍊", met("Sinas", "7up", "Ice tea") + ["limonade siroop"]),
   ("Water", "💧", met("Spa ", "Bruisend water", "Water ")),
   ("Sap", "🧃", ["sinaasappelsap", "appelsap", "multivitaminesap"]),
   ("Energiedrank", "⚡", met("Energiedrank")),
 ],
 "Bier en wijn": [
   ("Bier", "🍺", met("Pils")),
   ("Alcoholvrij bier", "🍺", met("Alcoholvrij bier")),
   ("Wijn", "🍷", ["rode wijn", "witte wijn", "rose"]),
 ]}
cats, groepen = [], []
for g, ic, subs in G:
    groepen.append([g, ic])
    for naam, sic, terms in (subs or DRANK[g]):
        cats.append([naam, sic, terms, g])
json.dump(cats, open(os.path.join(ROOT, "scripts", "cats.json"), "w"), ensure_ascii=False, indent=1)
json.dump(groepen, open(os.path.join(ROOT, "scripts", "groepen.json"), "w"), ensure_ascii=False, indent=1)
print(len(groepen), "groepen,", len(cats), "subcategorieën,", sum(len(c[2]) for c in cats), "termen")
