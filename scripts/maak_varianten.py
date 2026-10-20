"""Maakt scripts/varianten.json: subcategorieën per verpakking en inhoud (blikje, sixpack, tray, fles 1,5 liter, krat ...).

Een variant is een zoekterm die niet op woorden zoekt, maar op een basisterm plus een verpakkingsfilter:
  zoek  – basistermen (de gewone zoekfunctie), samengevoegd
  niet  – woorden die er niet in mogen (smaakjes, andere soorten)
  pak   – "blik" of "fles" (of leeg: maakt niet uit)
  ml    – inhoud per blik of fles, [min, max] in milliliter
  n     – aantal blikken of flessen in de verpakking, [min, max]
  alc   – "vrij" (alcoholvrij) of "met" (met alcohol)
De herkenning zelf staat in vergelijk.py (pakinfo) en in site/index.html (pakInfo); die twee moeten gelijk blijven.
Gebruik: python3 scripts/maak_varianten.py  (daarna cats.json aanpassen als er termen bij komen of weg gaan)
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMAAK = ["cherry", "vanilla", "vanille", "lime", "lemon", "citroen", "caffeine", "cafeine", "caffeinevrij", "cafeinevrij", "cafeïne",
         "caffeïne", "mixed", "daniel", "creamy", "holiday", "limited", "edition", "tomorrow", "raspberry", "mango", "peach", "lemoen", "ginger"]
V = {}

def fris(basis, label, niet=()):
    niet = SMAAK + list(niet)
    z = {"zoek": basis, "niet": niet, "soort": "fris"}
    V[f"{label} fles 1,5 liter"] = {**z, "pak": "fles", "ml": [1250, 1500], "n": [1, 1]}
    V[f"{label} fles 1 liter"] = {**z, "pak": "fles", "ml": [1000, 1000], "n": [1, 1]}
    V[f"{label} flesje 0,5 liter"] = {**z, "pak": "fles", "ml": [375, 500], "n": [1, 1]}
    V[f"{label} los blikje 33 cl"] = {**z, "pak": "blik", "ml": [330, 355], "n": [1, 1]}
    V[f"{label} los blikje 25 cl"] = {**z, "pak": "blik", "ml": [250, 250], "n": [1, 1]}
    V[f"{label} sixpack blikjes 33 cl"] = {**z, "pak": "blik", "ml": [330, 355], "n": [6, 6]}
    V[f"{label} blikjes 33 cl 8- tot 12-pack"] = {**z, "pak": "blik", "ml": [330, 355], "n": [8, 12]}
    V[f"{label} blikjes 33 cl tray (24)"] = {**z, "pak": "blik", "ml": [330, 355], "n": [18, 24]}
    V[f"{label} blikjes 25 cl 4- tot 12-pack"] = {**z, "pak": "blik", "ml": [250, 250], "n": [4, 12]}
    V[f"{label} blikjes 25 cl tray (20 of 24)"] = {**z, "pak": "blik", "ml": [250, 250], "n": [18, 24]}
    V[f"{label} mini blikjes (15 cl)"] = {**z, "pak": "blik", "ml": [150, 200], "n": [6, 12]}
    V[f"{label} flesjes 4-pack 0,5 liter"] = {**z, "pak": "fles", "ml": [500, 500], "n": [4, 6]}
    V[f"{label} flessen 4- of 6-pack 1,5 liter"] = {**z, "pak": "fles", "ml": [1250, 1500], "n": [4, 6]}

fris(["coca cola"], "Coca-Cola", ["zero", "light", "0,0"])
fris(["coca cola zero"], "Coca-Cola Zero")
fris(["pepsi"], "Pepsi", ["max", "zero", "light"])
fris(["cola"], "Cola (alle merken)", ["zero", "light", "max"])
fris(["cola zero", "cola light", "pepsi max"], "Cola zero en light (alle merken)")
fris(["sinas", "fanta orange"], "Sinas", ["zero", "light", "lemon", "cassis", "exotic"])
fris(["7up", "sprite", "seven up"], "7up en Sprite", ["zero", "free", "cherry"])
fris(["ice tea", "icetea"], "Ice tea", ["zero", "green", "green", "mango", "peach", "perzik", "sparkling", "bubbels"])
for k in list(V):
    if k.startswith("Ice tea") and ("mini" in k):
        del V[k]

# Water
W = ["citroen", "lemon", "framboos", "limoen", "touch", "fruit", "aardbei", "sinaasappel", "smaak", "flavour", "vitamin", "infused"]
def water(basis, label, niet=()):
    z = {"zoek": basis, "niet": W + list(niet), "soort": "water"}
    V[f"{label} fles 1,5 liter"] = {**z, "pak": "fles", "ml": [1250, 1500], "n": [1, 1]}
    V[f"{label} 6 x 1,5 liter"] = {**z, "pak": "fles", "ml": [1250, 1500], "n": [4, 6]}
    V[f"{label} flesje 0,5 liter"] = {**z, "pak": "fles", "ml": [500, 500], "n": [1, 1]}
    V[f"{label} flesjes 6 x 0,5 liter"] = {**z, "pak": "fles", "ml": [500, 500], "n": [4, 6]}
    V[f"{label} flesjes 24 x 0,5 liter"] = {**z, "pak": "fles", "ml": [500, 500], "n": [12, 24]}
    V[f"{label} kinderflesjes (33 cl)"] = {**z, "pak": "fles", "ml": [250, 375], "n": [1, 6]}
water(["spa reine", "spa blauw"], "Spa Reine (zonder prik)")
water(["spa intens", "spa rood"], "Spa Intens (met prik)")
water(["bronwater"], "Bronwater zonder prik", ["bruisend", "koolzuur", "prik", "sparkling"])
water(["bruisend water", "mineraalwater bruisend", "sparkling water"], "Bruisend water")

# Energiedrank
E = {"zoek": ["red bull", "energy drink", "energiedrank", "monster energy"], "niet": SMAAK + ["sugarfree", "suikervrij", "zero", "ultra", "light", "tropical", "watermelon", "edition"], "soort": "fris"}
V["Energiedrank los blikje 25 cl"] = {**E, "pak": "blik", "ml": [250, 250], "n": [1, 1]}
V["Energiedrank los blik 50 cl"] = {**E, "pak": "blik", "ml": [473, 568], "n": [1, 1]}
V["Energiedrank blikjes multipack"] = {**E, "pak": "blik", "ml": [250, 355], "n": [4, 24]}
E0 = {"zoek": ["red bull sugarfree", "red bull zero", "monster ultra", "energy drink zero", "energy drink sugarfree", "energiedrank suikervrij"], "niet": SMAAK, "soort": "fris"}
V["Energiedrank suikervrij los blikje"] = {**E0, "pak": "blik", "ml": [250, 568], "n": [1, 1]}

# Bier
BIERNIET = ["radler", "rose", "bock", "ipa", "weizen", "weissbier", "weißbier", "hefe", "witbier", "wit", "blond", "dubbel", "tripel", "desperados",
            "zwaar", "kanon", "gladiator", "8,6", "extreme", "intense", "strong", "lekkerbekje", "lekkerbekjes", "bierbeslag", "biercheque", "gift",
            "fust", "blade", "biergist", "davitamon", "proef", "speciale", "gvp", "mojito", "margarita", "mix", "lemon", "citroen", "fruit",
            "cherry", "kriek", "amber", "dark", "donker", "stout", "porter", "saison", "texels", "trappe", "affligem", "leffe", "grimbergen",
            "karmeliet", "gazeuse", "campagne", "uiltje", "paulaner", "kaapse", "dubbelbock", "alcoholarm", "2,0", "tequila", "lime", "mango",
            "tarwe", "seizoen", "herfst", "lente", "winter", "glas", "glazen", "worst", "bierworst", "pindas", "nootjes", "kaas", "mosterd", "brood"]
B = {"zoek": ["pils", "pilsener", "pilsner", "bier", "lager"], "niet": BIERNIET, "soort": "bier"}
BM, BV = {**B, "alc": "met"}, {**B, "alc": "vrij"}
V["Pils krat 24 flesjes"] = {**BM, "pak": "fles", "ml": [250, 300], "n": [20, 24]}
V["Pils flesjes 6-pack"] = {**BM, "pak": "fles", "ml": [250, 300], "n": [6, 6]}
V["Pils flesjes 12-pack"] = {**BM, "pak": "fles", "ml": [250, 300], "n": [10, 12]}
V["Pils los blikje 33 cl"] = {**BM, "pak": "blik", "ml": [330, 355], "n": [1, 1]}
V["Pils sixpack blikjes 33 cl"] = {**BM, "pak": "blik", "ml": [330, 355], "n": [6, 6]}
V["Pils blikjes 33 cl 10- of 12-pack"] = {**BM, "pak": "blik", "ml": [330, 355], "n": [10, 12]}
V["Pils blikjes 33 cl tray (24)"] = {**BM, "pak": "blik", "ml": [330, 355], "n": [18, 24]}
V["Pils los blik 50 cl"] = {**BM, "pak": "blik", "ml": [440, 568], "n": [1, 1]}
V["Pils blikken 50 cl 4- of 6-pack"] = {**BM, "pak": "blik", "ml": [440, 568], "n": [4, 6]}
V["Pils blikken 50 cl tray (24)"] = {**BM, "pak": "blik", "ml": [440, 568], "n": [12, 24]}
V["Pils beugelflessen"] = {**BM, "pak": "fles", "ml": [450, 450], "n": [4, 16]}
V["Alcoholvrij bier krat 24 flesjes"] = {**BV, "pak": "fles", "ml": [250, 300], "n": [20, 24]}
V["Alcoholvrij bier flesjes 6-pack"] = {**BV, "pak": "fles", "ml": [250, 300], "n": [6, 6]}
V["Alcoholvrij bier los blikje 33 cl"] = {**BV, "pak": "blik", "ml": [330, 355], "n": [1, 1]}
V["Alcoholvrij bier sixpack blikjes 33 cl"] = {**BV, "pak": "blik", "ml": [330, 355], "n": [6, 6]}
V["Alcoholvrij bier blikjes 12-pack"] = {**BV, "pak": "blik", "ml": [250, 355], "n": [10, 12]}
V["Alcoholvrij bier los blik 50 cl"] = {**BV, "pak": "blik", "ml": [440, 568], "n": [1, 1]}


water(["mineraalwater", "bronwater", "water"], "Water zonder prik (alle merken)", ["bruisend", "koolzuur", "prik", "sparkling", "intens", "licht", "rood", "spa", "kokos", "tonic", "bruiswater", "br", "peer", "cactus", "mondwater", "cb12", "vitwater", "hydrate", "sportcap"])

# ---------- eten: vers, diepvries of pot ----------
DIEP = ["iglo", "ardo", "diepvries", "vriesvers", "vriesverse", "bevroren"]
POT = ["hak", "bonduelle", "kramer", "pot", "glas", "blik", "betuws", "conserven", "pak", "jumbo's"]
BEREID = ["roomsaus", "creme", "crème", "kaassaus", "gratin", "ovenschotel", "verspakket", "maaltijd", "salade", "soep", "mix", "pakket", "roerbak",
          "stamppot", "borek", "boreks", "quiche", "lasagne", "pizza", "taart", "burger", "rosti", "rösti", "puree", "rijst", "noedels", "spaghetti",
          "chips", "snack", "pesto", "spread", "smoothie", "sap", "olvarit", "baby", "knijpfruit", "ijs", "jam", "fruitspread", "confituur", "yoghurt",
          "kwark", "drank", "siroop", "gedroogd", "gedroogde", "taco", "wrap", "dip", "saus", "kroket", "schijf", "schijven", "pasta", "pastei"]
def vers_diep_pot(basis, naam, vers=True, diep=True, pot=False, niet=()):
    n = list(niet)
    if vers: V[f"{naam} vers"] = {"zoek": basis, "niet": DIEP + POT + BEREID + n}
    if diep: V[f"{naam} diepvries"] = {"zoek": basis, "wel": DIEP, "niet": BEREID + n}
    if pot: V[f"{naam} in pot"] = {"zoek": basis, "wel": POT, "niet": DIEP + BEREID + n}
vers_diep_pot(["broccoli"], "broccoli", niet=["800", "seasons", "fish"])
vers_diep_pot(["bloemkool"], "bloemkool", niet=["800", "seasons", "braadworst", "worst"])
vers_diep_pot(["sperziebonen"], "sperziebonen", pot=True)
V["sperziebonen vers"]["niet"] += ["gebroken", "ml", "680", "660", "720", "370", "340", "675", "seasons"]
vers_diep_pot(["spinazie", "bladspinazie"], "spinazie", pot=True, niet=["feta", "a", "la", "ricotta", "boursin"])
V["spinazie vers"]["niet"] += ["gehakte", "gesneden", "330", "630", "245", "seasons"]
vers_diep_pot(["boerenkool"], "boerenkool", niet=["rookworst", "worst", "spekjes"])
V["boerenkool vers"]["niet"] += ["deelblokjes", "seasons", "800", "680"]
vers_diep_pot(["spruitjes"], "spruitjes", diep=False)
vers_diep_pot(["rode kool"], "rode kool", diep=False, pot=True, niet=["salade", "rauwkost"])
V["rode kool vers"]["niet"] += ["680", "690", "700", "710", "355", "340", "appel", "appeltjes", "ml"]
vers_diep_pot(["champignons"], "champignons", diep=False, pot=True, niet=["gevuld", "gevulde", "bouillon", "roomsaus"])
vers_diep_pot(["aardbeien"], "aardbeien", niet=["haribo", "schuim", "snoep"])
vers_diep_pot(["blauwe bessen"], "blauwe bessen")
V["blauwe bessen vers"]["niet"] += ["diepv", "diepvriesfruit"]; V["blauwe bessen diepvries"]["wel"] = DIEP + ["diepv", "diepvriesfruit"]; V["aardbeien diepvries"]["wel"] = DIEP + ["diepv", "diepvriesfruit"]
vers_diep_pot(["frambozen"], "frambozen", vers=False)
vers_diep_pot(["doperwten", "erwten", "erwtjes"], "doperwten", vers=False, niet=["wortel", "wortelen", "wortels", "soep", "kikker", "spliterwten"])
vers_diep_pot(["wokgroente", "wokgroenten", "roerbakgroente", "roerbakgroenten"], "wokgroente", niet=[])
for k in ("wokgroente vers", "wokgroente diepvries"):
    V[k]["niet"] = [x for x in V[k]["niet"] if x not in ("roerbak", "mix")]
V["erwten en wortelen in pot"] = {"zoek": ["erwten en wortelen", "erwten wortelen", "erwtjes en worteltjes", "erwtjes worteltjes", "doperwten en wortelen", "doperwten wortelen"], "niet": DIEP + ["soep", "baby", "olvarit"]}

# Aardappelen
V["aardappelen kruimig"] = {"zoek": ["aardappelen", "aardappels"], "wel": ["kruimig", "kruimige", "stamppotaardappelen", "bloemig", "bloemige"], "niet": BEREID + DIEP + ["krieltjes", "zoete", "friet", "parten", "schijfjes"]}
V["aardappelen vastkokend"] = {"zoek": ["aardappelen", "aardappels"], "wel": ["vastkokend", "vastkokende"], "niet": BEREID + DIEP + ["krieltjes", "zoete", "friet", "parten", "schijfjes"]}
V["aardappelpuree"] = {"zoek": ["aardappelpuree"], "niet": DIEP + ["poeder", "pak", "instant", "zakje", "zakjes"], "ml": [300, 2000]}
V["knoflook bollen"] = {"zoek": ["knoflook"], "niet": ["gehakt", "gehakte", "pasta", "puree", "saus", "poeder", "korrels", "olie", "gedroogd", "gedroogde", "inproba", "kruiden",
        "boter", "brood", "stokbrood", "chips", "kaas", "mayonaise", "dressing", "worst", "ingelegd", "tube", "spray", "pers", "zout", "peper", "fles", "glas", "snack", "verkade", "olijven"]}
V["gehakte knoflook"] = {"zoek": ["gehakte knoflook", "knoflook gehakt"], "niet": ["olie", "saus"]}
V["paprika rood"] = {"zoek": ["paprika rood", "rode paprika", "paprika's rood", "rode paprika's"], "niet": ["punt", "puntpaprika", "snack", "snackpaprika", "chips", "soep", "poeder", "saus", "gegrild", "gegrilde", "pot", "glas", "spread", "humus", "hummus", "mix", "geroosterd", "geroosterde", "royal", "sera"]}
V["paprika mix"] = {"zoek": ["paprika mix", "paprika's mix", "mix paprika", "paprika driekleur", "paprika trio", "paprika tricolore", "paprika's"], "wel": ["mix", "driekleur", "trio", "tricolore", "3 stuks", "kleuren"],
        "niet": ["punt", "snack", "chips", "soep", "poeder", "saus", "gegrild", "pot", "glas", "spread", "kruiden", "rood", "groen", "geel", "kip", "pretty", "silvo", "mini"]}

# Vis
V["zalmfilet"] = {"zoek": ["zalmfilet", "zalmfilets", "zalm filet", "zalmmoot", "zalmmoten", "zalm"], "niet": ["gerookt", "gerookte", "blik", "salade", "pokebowl", "poke", "roomkaas", "ovenschotel", "spread", "snack", "salm", "kattenvoer", "katten", "sushi", "burger", "worst", "pate", "rolletjes", "carpaccio", "spies", "princes", "statesman", "roze", "maaltijd", "pasta", "quiche", "wrap", "hond", "snippers", "stukjes"]}
V["tonijn in water"] = {"zoek": ["tonijn"], "wel": ["water", "eigen nat"], "niet": ["sandwich", "salade", "spread", "steak", "pizza", "katten", "kattenvoer", "pasta", "olie"]}
V["tonijn in olie"] = {"zoek": ["tonijn"], "wel": ["olie", "zonnebloemolie", "olijfolie", "zonnebl", "oil"], "niet": ["sandwich", "salade", "spread", "steak", "pizza", "katten", "kattenvoer", "pasta", "water"]}

# IJs
IJSNIET = ["ijsthee", "ice", "tea", "ijsbergsla", "ijsblokjes", "ijsbokaal", "schepijs", "taart", "bonbon", "ijskrabber", "ijszakken", "hond", "honden", "kat", "ijslolly", "ijsvorm"]
V["ijs in bak"] = {"zoek": ["ijs", "roomijs", "schepijs"], "niet": IJSNIET[:-6] + ["hond", "honden", "kat", "stuks", "raket", "magnum", "cornetto", "hoorntjes", "sticks"], "ml": [450, 2500], "n": [1, 1]}
V["ijsjes multipack"] = {"zoek": ["ijs", "ijsjes", "magnum", "cornetto", "raket", "ijslolly", "waterijs", "roomijs"], "niet": IJSNIET[:9] + ["hond", "honden", "kat", "vorm", "vormpjes", "maker"], "n": [3, 30]}

# Wassen
V["wasmiddel vloeibaar"] = {"zoek": ["wasmiddel", "vloeibaar wasmiddel", "wasgel"], "wel": ["vloeibaar", "vloeibare", "gel", "liter", "ml", "l"], "niet": ["capsules", "caps", "pods", "tabs", "discs", "poeder", "waspoeder", "doekjes", "sheets", "dettol", "baby", "bonbebe", "vaatwas", "hand"]}
V["waspoeder"] = {"zoek": ["waspoeder", "wasmiddel poeder", "wasmiddel"], "wel": ["poeder", "waspoeder", "kg", "gram"], "niet": ["vaatwas", "vaatwaspoeder", "capsules", "caps", "pods", "tabs", "discs", "vloeibaar", "gel", "liter", "ml"]}
V["wascapsules"] = {"zoek": ["wasmiddel", "wascapsules", "ariel pods", "wasmiddelcapsules"], "wel": ["capsules", "caps", "pods", "discs", "tabs", "capsule"], "niet": ["vaatwas", "koffie", "vlekverwijderaar"]}

# Koffie en thee
V["koffiecups dolce gusto"] = {"zoek": ["dolce gusto", "koffiecups", "capsules"], "wel": ["dolce", "gusto"], "niet": ["machine", "apparaat", "houder"]}
V["koffiecups"] = {"zoek": ["koffiecups", "koffiecapsules", "capsules espresso", "koffie capsules"], "niet": ["dolce", "gusto", "senseo", "pads", "machine", "houder", "thee", "chocolade", "melk"]}
V["zwarte thee"] = {"zoek": ["zwarte thee", "earl grey", "engelse melange", "english breakfast", "thee engelse melange", "melange thee"], "niet": ["ijsthee", "ice", "lemon", "citroen", "chai", "decaf"]}
V["pepermuntthee"] = {"zoek": ["pepermuntthee", "pepermunt thee", "muntthee", "munt thee", "thee munt", "thee pepermunt"], "niet": ["ijsthee", "ice", "drop", "snoep"]}
V["kamillethee"] = {"zoek": ["kamillethee", "kamille thee", "thee kamille"], "niet": ["ijsthee", "ice"]}
V["vruchtenthee"] = {"zoek": ["vruchtenthee", "fruit thee", "fruitthee", "bosvruchten thee", "thee bosvruchten", "thee aardbei", "thee framboos", "thee bosvruchten"], "niet": ["ijsthee", "ice", "drop", "snoep", "yoghurt"]}

json.dump(V, open(os.path.join(ROOT, "scripts", "varianten.json"), "w"), ensure_ascii=False, indent=1)
print(len(V), "varianten")
