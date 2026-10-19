"""Maakt per complete maaltijd een afbeelding (voor Google-receptresultaten en delen): site/maaltijden-img/<slug>-16x9.png en -1x1.png.
Zonder prijzen, zodat ze niet verouderen. Draai opnieuw na het toevoegen van een maaltijd: python3 scripts/maaltijd_beelden.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from social import lettertype, afbreken, ROOT
from maaltijden import MAALTIJDEN, SOORTEN
GROEN, DONKER, GEEL, INKT, ZACHT = (14, 124, 74), (10, 98, 57), (255, 212, 59), (30, 42, 34), (226, 242, 232)
SOORT = {k: t for k, t, _ in SOORTEN}
OUT = os.path.join(ROOT, "site", "maaltijden-img"); os.makedirs(OUT, exist_ok=True)

def maak(m, w, h, naam):
    im = Image.new("RGB", (w, h), GROEN); d = ImageDraw.Draw(im)
    # bord: twee cirkels rechtsonder als eenvoudig beeldmerk
    r = int(min(w, h) * .42); cx, cy = w - int(r * .55), h - int(r * .45)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DONKER); d.ellipse([cx - r * .72, cy - r * .72, cx + r * .72, cy + r * .72], fill=ZACHT)
    d.ellipse([cx - r * .5, cy - r * .5, cx + r * .5, cy + r * .5], fill=(255, 255, 255))
    m_ = int(w * .07)
    lbl = lettertype("tekst", int(h * .045)); d.text((m_, m_), SOORT.get(m["soort"], "Complete maaltijd").upper(), font=lbl, fill=GEEL)
    groot = lettertype("getal", int(h * (.13 if w > h else .11)))
    regels = afbreken(m["naam"], groot, int(w * .62), d, max_regels=3)
    y = m_ + int(h * .09)
    for rgl in regels: d.text((m_, y), rgl, font=groot, fill=(255, 255, 255)); y += int(groot.size * 1.05)
    klein = lettertype("tekst-r", int(h * .045))
    d.text((m_, y + int(h * .03)), f"Voor 4 personen · {m['tijd']} minuten", font=klein, fill=ZACHT)
    # geel prijskaartje
    tk = lettertype("tekst", int(h * .05)); t = "Goedkoopste supermarkt?"
    tw = d.textlength(t, font=tk); ty = h - m_ - int(h * .1)
    d.rounded_rectangle([m_, ty, m_ + tw + 40, ty + int(h * .1)], radius=10, fill=GEEL)
    d.text((m_ + 20, ty + int(h * .02)), t, font=tk, fill=INKT)
    d.text((m_, ty - int(h * .07)), "goedkopeboodschappen.netlify.app", font=lettertype("tekst-r", int(h * .035)), fill=ZACHT)
    im.save(os.path.join(OUT, naam), optimize=True)

for m in MAALTIJDEN:
    maak(m, 1200, 675, f"{m['slug']}-16x9.png"); maak(m, 1200, 1200, f"{m['slug']}-1x1.png")
print(len(MAALTIJDEN) * 2, "afbeeldingen in", OUT)
