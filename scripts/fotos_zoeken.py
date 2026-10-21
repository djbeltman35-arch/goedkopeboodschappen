"""Zoekt per maaltijd vrij bruikbare foto's op Wikimedia Commons (CC0, publiek domein, CC BY, CC BY-SA) en slaat kandidaten op in fotos-kandidaten/."""
import json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from maaltijden import MAALTIJDEN
Q = {"boerenkool-met-rookworst": ["boerenkool stamppot", "boerenkool met worst", "kale stamppot"],
     "hete-bliksem-rookworst": ["hete bliksem", "stamppot apple potato", "rookworst stamppot"],
     "schol-mosterdsaus-wortelstamppot": ["breaded plaice", "fried plaice fillet", "schol"],
     "traybake-kip-krieltjes": ["chicken drumsticks potatoes tray bake", "roast chicken drumsticks potatoes"],
     "steak-de-boeuf-aardappelpartjes": ["steak potatoes green beans", "bavette steak potatoes"],
     "vegetarische-pompoenstamppot": ["pumpkin mashed potatoes", "pumpkin mash"],
     "vegan-preistamppot-gehaktbal": ["leek mashed potatoes", "stamppot prei", "vegan meatballs mashed potatoes"],
     "zoete-aardappelschotel-tonijn-prei": ["sweet potato gratin", "sweet potato casserole"],
     "zoete-aardappel-kip-oven": ["roasted sweet potato chickpeas chicken", "sheet pan chicken sweet potato"],
     "spitskool-ovenschotel-gehakt": ["cabbage casserole minced meat", "pointed cabbage casserole"],
     "quiche-ham-prei-erwtjes": ["ham leek quiche", "quiche lorraine"],
     "ovenomelet-bloemkool": ["frittata cauliflower", "oven omelette"],
     "vegan-moussaka-linzen": ["lentil moussaka", "vegetarian moussaka"],
     "pasta-garnalen-knoflook": ["shrimp garlic pasta", "prawn pasta garlic"],
     "romige-macaroni-kip-champignons": ["chicken mushroom pasta creamy", "macaroni chicken mushrooms"],
     "spaghetti-gehaktballetjes-tomatensaus": ["spaghetti meatballs", "spaghetti and meatballs"],
     "vegan-spaghetti-gebakken-tomaatjes": ["spaghetti cherry tomatoes", "pasta pomodorini"],
     "romige-pasta-worst-venkel": ["pasta sausage fennel", "sausage pasta"],
     "pasta-geroosterde-paprikasaus": ["roasted red pepper pasta", "red pepper sauce pasta"],
     "wraps-met-gehakt": ["minced beef wraps", "tortilla wrap minced meat"],
     "zoetzure-kip-rijst": ["sweet and sour chicken", "sweet and sour chicken rice"],
     "rijstbowl-zalm-gember": ["salmon rice bowl", "salmon poke bowl"],
     "rijstroerbak-varken-satesaus": ["pork satay rice", "pork stir fry peanut sauce"],
     "zilvervliesrijst-tofuspiesjes": ["tofu skewers", "tofu brown rice"],
     "risotto-verde-doperwten": ["pea risotto", "risotto peas spinach"],
     "butter-chicken-rijst": ["butter chicken", "murgh makhani"],
     "enchiladas-gehakt-tomatensalsa": ["enchiladas", "beef enchiladas"],
     "marokkaanse-pompoentajine-kikkererwten": ["pumpkin tagine", "vegetable tagine chickpeas couscous"],
     "indiase-roerbak-garnalen": ["prawn curry rice", "shrimp curry"],
     "zoetzuur-varkensvlees-ananas": ["sweet and sour pork pineapple", "sweet and sour pork"],
     "rijstbowl-soja-aubergine": ["eggplant rice bowl", "nasu dengaku", "miso aubergine"],
     "thaise-beef-salad-mango": ["thai beef salad", "yam nuea"],
     "aziatische-kip-noedelsalade": ["chicken noodle salad", "asian noodle salad"],
     "maaltijdsalade-zalm-penne": ["salmon pasta salad", "smoked salmon salad"],
     "spinaziesalade-spekjes-aardappel": ["spinach salad bacon egg", "warm potato salad bacon"],
     "zoete-aardappelsalade-hummusdressing": ["sweet potato salad", "roasted sweet potato salad"],
     "halloumisalade-linzen": ["halloumi salad", "halloumi lentil salad"],
     "goulashsoep": ["goulash soup", "gulyásleves"],
     "pannenkoeken-spek-ui": ["spekpannenkoek", "bacon pancake", "dutch pancake bacon"],
     "preisoep-spekjes-kaas": ["leek soup", "leek soup bacon"],
     "maaltijdvissoep": ["fish soup", "seafood soup"],
     "mexicaanse-bonensoep-quesadillas": ["black bean soup", "quesadilla"],
     "zoete-aardappel-wortelsoep": ["sweet potato carrot soup", "carrot soup"],
     "vispannetje-prei-wortel": ["fish pie puff pastry", "vispannetje", "salmon shrimp leek pie"],
     "vispannetje-kabeljauw-rijst": ["cod tomato sauce rice", "fish stew vegetables rice"],
     "broccolistamppot-vissticks": ["fish fingers mashed potatoes", "fish sticks broccoli"],
     "zalm-teriyaki-rijst": ["salmon teriyaki", "teriyaki salmon rice"],
     "woknoedels-garnalen": ["shrimp stir fry noodles", "prawn noodles"],
     "mosselen-met-friet": ["moules frites", "mussels fries"],
     "pasta-zalm-spinazie": ["salmon spinach pasta", "tagliatelle salmon"],
     "spaghetti-tonijn-bolognese": ["spaghetti tuna tomato sauce", "tuna pasta tomato"],
     "kibbeling-ovenfriet": ["kibbeling", "fried fish fries", "kibbeling friet"],
     "linzen-makreelsalade": ["lentil salad mackerel", "smoked mackerel salad"],
     "snelle-viscurry": ["fish curry", "green curry fish"],
     "visstoof-aardappelen-sperziebonen": ["fish stew potatoes", "fish casserole potatoes beans"],
     "vistacos-mango-avocado": ["fish tacos", "fish taco mango"],
     "varkenshaas-pasta-pesto": ["pork tenderloin pasta", "pork tenderloin mushrooms"],
     "babi-pangang": ["babi pangang", "sweet and sour pork"],
     "schnitzel-friet-witlofsalade": ["schnitzel fries", "pork schnitzel fries salad"],
     "procureur-stoofschotel": ["pork stew mushrooms peas", "braised pork potatoes"],
     "pasta-carbonara": ["spaghetti carbonara", "carbonara"],
     "gyrosschotel-rijst": ["gyros rice", "pork gyros plate"],
     "herfststamppot-slavink": ["red cabbage mashed potatoes", "rode kool stamppot", "slavink"],
     "karbonades-sperziebonen-krieltjes": ["pork chops green beans potatoes", "pork chop potatoes"],
     "zuurkool-mosterdspeklapjes": ["sauerkraut pork belly mashed potatoes", "zuurkool speklap"],
     "wraps-pulled-pork": ["pulled pork tortilla", "pulled pork wrap"],
     "spruitjesstamppot-saucijzen": ["brussels sprouts mashed potatoes sausage", "stamppot spruitjes"],
     "mie-varkensvlees-broccoli": ["pork noodles broccoli", "stir fried noodles pork"],
     "goulash-met-rijst": ["goulash", "hungarian goulash rice"],
     "runderstoof-spek-knolselderij": ["beef stew mashed potatoes", "beef stew bacon"],
     "boeuf-stroganoff": ["beef stroganoff", "stroganoff rice"],
     "hamburger-verse-friet": ["hamburger fries", "burger and fries"],
     "kogelbiefstuk-romige-aardappeltjes": ["steak potatoes broccoli", "beef steak broccoli potatoes"],
     "rijstschotel-gehakt-tauge": ["minced beef rice bean sprouts", "beef fried rice vegetables"],
     "witlof-ovenschotel-gehakt": ["witlof ovenschotel", "chicory gratin", "belgian endive casserole"],
     "zoete-spruitjes-kip-aardappelen": ["brussels sprouts chicken potatoes", "spruitjes", "brussels sprouts"],
     "kokos-kippensoep-rijstnoedels": ["chicken coconut soup noodles", "tom kha gai", "khao soi"],
     "zuurkoolstamppot-ananas-zalm": ["zuurkool stamppot", "sauerkraut mashed potatoes", "salmon fillet sauerkraut"],
     "jachtschotel-bloemkoolpuree": ["jachtschotel", "cauliflower mash casserole", "shepherd's pie cauliflower"],
     "ratatouille": ["ratatouille"],
     "gevulde-aubergine-gehakt": ["stuffed aubergine minced meat", "stuffed eggplant", "karniyarik"],
     "rijst-kip-sperziebonen": ["chicken rice green beans", "brown rice chicken green beans"],
     "salade-nicoise": ["salade niçoise", "nicoise salad"],
     "bloemkoolsoep-kikkererwten": ["cauliflower soup", "cream of cauliflower soup"],
     "kippensoep-met-rijst": ["chicken rice soup", "chicken soup rice vegetables"],
     "krieltjessalade-gerookte-forel": ["smoked trout potato salad", "smoked trout salad", "potato salad green beans"],
     "kip-piri-piri-rijst": ["piri piri chicken", "peri peri chicken legs"],
     "kipshoarma-rijst": ["chicken shawarma rice", "shawarma plate rice"],
     "geroosterde-groente-aardappelen-ei": ["roasted vegetables potatoes egg", "roasted root vegetables", "sheet pan vegetables"],
     "vis-tapenade-puree-sperziebonen": ["fish mashed potatoes green beans", "cod fillet mashed potatoes", "baked cod tapenade"],
     "lamsgehaktballetjes-tomatensaus": ["lamb meatballs tomato sauce", "kofta tomato sauce"],
     "pasta-boordevol-groente": ["pasta vegetable sauce", "linguine tomato vegetables"],
     "orzo-spinazie-kip": ["orzo spinach", "orzo chicken"],
     "lasagne-spinazie-ricotta": ["spinach ricotta lasagna", "spinach lasagne"],
     "paksoi-kip-rijst": ["bok choy chicken stir fry", "pak choi stir fry"],
     "noedelsoep-kip-groente": ["chicken noodle soup asian", "noodle soup chicken vegetables"],
     "poke-bowl-tofu": ["tofu poke bowl", "tofu bowl avocado", "buddha bowl tofu"],
     "caesarsalade-kip": ["chicken caesar salad", "caesar salad"],
     "stoofvlees": ["stoofvlees", "carbonade flamande", "beef stew"],
     "vegan-boerenkoolstamppot": ["boerenkool stamppot", "kale stamppot"],
     "vegan-hutspot": ["hutspot", "carrot onion mash"],
     "vegan-gehaktbal-aardappel-sperziebonen": ["vegetarian meatball potatoes green beans", "potatoes green beans"],
     "vegan-erwtensoep": ["erwtensoep", "split pea soup"],
     "shepherds-pie-linzen": ["lentil shepherd's pie", "shepherd's pie"],
     "paddenstoelenrijst-pastinaak-tofu": ["mushroom rice", "mushroom risotto tofu", "fried tofu rice"],
     "rijst-broccoli-tofu-ananassalsa": ["tofu broccoli rice", "tofu stir fry broccoli"],
     "vegan-bolognese-linzen": ["lentil bolognese", "vegan bolognese spaghetti"],
     "spaghetti-puttanesca-vegan": ["spaghetti puttanesca", "puttanesca"],
     "quinoasalade-venkel-wortel": ["quinoa salad roasted vegetables", "quinoa salad carrots"],
     "vegan-linzenstoof-spinazie": ["lentil stew spinach", "lentil spinach tomato stew"],
     "vegan-massaman-curry": ["massaman curry", "chickpea curry"],
     "gele-curry-sugarsnaps-kikkererwten": ["yellow curry chickpeas", "thai yellow curry vegetable", "chickpea curry rice"],
     "indonesische-roerbakschotel-snijbonen": ["peanut sauce stir fry", "gado gado"],
     "indonesische-roerbak-snijbonen": ["peanut sauce stir fry", "sambal goreng buncis", "gado gado"],
     "vegan-aardappelsalade": ["potato salad pickles", "potato salad"],
     "bruinebonensoep": ["bruine bonensoep", "brown bean soup", "bean soup"],
     "ovenschotel-aardappel-portobello": ["roasted potatoes portobello", "baked potatoes peppers vegetables", "roasted vegetables potatoes"],
     "vegan-tacos": ["vegan tacos", "tacos hard shell"],
     "snelle-vegan-noedels": ["vegetable stir fry noodles", "vegan noodles", "stir fried noodles vegetables"],
     "quinoa-paddenstoelen-bonen": ["quinoa mushrooms beans", "quinoa kidney beans", "quinoa chili"],
     "hutspot-met-rookworst": ["hutspot", "hutspot rookworst"],
     "andijviestamppot-met-spekjes": ["andijviestamppot", "stamppot andijvie", "endive stamppot"],
     "zuurkoolstamppot-met-spekjes": ["zuurkoolstamppot", "zuurkool stamppot", "sauerkraut mashed potatoes"],
     "gehaktbal-aardappelen-sperziebonen": ["gehaktbal sperziebonen", "gehaktbal aardappelen", "meatball potatoes green beans"],
     "hachee-met-rode-kool": ["hachee", "hachee rode kool", "dutch beef stew"],
     "broccoli-ovenschotel-met-gehakt": ["broccoli ovenschotel", "broccoli casserole minced meat", "broccoli gratin"],
     "spaghetti-bolognese": ["spaghetti bolognese"],
     "macaroni-ham-kaas": ["macaroni ham kaas", "macaroni met ham en kaas", "baked macaroni ham cheese"],
     "lasagne": ["lasagne bolognese", "lasagna"],
     "pasta-pesto-met-kip": ["pasta pesto chicken", "penne pesto chicken", "pasta pesto"],
     "penne-met-spek-en-spinazie": ["pasta spinach bacon cream", "penne spinach", "pasta spinazie spek"],
     "nasi-goreng": ["nasi goreng"],
     "bami-goreng": ["bami goreng", "mie goreng"],
     "chili-con-carne": ["chili con carne rice", "chili con carne"],
     "kip-ketjap-met-rijst": ["ayam kecap", "chicken kecap manis rice", "kip ketjap"],
     "maaltijdsalade-kip-krieltjes": ["chicken salad potatoes egg", "salad chicken potatoes green beans", "maaltijdsalade"],
     "pastasalade-pesto-kip": ["pasta salad pesto mozzarella", "pesto pasta salad", "pasta salad tomatoes mozzarella"],
     "pastasalade-tonijn": ["tuna pasta salad", "pasta salad tuna egg"],
     "erwtensoep": ["erwtensoep", "snert", "split pea soup sausage"],
     "pannenkoeken": ["pannenkoeken", "dutch pancakes stroop", "pannenkoek"],
     "chili-sin-carne": ["vegetarian chili beans rice", "chili sin carne", "bean chili"],
     "frittata-aardappel-ui": ["potato frittata", "spanish omelette tortilla de patatas", "frittata"],
     "zalm-broccoli-krieltjes": ["salmon broccoli potatoes", "baked salmon broccoli", "salmon fillet potatoes"],
     "groentesoep-met-balletjes": ["groentesoep balletjes", "vegetable soup meatballs", "groentesoep"],
     "gevulde-paprika": ["stuffed peppers", "gevulde paprika", "stuffed bell peppers minced meat"],
     "kip-kerrie-kokos": ["chicken curry coconut rice", "chicken curry rice", "kip kerrie"],
     "risotto-champignons-spinazie": ["mushroom risotto", "risotto funghi", "mushroom spinach risotto"],
     "wraps-met-kip": ["chicken wrap", "chicken tortilla wrap", "wrap kip"],
     "bloemkool-ovenschotel-gehakt": ["cauliflower casserole", "cauliflower gratin", "cauliflower cheese"],
     "griekse-salade-kip": ["greek salad chicken", "greek salad feta", "horiatiki"],
     "tomatensoep-met-balletjes": ["tomatensoep balletjes", "tomato soup meatballs", "tomato soup"],
     "kip-teriyaki": ["chicken teriyaki rice", "teriyaki chicken", "chicken teriyaki"],
     "kipcurry-peultjes": ["chicken curry snow peas", "chicken curry vegetables rice", "chicken curry"],
     "shakshuka-met-balletjes": ["shakshuka", "shakshouka eggs tomato", "shakshuka pan"],
     "thaise-groene-curry": ["thai green curry chicken", "green curry", "gaeng keow wan"],
     "linzendahl": ["dal red lentils", "masoor dal", "lentil dahl"],
     "couscous-kip-dadels": ["couscous chicken vegetables", "couscous chicken", "couscous dish"],
     "pad-thai": ["pad thai chicken", "pad thai"],
     "burrito-bowl": ["burrito bowl", "mexican rice bowl", "burrito bowl chicken"],
     "gehaktbal-aardappelen-sperziebonen": ["meatball potatoes green beans", "gehaktbal", "meatballs boiled potatoes"],
     "macaroni-ham-kaas": ["macaroni ham cheese casserole", "baked macaroni", "macaroni and cheese ham"],
     "maaltijdsalade-kip-krieltjes": ["chicken salad potatoes", "potato salad chicken egg", "chicken potato salad"],
     "zoete-aardappelcurry": ["sweet potato curry", "sweet potato cauliflower curry", "vegetable curry rice"],
     "pompoensoep": ["pumpkin soup", "butternut squash soup", "pompoensoep"],
     "gevulde-courgette": ["stuffed zucchini", "stuffed courgette minced meat", "zucchini boats"],
     "preischotel-aardappel": ["leek potato gratin", "leek potato casserole", "potato leek bake"],
     "kip-tandoori-rijst": ["tandoori chicken rice", "tandoori chicken", "chicken tikka rice"],
     "paella-met-kip": ["chicken paella", "paella valenciana", "paella"],
     "turkse-linzensoep": ["mercimek corbasi", "turkish lentil soup", "red lentil soup"],
     "vis-ovenschotel-spinazie": ["fish pie spinach", "fish casserole mashed potatoes", "fish gratin spinach"],
     "mexicaans-eenpansgerecht-rijst": ["mexican rice beef skillet", "mexican rice minced meat", "one pot mexican rice"],
     "quinoasalade-tonijn-avocado": ["quinoa salad tuna avocado", "quinoa salad avocado", "tuna quinoa salad"],
     "pompoenrisotto": ["pumpkin risotto", "butternut squash risotto", "risotto zucca"],
     "ovenschotel-aardappel-kip": ["chicken potato casserole", "chicken potato bake broccoli", "chicken gratin potatoes"],
     "aardappel-bloemkoolcurry-bief": ["aloo gobi", "potato cauliflower curry", "cauliflower potato curry beef"],
     "roerbak-kip-krieltjes": ["chicken stir fry vegetables potatoes", "stir fried chicken broccoli", "chicken vegetables baby potatoes"],
     "shakshuka-paprika": ["shakshuka", "shakshouka eggs tomato pepper", "shakshuka pan"],
     "penne-tonijn-roerbakgroente": ["pasta tuna vegetables", "penne tuna tomato", "tuna pasta"],
     "wraps-guacamole-kidneybonen": ["bean wrap guacamole", "vegetarian burrito beans", "wrap kidney beans"],
     "bulgursalade-kisir": ["kisir", "bulgur salad", "tabbouleh bulgur"],
     "minestrone-met-gehakt": ["minestrone soup", "minestrone", "vegetable soup pasta"],
     "pita-kipgyros": ["chicken gyros pita", "gyros pita tzatziki", "chicken pita"],
     "volkorenspaghetti-courgette-champignons": ["spaghetti zucchini mushrooms", "pasta courgette mushroom", "whole wheat spaghetti vegetables"],
     "couscoussalade-kikkererwten": ["couscous salad chickpeas", "chickpea couscous salad", "couscous salad"],
     "linzensoep-rookworst": ["lentil soup sausage", "linsensuppe wurst", "lentil soup"],
     "courgette-bonensoep-geitenkaas": ["bean soup zucchini", "green vegetable soup beans", "courgette soup"],
     "tomaat-paprikasoep-kip": ["tomato pepper soup", "roasted red pepper tomato soup", "tomato soup"],
     "visfilet-courgette-tomaat": ["fish fillet zucchini tomato", "baked fish vegetables mashed potatoes", "white fish tomato courgette"],
     "stamppot-rauwe-spinazie-kip": ["spinach stamppot", "mashed potatoes spinach", "stamppot spinazie"],
     "kalkoenfilet-groene-groenten": ["turkey fillet vegetables", "turkey breast broccoli potatoes", "turkey steak green beans"],
     "groente-omelet": ["vegetable omelette", "omelette vegetables", "frittata vegetables"],
     "ovenschotel-vis-snijbonen": ["fish potato casserole", "fish bake potatoes beans", "fish gratin potatoes"],
     "spinazieschotel-met-ei": ["spinach egg casserole", "eggs florentine bake", "spinach egg bake"],
     "kabeljauw-wortelpuree": ["cod carrot puree", "baked cod crust", "cod fillet mashed carrots"],
     "volkorenpasta-spinazie-tonijn": ["pasta spinach tuna", "penne spinach tomato", "tuna spinach pasta"],
     "pasta-met-groenten": ["pasta roasted vegetables", "pasta primavera", "vegetable pasta"],
     "bloemkoolrijstbowl-kip-pindasaus": ["cauliflower rice bowl chicken", "chicken peanut sauce bowl", "cauliflower rice chicken"],
     "roerbak-kip-woksaus": ["chicken stir fry rice", "chicken vegetable stir fry", "stir fry baby corn"],
     "traybake-kip-zwarte-bonen": ["chicken black beans peppers", "mexican chicken traybake", "chicken sheet pan peppers"],
     "pita-griekse-kip": ["greek chicken pita", "chicken souvlaki pita", "pita chicken salad"],
     "bonensalade-tonijn": ["bean salad tuna", "tuna bean salad", "white bean salad"],
     "quinoasalade-linzen": ["quinoa lentil salad", "quinoa salad corn feta", "lentil salad"]}
