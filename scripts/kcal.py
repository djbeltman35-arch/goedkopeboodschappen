"""Calorieën per product: gemiddelde richtwaarden in kcal per 100 g of 100 ml (afgerond, naar de Nederlandse
voedingsmiddelentabel NEVO en etiketten van gangbare producten). Per merk kan het iets verschillen.
Gebruik: from kcal import kcal_van; kcal_van("halfvolle melk") -> (46, "100 ml") of None (non-food)."""

G, ML = "100 g", "100 ml"
K = {
 # groente en aardappelen
 "aardappelen": 77, "krieltjes": 77, "zoete aardappel": 86, "aardappelpuree": 85, "uien": 40, "rode uien": 40, "sjalotten": 72,
 "knoflook bollen": 149, "gehakte knoflook": 120, "tomaten": 18, "trostomaten": 18, "cherrytomaten": 20, "komkommer": 13, "paprika rood": 31,
 "paprika mix": 28, "puntpaprika": 31, "winterpeen": 35, "broccoli": 34, "bloemkool": 25, "sperziebonen": 31, "sperziebonen in pot": 22,
 "spinazie": 23, "spinazie in pot": 20, "andijvie": 17, "boerenkool": 49, "zuurkool": 19, "prei": 31, "witlof": 17, "spruitjes": 43,
 "rode kool": 31, "rode kool in pot": 50, "courgette": 17, "aubergine": 25, "champignons": 22, "champignons in pot": 20, "pompoen": 26,
 "bosui": 32, "wokgroente": 30, "sla": 15, "ijsbergsla": 14, "rucola": 25, "veldsla": 21, "rode bieten": 43, "erwten en wortelen in pot": 50,
 "mais": 80, "doperwten": 75, "worteltjes geraspt": 35,
 # fruit
 "bananen": 89, "appels": 52, "peren": 57, "sinaasappels": 47, "mandarijnen": 53, "druiven": 69, "aardbeien": 32, "blauwe bessen": 57,
 "kiwi": 61, "citroenen": 29, "avocado": 160, "mango": 60, "ananas": 50, "meloen": 34, "frambozen": 52,
 # diepvries
 "friet": 150, "kroketten": 240, "frikandellen": 240, "bitterballen": 270, "kipnuggets": 250, "loempia": 210, "kaassoufflés": 300,
 "mexicano": 250, "pizza": 250, "vissticks": 200, "lekkerbekjes": 220, "kibbeling": 230, "ijs in bak": 200, "ijsjes multipack": 250,
 # brood en ontbijt
 "volkoren brood": 230, "wit brood": 260, "bruin brood": 245, "stokbrood": 260, "krentenbollen": 270, "croissants": 410, "pannenkoeken": 200,
 "beschuit": 400, "crackers": 420, "knackebrod": 360, "rijstwafels": 385, "ontbijtkoek": 330, "cornflakes": 375, "havermout": 370,
 "muesli": 400, "cruesli": 450, "granola": 450,
 # beleg
 "pindakaas": 600, "hagelslag": 525, "chocoladevlokken": 530, "vruchtenhagel": 400, "jam": 250, "appelstroop": 280, "chocoladepasta": 540,
 "hazelnootpasta": 540, "speculoospasta": 580, "honing": 320,
 # zuivel
 "halfvolle melk": (46, ML), "volle melk": (63, ML), "magere melk": (35, ML), "karnemelk": (30, ML), "chocolademelk": (70, ML),
 "havermelk": (45, ML), "sojamelk": (39, ML), "yoghurt": 50, "griekse yoghurt": 110, "kwark": 60, "skyr": 63, "vla": 100,
 "slagroom": (340, ML), "kookroom": (200, ML), "creme fraiche": 300, "roomboter": 740, "margarine": 720, "halvarine": 350, "eieren": 140,
 # kaas
 "jonge kaas": 360, "jong belegen kaas": 365, "belegen kaas": 370, "oude kaas": 405, "plakken kaas": 360, "geraspte kaas": 370,
 "smeerkaas": 260, "roomkaas": 230, "mozzarella": 250, "feta": 270, "brie": 330, "parmigiano": 400, "grana padano": 400,
 # vleeswaren en tapas
 "ham": 110, "kipfilet beleg": 105, "salami": 430, "leverworst": 290, "boterhamworst": 240, "cervelaat": 430, "filet americain": 280,
 "rookvlees": 120, "olijven": 140, "hummus": 300,
 # vlees en vis
 "kipfilet": 110, "kipdijfilet": 160, "kippendijen": 200, "kipdrumsticks": 180, "kipgehakt": 150, "gehakt": 230, "rundergehakt": 200,
 "half om half gehakt": 230, "gehaktballen": 230, "hamburgers": 230, "speklappen": 280, "spekreepjes": 300, "spekblokjes": 300,
 "varkenshaas": 110, "biefstuk": 120, "shoarma": 200, "rookworst": 300, "braadworst": 270, "zalmfilet": 180, "gerookte zalm": 190,
 "tonijn in water": 110, "tonijn in olie": 200, "kabeljauw": 80, "garnalen": 80, "haring": 190, "makreel": 300,
 # pasta en rijst (ongekookt)
 "rijst": 350, "basmati rijst": 350, "pandan rijst": 350, "zilvervliesrijst": 350, "spaghetti": 350, "macaroni": 350, "penne": 350,
 "fusilli": 350, "lasagne": 350, "noedels": 350, "mie": 350, "couscous": 360, "tortilla wraps": 300,
 # soep, conserven, bakken
 "soep": (40, ML), "tomatenpuree": 85, "passata": 30, "tomatenblokjes": 22, "kidneybonen": 100, "kikkererwten": 120, "linzen": 100,
 "appelmoes": 70, "tarwebloem": 350, "suiker": 400,
 # sauzen, olie, kruiden
 "pastasaus": 60, "pesto": 450, "mayonaise": 690, "fritessaus": 300, "ketchup": 110, "curry": 115, "mosterd": 140, "satesaus": 200,
 "knoflooksaus": 330, "barbecuesaus": 130, "slasaus": 300, "sambal": 50, "ketjap": (280, ML), "sojasaus": (60, ML), "olijfolie": (820, ML),
 "zonnebloemolie": (820, ML), "bakboter": 800, "keukenzout": 0, "peper": 290, "bouillonblokjes": 230,
 # koffie en thee (zoals je het drinkt)
 "koffiebonen": (2, "kopje"), "filterkoffie": (2, "kopje"), "koffiepads": (2, "kopje"), "koffiecups": (2, "kopje"), "oploskoffie": (2, "kopje"),
 "zwarte thee": (1, "kopje"), "groene thee": (1, "kopje"), "rooibos thee": (1, "kopje"), "pepermuntthee": (1, "kopje"), "kamillethee": (1, "kopje"),
 "vruchtenthee": (1, "kopje"),
 # sap en wijn
 "sinaasappelsap": (45, ML), "appelsap": (46, ML), "multivitaminesap": (50, ML), "rode wijn": (85, ML), "witte wijn": (80, ML), "rose": (80, ML),
 # koek, snoep, chips, noten
 "chocolade reep": 530, "melkchocolade": 540, "pure chocolade": 550, "drop": 350, "winegums": 330, "snoep": 350, "eierkoeken": 390,
 "stroopwafels": 450, "koekjes": 480, "speculaas": 470, "biscuits": 460, "naturel chips": 540, "paprika chips": 530, "chips": 530,
 "tortilla chips": 490, "popcorn": 470, "pinda": 600, "nootjes": 520, "cashewnoten": 600,
}
# Dranken in verpakkingen (varianten): op begin van de naam
PREFIX = [("Coca-Cola Zero", 0), ("Cola zero en light", 0), ("Coca-Cola", 42), ("Pepsi", 43), ("Cola (alle merken)", 42), ("Sinas", 38),
          ("7up en Sprite", 30), ("Ice tea", 25), ("Spa ", 0), ("Bruisend water", 0), ("Water ", 0), ("Energiedrank suikervrij", 3),
          ("Energiedrank", 45), ("Alcoholvrij bier", 20), ("Pils", 42)]

from kcal_extra import K2

def kcal_van(t):
    if t in K2:
        v = K2[t]
        return v if isinstance(v, tuple) else (v, G)
    for pre, v in PREFIX:
        if t.startswith(pre): return (v, ML)
    for k in (t, t.removesuffix(" vers"), t.removesuffix(" diepvries"), t.removesuffix(" in pot"),
              t.removeprefix("aardappelen ").replace("kruimig", "aardappelen").replace("vastkokend", "aardappelen")):
        if k in K:
            v = K[k]
            return v if isinstance(v, tuple) else (v, G)
    if t.startswith("aardappelen"): return (77, G)
    if t.startswith(("wasmiddel", "koffiecups dolce")): return None
    return None
