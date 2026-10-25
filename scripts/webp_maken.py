"""Maakt van de maaltijdfoto's (kaart en 16x9) een kleinere WebP-versie naast de JPG, plus een kleine kaartversie
(-kaart-s.webp, 320 breed) voor schermen waar de kaart smal wordt getoond. Draai na het toevoegen van foto's."""
import glob, os
from PIL import Image
n = 0
for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site", "maaltijden-foto", "*.jpg")):
    if not (f.endswith("-kaart.jpg") or f.endswith("-16x9.jpg")): continue
    w = f[:-4] + ".webp"
    if not (os.path.exists(w) and os.path.getmtime(w) >= os.path.getmtime(f)):
        Image.open(f).save(w, "WEBP", quality=78, method=6); n += 1
    if f.endswith("-kaart.jpg"):
        s = f[:-4] + "-s.webp"
        if not (os.path.exists(s) and os.path.getmtime(s) >= os.path.getmtime(f)):
            im = Image.open(f).convert("RGB"); im = im.resize((320, round(320 * im.height / im.width)), Image.LANCZOS)
            im.save(s, "WEBP", quality=74, method=6); n += 1
print(n, "webp-bestanden gemaakt")
