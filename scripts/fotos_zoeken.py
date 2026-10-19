"""Zoekt per maaltijd vrij bruikbare foto's op Wikimedia Commons (CC0, publiek domein, CC BY, CC BY-SA) en slaat kandidaten op in fotos-kandidaten/."""
import json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from maaltijden import MAALTIJDEN
Q = {"boerenkool-met-rookworst": ["boerenkool stamppot", "boerenkool met worst", "kale stamppot"],
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
     "pannenkoeken": ["pannenkoeken", "dutch pancakes stroop", "pannenkoek"]}
UA = {"User-Agent": "GoedkopeBoodschappen/1.0 (https://goedkopeboodschappen.netlify.app; goedkopeboodschappen@proton.me)"}
OK = re.compile(r"^(CC0|Public domain|PD|CC BY(-SA)? [0-9.]+|CC BY(-SA)?)", re.I)
def api(params):
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({**params, "format": "json"})
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30))
os.makedirs("fotos-kandidaten", exist_ok=True)
alle = {}
for m in MAALTIJDEN:
    slug = m["slug"]; gezien = set(); kand = []
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
    kand = kand[:6]
    for i, k in enumerate(kand):
        try:
            data = urllib.request.urlopen(urllib.request.Request(k["thumb"], headers=UA), timeout=60).read()
            k["bestand"] = f"fotos-kandidaten/{slug}-{i}.jpg"; open(k["bestand"], "wb").write(data)
        except Exception as e: print("download fout", k["titel"], e)
        time.sleep(1)
    alle[slug] = kand; print(slug, len(kand))
json.dump(alle, open("fotos-kandidaten/kandidaten.json", "w"), ensure_ascii=False, indent=1)