GEDAAN = set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "maaltijd_fotos.json"))))
# Al eerder bekeken zonder geschikte foto: niet opnieuw zoeken (scheelt tijd)
GEDAAN |= {"bloemkoolrijstbowl-kip-pindasaus", "bruinebonensoep", "courgette-bonensoep-geitenkaas", "indonesische-roerbak-snijbonen", "jachtschotel-bloemkoolpuree", "kabeljauw-wortelpuree", "kalkoenfilet-groene-groenten", "kip-piri-piri-rijst", "kipshoarma-rijst", "krieltjessalade-gerookte-forel", "lamsgehaktballetjes-tomatensaus", "maaltijdsalade-kip-krieltjes", "macaroni-ham-kaas", "mexicaans-eenpansgerecht-rijst", "noedelsoep-kip-groente", "orzo-spinazie-kip", "ovenschotel-aardappel-portobello", "paksoi-kip-rijst", "pasta-boordevol-groente", "preischotel-aardappel", "quinoasalade-tonijn-avocado", "quinoasalade-venkel-wortel", "roerbak-kip-krieltjes", "shepherds-pie-linzen", "traybake-kip-zwarte-bonen", "vegan-aardappelsalade", "vegan-boerenkoolstamppot", "vegan-gehaktbal-aardappel-sperziebonen", "vis-ovenschotel-spinazie", "vis-tapenade-puree-sperziebonen", "visfilet-courgette-tomaat", "volkorenspaghetti-courgette-champignons", "witlof-ovenschotel-gehakt", "wraps-guacamole-kidneybonen", "zuurkoolstamppot-ananas-zalm"}
UA = {"User-Agent": "GoedkopeBoodschappen/1.0 (https://boodschappenvergelijk.nl; goedkopeboodschappen@proton.me)"}
OK = re.compile(r"^(CC0|Public domain|PD|CC BY(-SA)? [0-9.]+|CC BY(-SA)?)", re.I)
def api(params):
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({**params, "format": "json"})
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30))
os.makedirs("fotos-kandidaten", exist_ok=True)
_af = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fotos_alleen.txt')
ALLEEN = set((os.environ.get('ALLEEN') or (open(_af).read() if os.path.exists(_af) else '')).strip().split(',')) - {''}
alle = {}
for m in MAALTIJDEN:
    slug = m["slug"]; gezien = set(); kand = []
    if slug in GEDAAN or (ALLEEN and slug not in ALLEEN): continue
    for q in Q.get(slug, [m["naam"]]):
        try:
            r = api({"action": "query", "generator": "search", "gsrsearch": f"{q} filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 12,
                     "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 1400,
                     "iiextmetadatafilter": "LicenseShortName|Artist|ImageDescription|Credit"})
        except Exception as e:
            print("fout", q, e); continue
        for p in sorted(r.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
            ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {})
            lic = md.get("LicenseShortName", {}).get("value", "")
            if p["title"] in gezien or not OK.match(lic) or ii.get("mime") not in ("image/jpeg", "image/png") or ii.get("width", 0) < 900: continue
            gezien.add(p["title"])
            artist = re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "")).strip()
            desc = re.sub(r"<[^>]+>", "", md.get("ImageDescription", {}).get("value", "")).strip()[:200]
            kand.append({"titel": p["title"], "licentie": lic, "maker": artist, "beschrijving": desc, "bron": ii.get("descriptionurl"), "thumb": ii.get("thumburl"), "zoek": q})
        time.sleep(1)
    # Te weinig op Wikimedia? Dan ook zoeken via Openverse (Flickr en andere sites met vrije licenties: CC0, publiek domein, CC BY, CC BY-SA).
    if len(kand) < 6:
        for q in Q.get(slug, [m["naam"]]):
            if len(kand) >= 6: break
            try:
                u = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode({"q": q, "license": "cc0,pdm,by,by-sa", "page_size": 12, "mature": "false"})
                r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30))
            except Exception as e:
                print("openverse fout", q, e); continue
            for x in r.get("results", []):
                if len(kand) >= 6: break
                if (x.get("width") and x["width"] < 800) or x.get("url") in gezien: continue
                gezien.add(x.get("url"))
                l, v = (x.get("license") or "").lower(), x.get("license_version") or ""
                lic = {"cc0": "CC0", "pdm": "Public domain", "by": f"CC BY {v}".strip(), "by-sa": f"CC BY-SA {v}".strip()}.get(l)
                if not lic: continue
                kand.append({"titel": x.get("title") or q, "licentie": lic, "maker": x.get("creator") or "", "beschrijving": (x.get("title") or "")[:200],
                             "bron": x.get("foreign_landing_url") or x.get("url"), "thumb": x.get("url"), "zoek": q, "via": x.get("source") or "openverse"})
            time.sleep(1)
    kand = kand[:6]
    for i, k in enumerate(kand):
        try:
            data = urllib.request.urlopen(urllib.request.Request(k["thumb"], headers=UA), timeout=60).read()
            k["bestand"] = f"fotos-kandidaten/{slug}-{i}.jpg"; open(k["bestand"], "wb").write(data)
        except Exception as e: print("download fout", k["titel"], e)
        time.sleep(1)
    alle[slug] = kand; print(slug, len(kand))
json.dump(alle, open("fotos-kandidaten/kandidaten.json", "w"), ensure_ascii=False, indent=1)
