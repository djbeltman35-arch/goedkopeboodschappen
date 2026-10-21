"""Maakt van de maaltijdfoto's (kaart en 16x9) een kleinere WebP-versie naast de JPG. Draai na het toevoegen van foto's."""
import glob, os
from PIL import Image
n = 0
for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site", "maaltijden-foto", "*.jpg")):
    if not (f.endswith("-kaart.jpg") or f.endswith("-16x9.jpg")): continue
    w = f[:-4] + ".webp"
    if os.path.exists(w) and os.path.getmtime(w) >= os.path.getmtime(f): continue
    Image.open(f).save(w, "WEBP", quality=78, method=6); n += 1
print(n, "webp-bestanden gemaakt")
